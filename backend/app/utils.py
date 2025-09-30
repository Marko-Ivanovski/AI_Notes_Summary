# backend/app/utils.py

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
