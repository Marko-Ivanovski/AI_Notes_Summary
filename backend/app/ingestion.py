# app/ingestion.py

import fitz
from .models import Chunk
from . import db

def extract_and_chunk(doc_id: int, file_path: str, chunk_size: int = 500, overlap: int = 50) -> int:
    """
    1) Open the PDF at file_path
    2) Extract text from each page
    3) Split into overlapping chunks of ~chunk_size words
    4) Insert all chunks into the DB, setting chunk_index
    5) Return the number of chunks created
    """

    pdf = fitz.open(file_path)
    chunks = []
    idx = 0

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

    if chunks:
        db.session.bulk_save_objects(chunks)
        db.session.commit()

    return len(chunks)
