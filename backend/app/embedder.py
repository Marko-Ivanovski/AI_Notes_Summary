# app/embedder.py

import os
import gzip
import logging
import numpy as np
import redis
import torch

from transformers import AutoTokenizer, AutoModel
from typing import List

# Configuration from environment
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", 32))
REDIS_TTL = int(os.getenv("REDIS_TTL", 0))

# Initialize Redis client
redis_client = redis.from_url(REDIS_URL)

# Lazy model/tokenizer holders
_tokenizer = None
_model = None

def _load_model():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL)
        _model = AutoModel.from_pretrained(EMBED_MODEL)
        _model.eval()
    return _tokenizer, _model


def _encode_batch(texts: List[str]) -> np.ndarray:
    """
    Encode a list of texts into embedding vectors.
    Returns a NumPy array of shape (len(texts), dim).
    """

    tokenizer, model = _load_model()
    with torch.no_grad():
        encoded = tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        outputs = model(**encoded)
        hidden = outputs.last_hidden_state
        attn_mask = encoded.attention_mask.unsqueeze(-1)
        masked = hidden * attn_mask
        summed = masked.sum(1)
        counts = attn_mask.sum(1)
        embeddings = summed / counts
        np_emb = embeddings.cpu().numpy().astype(np.float32)
    return np_emb


def _redis_key(chunk_id: str) -> str:
    return f"embed:{chunk_id}"


def get_or_compute_embedding(chunk_id: str, text: str) -> np.ndarray:
    """
    Retrieve embedding from cache or compute + cache it.
    """

    key = _redis_key(chunk_id)
    try:
        cached = redis_client.get(key)
        if cached:
            logging.debug(f"Cache hit for chunk {chunk_id}")
            decompressed = gzip.decompress(cached)
            return np.frombuffer(decompressed, dtype=np.float32)
        logging.debug(f"Cache miss for chunk {chunk_id}")
        emb = _encode_batch([text])[0]
        buf = emb.tobytes()
        compressed = gzip.compress(buf)

        if REDIS_TTL > 0:
            redis_client.setex(key, REDIS_TTL, compressed)
        else:
            redis_client.set(key, compressed)
        return emb
    except Exception as e:
        logging.error(f"Embedding error for chunk {chunk_id}: {e}")
        dim = _model.config.hidden_size if _model else _encode_batch([text]).shape[1]
        return np.zeros(dim, dtype=np.float32)


def encode_texts_for_chunks(chunks: List[dict]) -> None:
    """
    Given a list of chunk dicts with 'chunk_id' and 'text',
    compute embeddings for each and attach under 'embedding'.
    Modifies chunks in place.
    """

    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[i : i + EMBED_BATCH_SIZE]
        ids = [c['chunk_id'] for c in batch]
        texts = [c['text'] for c in batch]
        try:
            batch_embs = _encode_batch(texts)
            for chunk, emb in zip(batch, batch_embs):
                chunk['embedding'] = emb
        except Exception as e:
            logging.error(f"Batch encoding error: {e}")
            for chunk in batch:
                chunk['embedding'] = get_or_compute_embedding(chunk['chunk_id'], chunk['text'])
