# app/routes.py

from flask import Blueprint, request, jsonify, current_app, send_file, send_from_directory
from .utils import save_upload, delete_document
from .ingestion import extract_and_chunk
from .indexer import build_indexes
from .models import Chunk, Document
from .retriever import retrieve
from .generator import generate_answer

import os

api = Blueprint("api", __name__)

def error(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


@api.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".pdf"):
        return error("Missing or invalid PDF file.")

    name = request.form.get("doc_name") or file.filename
    doc_id, path = save_upload(file, name)

    count = extract_and_chunk(doc_id, path)
    build_indexes(reindex_all=False)

    return jsonify({
        "doc_id": doc_id,
        "chunks": count,
        "message": f"Upload successful, {count} chunks created."
    }), 201


@api.route("/chunks/<int:doc_id>", methods=["GET"])
def list_chunks(doc_id):
    from .models import Chunk
    chunks = (
        Chunk.query
             .filter_by(document_id=doc_id)
             .order_by(Chunk.page_number)
             .all()
    )
    return jsonify([
        { "chunk_id": c.id, "page": c.page_number, "preview": c.text[:60] + "…" }
        for c in chunks
    ]), 200


@api.route("/delete/<int:doc_id>", methods=["DELETE"])
def delete_doc(doc_id):
    try:
        delete_document(doc_id)
        return jsonify({ "message": f"Document {doc_id} deleted." }), 200
    except ValueError as e:
        return jsonify({ "error": str(e) }), 404
    except Exception as e:
        current_app.logger.error("Delete failed: %s", e)
        return jsonify({ "error": "Server error during deletion." }), 500


@api.route("/query", methods=["POST"])
def query():
    data = request.get_json(force=True)
    doc_id  = data.get("doc_id")
    question = (data.get("question") or "").strip()
    if not doc_id or not question:
        return error("Both doc_id and question are required.")

    all_chunks = Chunk.query.filter_by(document_id=doc_id).all()
    if not all_chunks:
        return error(f"No document #{doc_id} found.", 404)

    # ce = current_app.cross_encoder
    ce = None

    hits = retrieve(
        question,
        top_k_bm25=5,
        top_k_faiss=5,
        top_n=5,
        cross_encoder=ce
    )
    hit_ids = [cid for cid, _ in hits] if hits else []

    # Pull only chunks for THIS doc, preserving the hit order
    if hit_ids:
        doc_chunks = (
            Chunk.query
                 .filter(Chunk.id.in_(hit_ids), Chunk.document_id == doc_id)
                 .all()
        )
        by_id = {c.id: c for c in doc_chunks}
        top_chunks = [by_id[cid] for cid in hit_ids if cid in by_id]
    else:
        top_chunks = []

    # Fallback: if retrieval produced nothing for this doc, use the first few chunks
    if not top_chunks:
        top_chunks = (
            Chunk.query
                 .filter_by(document_id=doc_id)
                 .order_by(Chunk.page_number.asc(), Chunk.chunk_index.asc())
                 .limit(5)
                 .all()
        )

    answer_text, cited_chunk_ids = generate_answer(question, top_chunks)

    return jsonify({
        "answer":      answer_text,
        "citations":   cited_chunk_ids,
        "used_k":      len(hits or []),
        "context_count": len(top_chunks)
    }), 200


@api.route("/upload/<int:doc_id>", methods=["GET"])
def serve_pdf(doc_id: int):
    doc = Document.query.get(doc_id)
    if not doc:
        return jsonify({"error": f"Document {doc_id} not found."}), 404

    upload_dir = current_app.config.get("UPLOAD_FOLDER")
    if not upload_dir or not os.path.isdir(upload_dir):
        return jsonify({"error": "Upload directory is not configured or missing."}), 500

    # Primary: use the filename we saved at upload time
    candidates = []
    if doc.filename:
        candidates.append(doc.filename)

    # Fallback: try "<doc_id>.pdf"
    candidates.append(f"{doc_id}.pdf")

    for fname in candidates:
        file_path = os.path.join(upload_dir, fname)
        if os.path.isfile(file_path):
            return send_from_directory(
                directory=upload_dir,
                path=fname,
                mimetype="application/pdf",
                as_attachment=False,
                max_age=3600,
            )

    return jsonify({"error": f"File for document {doc_id} not found on disk."}), 404
