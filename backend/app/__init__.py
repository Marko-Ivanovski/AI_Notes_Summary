# app/__init__.py

import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from redis import Redis

db = SQLAlchemy()
migrate = Migrate()
redis_client = None


def create_app():
    load_dotenv()

    app = Flask(__name__)

    # CONFIG
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # file upload settings
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/app/uploads')
    allowed = os.getenv('ALLOWED_EXTENSIONS', '')
    app.config['ALLOWED_EXTENSIONS'] = {e.strip().lower() for e in allowed.split(',') if e}
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 0))

    # EXTENSIONS
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Redis client for caching
    global redis_client
    redis_client = Redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'), decode_responses=True)

    # BLUEPRINTS
    from .routes import main_bp
    # from .ingestion import ingestion_bp
    # from .indexer import indexer_bp
    # from .retriever import retriever_bp
    # from .generator import generator_bp

    app.register_blueprint(main_bp)
    # app.register_blueprint(ingestion_bp)
    # app.register_blueprint(indexer_bp)
    # app.register_blueprint(retriever_bp)
    # app.register_blueprint(generator_bp)

    return app
