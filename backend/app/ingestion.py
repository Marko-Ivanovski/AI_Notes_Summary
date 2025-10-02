# app/ingestion.py

import fitz
import logging

from .models import Chunk
from . import db
from .embedder import get_or_compute_embedding


def extract_and_chunk(doc_id: int, file_path: str, chunk_size: int = 500, overlap: int = 50) -> int:
    """
    1) Open the PDF at file_path
    2) Extract text from each page
    3) Split into overlapping chunks of ~chunk_size words
    4) Insert all chunks into the DB, setting chunk_index
    5) Compute and store embeddings for each chunk
    6) Return the number of chunks created
    """

    pdf = fitz.open(file_path)
    chunks = []
    idx = 0

    # Step 1–3: Extract and chunk text
    for page in pdf:
        words = page.get_text().split()
        start = 0
        while start < len(words):
            slice_words = words[start : start + chunk_size]
            text = " ".join(slice_words)

            chunks.append(
                Chunk(
                    document_id=doc_id,
                    page_number=page.number + 1,
                    chunk_index=idx,
                    text=text
                )
            )

            idx += 1
            start += chunk_size - overlap

    created = 0
    if chunks:
        # Step 4: Insert chunks so they get real IDs
        db.session.add_all(chunks)
        db.session.flush()  # assign IDs without committing
        db.session.commit()
        created = len(chunks)

        # Step 5: Compute and store embeddings
        for chunk in chunks:
            try:
                emb = get_or_compute_embedding(str(chunk.id), chunk.text)
                chunk.embedding = emb.tobytes()
            except Exception as e:
                logging.error(f"Failed to embed chunk {chunk.id}: {e}")

        # Commit embedding updates
        db.session.commit()

    return created
