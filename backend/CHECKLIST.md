# AI Notes Summary – Backend Implementation Checklist

> One‑page, copy‑paste friendly plan.
> Legend: 🟩 = already implemented, ⬜ = to implement

---

## 0) Foundation & App Wiring

* 🟩 **`backend/run.py`** – Entrypoint that imports `create_app()` and runs Flask.
* 🟩 **`backend/app/__init__.py`** – Creates Flask app, initializes DB/Redis/CORS, registers blueprint `api`.
* 🟩 **`backend/app/models.py`** – SQLAlchemy models: `Document`, `Chunk`.
* 🟩 **Config files** – `.env`, `requirements.txt` (Flask, SQLAlchemy, redis, PyMuPDF, sentence-transformers, faiss, BM25 lib, LLM client, etc.).

**Done criteria:** App boots; `/api/...` routes mount; DB connects.

---

## 1) HTTP Endpoints (Routes)

* 🟩 **`backend/app/routes.py`**

  * `POST /upload` – Orchestrates: save → ingest → embed → index → JSON `{doc_id, chunks}`.
  * `POST /query` – Orchestrates: load indexes → hybrid retrieval → LLM answer → JSON `{answer, citations}`.

**Done criteria:** Both endpoints return structured JSON and minimal errors.

---

## 2) Utils (File & Path Helpers)

* 🟩 **`backend/app/utils.py`**

  * `save_upload(file, doc_name) -> (doc_id, file_path)`

    * Generate `doc_id` (UUID or DB row ID)
    * Save to `/uploads/<doc_id>.pdf`
    * Insert `Document` row; return `(doc_id, path)`

**Done criteria:** Upload persists file + DB metadata reliably.

---

## 3) Ingestion & Chunking

* 🟩 **`backend/app/ingestion.py`**

  * `extract_and_chunk(doc_id, file_path) -> int`

    * Parse PDF (PyMuPDF), extract text with page numbers
    * Split into ~200–500‑token chunks with small overlap
    * Insert `Chunk(doc_id, page, chunk_id, text, token_count)` rows
    * Return `chunk_count`

**Done criteria:** After `/upload`, chunks exist in DB for the document.

---

## 4) Embeddings

* ⬜ **`backend/app/embedder.py`**

  * Model bootstrap (load once; e.g., sentence‑transformers)
  * `encode_all(doc_id) -> int`

    * Read chunks for `doc_id`
    * Batch encode → float32 vectors
    * Cache in Redis by `chunk_id` (and/or persist to disk)
    * Return encoded count

**Done criteria:** Vectors are generated and reusable without recompute.

---

## 5) Indexing (BM25 + FAISS)

* ⬜ **`backend/app/indexer.py`**

  * `build_and_save(doc_id) -> None`

    * Build BM25 over chunk text → save under `data/bm25/<doc_id>/...`
    * Build FAISS over vectors → save `data/faiss/<doc_id>.index`
  * `load(doc_id) -> None/Handles`

    * Load both indexes for retrieval time

**Done criteria:** Index files exist on disk and can be loaded fast.

---

## 6) Retrieval and Re‑rank

* ⬜ **`backend/app/retriever.py`**

  * `search(doc_id, question, k) -> List[Dict]`

    * BM25.search(k) → lexical hits
    * FAISS.search(k) → semantic hits
    * Merge & dedupe by `chunk_id`; normalize and combine scores
    * Cross‑encoder re‑rank top M
    * Return sorted dicts: `{chunk_id, page, text, score}`

**Done criteria:** Given a question, returns top relevant chunks.

---

## 7) Answer Generation (LLM)

* ⬜ **`backend/app/generator.py`**

  * `answer(question, top_context) -> {answer: str, citations: List[str]}`

    * Build prompt: “Use ONLY provided context; cite chunk_id(s)”
    * Call LLM (LangChain/LlamaIndex/OpenAI, etc.)
    * Return concise answer + list of cited `chunk_id`s

**Done criteria:** Returns grounded, citation‑bearing answers.

---

## Minimal Non‑Goals (for now)

* No `/health` endpoint
* No background jobs
* No complex auth or rate limiting

---

## Definition of Done (Backend)

* `/upload` and `/query` run end‑to‑end on a small PDF
* BM25 + FAISS indexes persist and reload
* Answers include citations referencing real chunk_ids
* Errors are simple and consistent (400/404/422/500)
