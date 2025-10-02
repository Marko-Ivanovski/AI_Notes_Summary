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
    """
    Build or update the Whoosh index from a list of Chunk ORM objects.
    """

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
    """
    Load all chunks from the DB and rebuild the Whoosh index from scratch.
    """

    logging.info("Rebuilding Whoosh index from DB...")
    chunks = db.session.query(Chunk).all()

    if os.path.exists(WHOOSH_INDEX_DIR):
        for fname in os.listdir(WHOOSH_INDEX_DIR):
            path = os.path.join(WHOOSH_INDEX_DIR, fname)
            os.remove(path)
    build_whoosh_index(chunks)


# FAISS (vector) Indexing
def build_faiss_index(chunks: List[Chunk]) -> Tuple[faiss.Index, List[int]]:
    """
    Create a FAISS index from chunks with embeddings.
    Returns the index and the list of chunk IDs corresponding to vector positions.
    """

    valid = [(chunk.id, chunk.embedding) for chunk in chunks if chunk.embedding]
    if not valid:
        raise ValueError("No embeddings found for FAISS indexing.")

    ids, emb_blobs = zip(*valid)
    embeddings = np.stack([np.frombuffer(blob, dtype=np.float32) for blob in emb_blobs])
    vector_dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(vector_dim)
    index.add(embeddings)

    logging.info(f"FAISS index built with {len(ids)} vectors (dim={vector_dim}).")
    return index, list(ids)


def persist_faiss_index(index: faiss.Index, id_map: List[int]):
    """
    Persist FAISS index file and ID map to disk.
    """

    _ensure_dir(FAISS_INDEX_DIR)
    index_path = os.path.join(FAISS_INDEX_DIR, "faiss.index")
    idmap_path  = os.path.join(FAISS_INDEX_DIR, "id_map.json")

    faiss.write_index(index, index_path)
    with open(idmap_path, "w") as f:
        json.dump(id_map, f)

    logging.info(f"Persisted FAISS index to {index_path} and id_map to {idmap_path}.")


def rebuild_faiss_index():
    """
    Rebuild the FAISS index from all chunk embeddings in the DB.
    """

    logging.info("Rebuilding FAISS index from DB...")
    chunks = db.session.query(Chunk).all()
    index, id_map = build_faiss_index(chunks)
    persist_faiss_index(index, id_map)


# Combining Indexes
def build_indexes(reindex_all: bool = False):
    """
    Build or update both Whoosh and FAISS indexes.
    If reindex_all=True, rebuild from scratch; otherwise, add only new chunks.
    """

    logging.info(f"Starting index build (reindex_all={reindex_all}).")

    if reindex_all:
        rebuild_whoosh_index()
        rebuild_faiss_index()
    else:
        new_chunks = db.session.query(Chunk).filter(Chunk.embedding.isnot(None)).all()
        if new_chunks:
            build_whoosh_index(new_chunks)
            index, id_map = build_faiss_index(new_chunks)
            existing_index_path = os.path.join(FAISS_INDEX_DIR, "faiss.index")
            if os.path.exists(existing_index_path):
                existing_index = faiss.read_index(existing_index_path)
                # Reorder embeddings to numpy array
                ids, emb_blobs = zip(*[(c.id, c.embedding) for c in new_chunks])
                embeddings = np.stack([np.frombuffer(b, dtype=np.float32) for b in emb_blobs])
                existing_index.add(embeddings)
                persist_faiss_index(existing_index, id_map)
            else:
                persist_faiss_index(index, id_map)
        else:
            logging.info("No new chunks to index.")

    logging.info("Index build complete.")
