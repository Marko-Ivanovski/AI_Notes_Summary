# app/routes.py

from flask import Blueprint, request, jsonify
from .utils import save_upload, delete_document
from .ingestion import extract_and_chunk
from .indexer import build_indexes

api = Blueprint("api", __name__)

def error(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


@api.route("/upload", methods=["POST"])
def upload():
    """
    1) Receive a PDF file + optional doc_name
    2) Save file & create Document row
    3) Return the new doc_id
    """

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
    """
    1) Return all chunks for a given doc_id
    2) Order by page
    3) Return chunk_id, page, and preview of text
    """

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
    """
    1) Find the document by doc_id
    2) Delete the file
    3) Delete the DB record (chunks will be cascaded‐deleted)
    """

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
    """
    Placeholder endpoint until retrieval/generation is wired.
    """

    data = request.get_json(force=True)
    if not data.get("doc_id") or not data.get("question"):
        return error("Both doc_id and question are required.")

    return jsonify({
        "answer": "Under construction",
        "citations": [],
        "used_k": 0,
        "context_count": 0
    }), 200
