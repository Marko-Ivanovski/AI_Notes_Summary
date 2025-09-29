# app/routes.py

from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def index():
    """
    Health check endpoint.
    """
    return jsonify({
        'status': 'ok',
        'message': 'AI Notes App backend is running.'
    })
