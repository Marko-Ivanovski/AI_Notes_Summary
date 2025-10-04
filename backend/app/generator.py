import os
from typing import List, Tuple
from transformers import pipeline
import re

from app.models import Chunk

MODEL = os.getenv("GENERATION_MODEL", "google/flan-t5-large")

# Initialize once
generator = pipeline("text2text-generation", model=MODEL, device=0)

def generate_answer(
    query: str,
    chunks: List[Chunk]
) -> Tuple[str, List[int]]:
    # 1) Build the prompt
    prompt = "Use ONLY the context below (with [chunk_id] tags):\n\n"
    for c in chunks:
        prompt += f"[{c.chunk_id}] {c.content}\n\n"
    prompt += f"Question: {query}\nAnswer (cite chunk_id in [ ]):"

    # 2) Run generation
    out = generator(prompt, max_length=512, do_sample=False)[0]["generated_text"].strip()

    # 3) Extract cited chunk_ids
    cited_ids = [int(m) for m in re.findall(r"\[(\d+)\]", out)]
    return out, cited_ids
