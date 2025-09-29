# app/models.py

from . import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now)
    chunks = db.relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document id={self.id} filename={self.filename}>"


class Chunk(db.Model):
    __tablename__ = "chunks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    document = db.relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<Chunk id={self.id} doc={self.document_id} page={self.page_number} idx={self.chunk_index}>"
