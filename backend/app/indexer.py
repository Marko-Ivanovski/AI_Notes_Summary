# app/indexer.py
import os
import json
import logging
from typing import List, Tuple

import numpy as np
import faiss
from whoosh import index as whoosh_index
from whoosh.fields import Schema, TEXT, ID, NUMERIC
from whoosh.writing import AsyncWriter

from .models import Chunk
from . import db

# Configuration from environment
WHOOSH_INDEX_DIR = os.getenv("WHOOSH_INDEX_DIR", "indexes/whoosh_index")
FAISS_INDEX_DIR  = os.getenv("FAISS_INDEX_DIR",  "indexes/faiss_index")


def _ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


# Whoosh (BM25) Indexing
def _create_whoosh_schema() -> Schema:
    return Schema(
        chunk_id=ID(stored=True, unique=True),
        document_id=NUMERIC(stored=True),
        page_number=NUMERIC(stored=True),
        chunk_index=NUMERIC(stored=True),
        text=TEXT(stored=True)
    )


def build_whoosh_index(chunks: List[Chunk]):
    _ensure_dir(WHOOSH_INDEX_DIR)
    if whoosh_index.exists_in(WHOOSH_INDEX_DIR):
        idx = whoosh_index.open_dir(WHOOSH_INDEX_DIR)
    else:
        schema = _create_whoosh_schema()
        idx = whoosh_index.create_in(WHOOSH_INDEX_DIR, schema)

    writer = AsyncWriter(idx)
    for chunk in chunks:
        writer.update_document(
            chunk_id=str(chunk.id),
            document_id=chunk.document_id,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            text=chunk.text
        )
    writer.commit()
    logging.info(f"Whoosh index updated with {len(chunks)} chunks.")


def rebuild_whoosh_index():
    logging.info("Rebuilding Whoosh index from DB...")
    chunks = db.session.query(Chunk).all()

    if os.path.exists(WHOOSH_INDEX_DIR):
        for fname in os.listdir(WHOOSH_INDEX_DIR):
            path = os.path.join(WHOOSH_INDEX_DIR, fname)
            os.remove(path)
    build_whoosh_index(chunks)


# FAISS (vector) Indexing
def build_faiss_index(chunks: List[Chunk]) -> Tuple[faiss.Index, List[int]]:
    valid = [(chunk.id, chunk.embedding) for chunk in chunks if chunk.embedding]
    if not valid:
        raise ValueError("No embeddings found for FAISS indexing.")

    ids, emb_blobs = zip(*valid)
    embeddings = np.stack([np.frombuffer(blob, dtype=np.float32) for blob in emb_blobs])

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
    embeddings = embeddings / norms

    vector_dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(vector_dim)
    index.add(embeddings)

    logging.info(f"FAISS index built with {len(ids)} vectors (dim={vector_dim}).")
    return index, list(ids)


def persist_faiss_index(index: faiss.Index, id_list: List[int]):
    _ensure_dir(FAISS_INDEX_DIR)
    index_path = os.path.join(FAISS_INDEX_DIR, "faiss.index")
    idmap_path = os.path.join(FAISS_INDEX_DIR, "id_map.json")

    faiss.write_index(index, index_path)

    mapping = {str(i): int(cid) for i, cid in enumerate(id_list)}
    with open(idmap_path, "w") as f:
        json.dump(mapping, f)

    logging.info(f"Persisted FAISS index to {index_path} and id_map (dict) to {idmap_path}.")


def rebuild_faiss_index():
    logging.info("Rebuilding FAISS index from DB...")
    chunks = db.session.query(Chunk).all()
    index, id_map = build_faiss_index(chunks)
    persist_faiss_index(index, id_map)


# Combining Indexes
def build_indexes(reindex_all: bool = False):
    logging.info(f"Starting index build (reindex_all={reindex_all}).")

    if reindex_all:
        rebuild_whoosh_index()
        rebuild_faiss_index()
    else:
        new_chunks = db.session.query(Chunk).filter(Chunk.embedding.isnot(None)).all()
        if new_chunks:
            build_whoosh_index(new_chunks)

            index_path = os.path.join(FAISS_INDEX_DIR, "faiss.index")
            idmap_path = os.path.join(FAISS_INDEX_DIR, "id_map.json")

            if new_chunks:
                ids_new, emb_blobs = zip(*[(c.id, c.embedding) for c in new_chunks])
                embs_new = np.stack([np.frombuffer(b, dtype=np.float32) for b in emb_blobs])
                norms = np.linalg.norm(embs_new, axis=1, keepdims=True) + 1e-12
                embs_new = embs_new / norms

                if os.path.exists(index_path) and os.path.exists(idmap_path):
                    idx = faiss.read_index(index_path)
                    with open(idmap_path, "r") as f:
                        existing_map = json.load(f)

                    start_row = idx.ntotal
                    idx.add(embs_new)

                    for offset, cid in enumerate(ids_new):
                        existing_map[str(start_row + offset)] = int(cid)

                    # Rebuild ordered list for persistence
                    total_rows = idx.ntotal
                    ordered_ids = [existing_map[str(i)] for i in range(total_rows)]
                    persist_faiss_index(idx, ordered_ids)
                else:
                    idx = faiss.IndexFlatIP(embs_new.shape[1])
                    idx.add(embs_new)
                    persist_faiss_index(idx, list(ids_new))
        else:
            logging.info("No new chunks to index.")

    logging.info("Index build complete.")
