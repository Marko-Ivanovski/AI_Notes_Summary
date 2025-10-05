# app/retriever.py

import os
import logging
import faiss

from typing import List, Optional, Tuple, Dict
from whoosh import index as whoosh_index
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh import scoring
from sentence_transformers import CrossEncoder
from app.embedder import get_query_embedding

# Configuration from environment
WHOOSH_INDEX_DIR = os.getenv("WHOOSH_INDEX_DIR", "indexes/whoosh_index")
FAISS_INDEX_DIR  = os.getenv("FAISS_INDEX_DIR",  "indexes/faiss_index")

if whoosh_index.exists_in(WHOOSH_INDEX_DIR):
    try:
        ix = whoosh_index.open_dir(WHOOSH_INDEX_DIR)
        logging.info(f"Loaded Whoosh index from {WHOOSH_INDEX_DIR}")
    except Exception as e:
        logging.exception(f"Failed to open Whoosh index at {WHOOSH_INDEX_DIR}: {e}")
        ix = None
else:
    logging.warning(f"Whoosh index not found in {WHOOSH_INDEX_DIR}")
    ix = None

faiss_index = None
id_map: Dict[str, int] = {}
try:
    idx_file = os.path.join(FAISS_INDEX_DIR, "faiss.index")
    id_map_file = os.path.join(FAISS_INDEX_DIR, "id_map.json")
    if os.path.exists(idx_file):
        faiss_index = faiss.read_index(idx_file)
        logging.info(f"Loaded FAISS index from {idx_file}")
    else:
        logging.warning(f"FAISS index file not found at {idx_file}")
    if os.path.exists(id_map_file):
        import json
        with open(id_map_file, "r", encoding="utf-8") as f:
            id_map = json.load(f)
        logging.info(f"Loaded FAISS id_map from {id_map_file}")
    else:
        logging.warning(f"id_map.json not found at {id_map_file}")
except Exception as e:
    logging.exception(f"Failed to load FAISS index/id_map: {e}")
    faiss_index = None
    id_map = {}

def retrieve(
    query: str,
    top_k_bm25: int = 5,
    top_k_faiss: int = 5,
    top_n: int = 5,
    cross_encoder: Optional[CrossEncoder] = None
) -> List[Tuple[int, float]]:
    results: Dict[int, float] = {}

    if ix:
        try:
            raw_q = (query or "").strip()
            if raw_q:
                parser = MultifieldParser(["text"], schema=ix.schema, group=OrGroup.factory(0.9))
                q = parser.parse(raw_q)
                if str(q).strip() not in ("", "()", "[]"):
                    with ix.searcher(weighting=scoring.BM25F()) as searcher:
                        hits = searcher.search(q, limit=top_k_bm25)
                        for hit in hits:
                            cid_val = hit.get("chunk_id") or hit.get("id") or hit.get("pk")
                            try:
                                cid = int(cid_val)
                            except Exception:
                                continue
                            score = float(hit.score)
                            results[cid] = max(results.get(cid, 0.0), score)
            else:
                logging.info("Empty query; skipping BM25.")
        except Exception as e:
            logging.exception(f"Whoosh BM25 search failed: {e}")

    if faiss_index is not None:
        try:
            from app.embedder import get_query_embedding
            q_emb = get_query_embedding(query)
            D, I = faiss_index.search(q_emb, top_k_faiss)
            for dist, idx in zip(D[0], I[0]):
                if idx < 0:
                    continue
                cid = int(id_map.get(str(idx), -1))
                if cid == -1:
                    continue
                score = 1.0 / (1.0 + float(dist))
                results[cid] = max(results.get(cid, 0.0), score)
        except Exception as e:
            logging.exception(f"FAISS search failed: {e}")

    candidates: List[Tuple[int, float]] = list(results.items())

    if cross_encoder and candidates:
        try:
            from app.models import Chunk
            pairs: List[Tuple[str, str]] = []
            ids: List[int] = []
            for cid, _ in candidates:
                chunk = Chunk.query.get(cid)
                if not chunk:
                    continue
                chunk_text: str = getattr(chunk, "text", None) or getattr(chunk, "content", None) or ""
                if not chunk_text:
                    continue
                pairs.append((query, chunk_text))
                ids.append(cid)
            if pairs:
                scores = cross_encoder.predict(pairs)
                candidates = list(zip(ids, [float(s) for s in scores]))
        except Exception as e:
            logging.exception(f"CrossEncoder re-rank failed: {e}")

    candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
    return candidates[:top_n]
