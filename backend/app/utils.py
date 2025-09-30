# app/utils.py

import os

from flask import current_app
from werkzeug.utils import secure_filename
from .models import Document
from . import db

def save_upload(file, name):
    """
    Saves `file` under UPLOAD_FOLDER with a Document row.
    Returns (doc_id, full_file_path).
    """

    # 1) record in DB
    doc = Document(filename=name)
    db.session.add(doc)
    db.session.commit()

    # 2) filesystem
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)

    filename = secure_filename(f"{doc.id}.pdf")
    full_path = os.path.join(folder, filename)
    file.save(full_path)

    return doc.id, full_path


def delete_document(doc_id: int):
    """
    Finds the file and DB record by doc_id and deletes both.
    Returns None if successful, raises ValueError if not found.
    """

    doc = Document.query.get(doc_id)
    if not doc:
        raise ValueError(f"Document {doc_id} not found")

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, f"{doc_id}.pdf")
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(doc)
    db.session.commit()