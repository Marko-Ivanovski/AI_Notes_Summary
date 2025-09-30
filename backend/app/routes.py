# backend/app/routes.py

from flask import Blueprint, request, jsonify
from .utils import save_upload

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

    return jsonify({
        "doc_id": doc_id,
        "message": "Upload successful",
        "path": path
    }), 201

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
