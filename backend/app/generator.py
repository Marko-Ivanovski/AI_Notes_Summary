# app/generator.py

import os
import re
import logging
import torch

from typing import List, Tuple
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Configuration from environment
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "sshleifer/distilbart-cnn-6-6")
USE_GENERATOR = os.getenv("USE_GENERATOR", "1") not in ("0", "false", "False")
TORCH_THREADS = int(os.getenv("TORCH_NUM_THREADS", "1"))

MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", "4"))
MAX_CHARS_PER_CHUNK = int(os.getenv("MAX_CHARS_PER_CHUNK", "350"))

MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "128"))
NUM_BEAMS = int(os.getenv("NUM_BEAMS", "2"))

_tokenizer = None
_model = None


def _load_model():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(GENERATION_MODEL)
        _model = AutoModelForSeq2SeqLM.from_pretrained(GENERATION_MODEL)
        _model.eval()
        try:
            torch.set_num_threads(TORCH_THREADS)
        except Exception:
            pass
    return _tokenizer, _model


def _sentence_split(text: str) -> List[str]:
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def _extractive_fallback(question: str, chunks: List) -> str:
    q_tokens = set(re.findall(r"\w+", (question or "").lower()))
    scored = []
    for c in chunks[:MAX_CHUNKS]:
        for sent in _sentence_split((c.text or "")[:1000]):
            s_tokens = set(re.findall(r"\w+", sent.lower()))
            overlap = len(q_tokens & s_tokens)
            if overlap > 0:
                scored.append((overlap, sent))
    if not scored:
        if chunks:
            sents = _sentence_split((chunks[0].text or "")[:800])
            return " ".join(sents[:3]) or "I couldn't find that in the uploaded document."
        return "I couldn't find that in the uploaded document."
    scored.sort(key=lambda x: x[0], reverse=True)
    best = [s for _, s in scored[:5]]
    return " ".join(best)


def _build_prompt(question: str, chunks: List) -> str:
    ctx_lines = []
    for c in chunks[:MAX_CHUNKS]:
        snippet = (c.text or "").strip()
        if len(snippet) > MAX_CHARS_PER_CHUNK:
            snippet = snippet[:MAX_CHARS_PER_CHUNK] + "…"
        ctx_lines.append(f"(page {c.page_number}) {snippet}")
    context = "\n".join(ctx_lines) if ctx_lines else "(no context)"
    return (
        "Summarize the following document context to answer the question. "
        "If the answer is not present, say: I couldn't find that in the uploaded document.\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        "Summary:"
    )


@torch.inference_mode()
def generate_answer(question: str, chunks: List) -> Tuple[str, List[int]]:
    if not chunks:
        return "I couldn't find that in the uploaded document.", []

    if not USE_GENERATOR:
        ans = _extractive_fallback(question, chunks)
        return ans, [int(c.id) for c in chunks[:MAX_CHUNKS]]

    try:
        tokenizer, model = _load_model()
        prompt = _build_prompt(question, chunks)

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        )

        output_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            num_beams=NUM_BEAMS,
            early_stopping=True,
            no_repeat_ngram_size=3,
            do_sample=False,
            length_penalty=2.0,
        )

        answer = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
        if answer.lower().startswith("summary:"):
            answer = answer[8:].strip()

        sentences = _sentence_split(answer)
        if sentences:
            answer = " ".join(sentences).strip()

    except Exception as e:
        logging.exception(f"DistilBART generation failed, using extractive fallback: {e}")
        answer = _extractive_fallback(question, chunks)

    cited = [int(c.id) for c in chunks[:MAX_CHUNKS]]
    return answer, cited
