# app/__init__.py

import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from redis import Redis

db = SQLAlchemy()
redis_client = None

def create_app():
    app = Flask(__name__)
    load_dotenv()

    # CORS
    CORS(
        app,
        resources={r"/*": {"origins": "http://localhost:3000"}},
        supports_credentials=True,
        allow_headers="*",
        methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"]
    )

    # CONFIG
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

    # FILE UPLOAD CONFIG
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/app/uploads')
    allowed = os.getenv('ALLOWED_EXTENSIONS', '')
    app.config['ALLOWED_EXTENSIONS'] = {e.strip().lower() for e in allowed.split(',') if e}
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 104857600))

    # EXTENSIONS
    db.init_app(app)
    Migrate(app, db)

    # REDIS CONFIG
    global redis_client
    redis_client = Redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'), decode_responses=True)

    # MODELS
    from .models import Document, Chunk

    # BLUEPRINTS
    from .routes import api
    app.register_blueprint(api)

    # from .indexer import indexer_bp
    # app.register_blueprint(indexer_bp)

    # from .retriever import retriever_bp
    # app.register_blueprint(retriever_bp)

    # from .generator import generator_bp
    # app.register_blueprint(generator_bp)

    return app
