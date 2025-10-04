import os
import logging
from typing import List, Optional, Tuple
from whoosh import index as whoosh_index
from whoosh.qparser import QueryParser
import faiss
from sentence_transformers import CrossEncoder

# Initialize indexes once
WHOOSH_INDEX_DIR = os.getenv("WHOOSH_INDEX_DIR", "indexes/whoosh_index")
FAISS_INDEX_DIR  = os.getenv("FAISS_INDEX_DIR",  "indexes/faiss_index")

# Load Whoosh index
if whoosh_index.exists_in(WHOOSH_INDEX_DIR):
    ix = whoosh_index.open_dir(WHOOSH_INDEX_DIR)
else:
    logging.error(f"Whoosh index not found in {WHOOSH_INDEX_DIR}")
    ix = None

# Load FAISS index and id map
faiss_index = None
id_map = {}
try:
    idx_file = os.path.join(FAISS_INDEX_DIR, "faiss.index")
    id_map_file = os.path.join(FAISS_INDEX_DIR, "id_map.json")
    faiss_index = faiss.read_index(idx_file)
    import json
    with open(id_map_file, 'r') as f:
        id_map = json.load(f)
except Exception as e:
    logging.error(f"Failed to load FAISS index: {e}")


def retrieve(query: str, top_k_bm25: int = 5, top_k_faiss: int = 5, top_n: int = 5, cross_encoder: Optional[CrossEncoder] = None) -> List[Tuple[int, float]]:
    """
    Hybrid retrieve: BM25 + FAISS, optional CrossEncoder rerank.
    Returns list of (chunk_id, score).
    """

    results = {}

    # BM25 search
    if ix:
        qp = QueryParser("content", schema=ix.schema)
        q = qp.parse(query)
        with ix.searcher() as searcher:
            hits = searcher.search(q, limit=top_k_bm25)
            for hit in hits:
                cid = int(hit['chunk_id'])
                results[cid] = hit.score

    # FAISS search
    if faiss_index is not None:
        from app.embedder import get_query_embedding
        q_emb = get_query_embedding(query)
        D, I = faiss_index.search(q_emb, top_k_faiss)
        for dist, idx in zip(D[0], I[0]):
            if idx < 0: continue
            cid = int(id_map.get(str(idx), -1))
            if cid == -1: continue
            score = 1 / (1 + dist)
            results[cid] = max(results.get(cid, 0), score)

    # Convert to list and sort by score desc
    candidates = list(results.items())

    # Optional cross-encoder rerank
    if cross_encoder and candidates:
        from app.models import Chunk
        pairs = []
        ids = []
        for cid, _ in candidates:
            chunk = Chunk.query.get(cid)
            pairs.append((query, chunk.content))
            ids.append(cid)
        scores = cross_encoder.predict(pairs)
        candidates = list(zip(ids, scores))

    candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
    return candidates[:top_n]
