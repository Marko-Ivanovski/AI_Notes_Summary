# app/routes.py

from flask import Blueprint, request, jsonify

from . import ingestion
from . import embedder
from . import indexer
from . import retriever
from . import generator
from . import utils

api = Blueprint("api", __name__)

@api.route("/upload", methods=["POST"])
def upload():
    """
    POST /upload
    Purpose: accept a PDF, create a doc, chunk it, embed, and index it.
    Input: multipart/form-data with 'file' (PDF) and optional 'doc_name'
    Output: { doc_id, chunks, message }
    """

    file = request.files.get("file")
    if not file or file.filename.strip() == "":
        return jsonify({"error": {"type": "ValidationError", "message": "Missing PDF file."}}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": {"type": "ValidationError", "message": "Only .pdf files are accepted."}}), 400

    doc_name = request.form.get("doc_name") or file.filename

    try:
        # 1) Save the raw file and create a Document record
        # Implement utils.save_upload to:
        # - create a new doc_id
        # - save to /uploads/<doc_id>.pdf
        # - persist a Document row
        doc_id, file_path = utils.save_upload(file, doc_name)

        # 2) Extract text and create Chunk rows
        # Implement ingestion.extract_and_chunk(doc_id, file_path) -> returns number of chunks
        chunk_count = ingestion.extract_and_chunk(doc_id, file_path)

        # 3) Create embeddings (cached) for all chunks in this doc
        # Implement embedder.encode_all(doc_id) -> returns number of vectors encoded
        _ = embedder.encode_all(doc_id)

        # 4) Build and persist BM25 + FAISS indexes for this doc
        # Implement indexer.build_and_save(doc_id)
        indexer.build_and_save(doc_id)

        return jsonify({
            "doc_id": doc_id,
            "chunks": int(chunk_count),
            "message": "Document ingested and indexed."
        }), 201

    except FileNotFoundError:
        return jsonify({"error": {"type": "FileError", "message": "Could not read uploaded file."}}), 422
    except ValueError as e:
        return jsonify({"error": {"type": "IngestionError", "message": str(e)}}), 422
    except Exception:
        return jsonify({"error": {"type": "ServerError", "message": "Unexpected error."}}), 500


@api.route("/query", methods=["POST"])
def query():
    """
    POST /query
    Purpose: answer a question about a specific document using hybrid retrieval + LLM.
    Input: { doc_id, question, k?, max_context? }
    Output: { answer, citations: [{chunk_id, page, score}, ...], used_k, context_count }
    """
    data = request.get_json(silent=True) or {}

    doc_id = data.get("doc_id")
    question = (data.get("question") or "").strip()
    k = int(data.get("k", 8))
    max_context = int(data.get("max_context", 4))

    if not doc_id:
        return jsonify({"error": {"type": "ValidationError", "message": "Missing doc_id."}}), 400
    if not question:
        return jsonify({"error": {"type": "ValidationError", "message": "Missing question."}}), 400
    k = max(1, min(k, 20))
    max_context = max(1, min(max_context, 10))

    try:
        # 1) Load BM25 + FAISS indexes for this document
        # Implement indexer.load(doc_id) -> returns handles/objects you need internally
        indexer.load(doc_id)

        # 2) Run hybrid retrieval
        # Implement retriever.search(doc_id, question, k) -> returns ranked list of chunk dicts
        # Each item should at least have: {"chunk_id": str, "page": int, "text": str, "score": float}
        candidates = retriever.search(doc_id, question, k)

        if not candidates:
            return jsonify({"answer": "I couldn’t find relevant context in this document.", "citations": []}), 200

        # 3) Keep only the top N chunks for the LLM context window
        top_context = candidates[:max_context]

        # 4) Generate the final answer with citations
        # Implement generator.answer(question, top_context) -> { "answer": str, "citations": [chunk_id, ...] }
        result = generator.answer(question, top_context)

        # Shape the response
        resp = {
            "answer": result.get("answer", "").strip(),
            "citations": [
                {"chunk_id": c["chunk_id"], "page": c.get("page"), "score": float(c.get("score", 0.0))}
                for c in top_context
            ],
            "used_k": k,
            "context_count": len(top_context),
        }
        return jsonify(resp), 200

    except FileNotFoundError:
        return jsonify({"error": {"type": "NotFound", "message": "Indexes for this document were not found."}}), 404
    except ValueError as e:
        return jsonify({"error": {"type": "QueryError", "message": str(e)}}), 422
    except Exception:
        return jsonify({"error": {"type": "ServerError", "message": "Unexpected error."}}), 500
