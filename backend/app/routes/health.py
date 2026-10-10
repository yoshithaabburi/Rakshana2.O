# ============================================
# RAKSHANA 24/7 — Health Check Route
# ============================================

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """System health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Rakshana 24/7 API",
        "version": "1.0.0",
    }), 200
