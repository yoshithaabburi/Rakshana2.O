# ============================================
# RAKSHANA 24/7 — Authentication Routes
# ============================================
# JWT with short expiry + refresh token rotation, optional OTP

import bcrypt
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)

from app import db, limiter
from app.models.user import User
from app.utils.encryption import hash_phone

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per hour")  # 5 registrations per hour per IP
def register():
    """
    Register a new user.

    PRD Flow:
    1. User provides phone (optional), selfie, social handles
    2. Phone is hashed (SHA-256) for scanning
    3. All PII encrypted with AES-256
    4. Celery periodic task registered for this user
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body required"}), 400

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        phone = data.get("phone_number", "")
        social_handles = data.get("social_handles", "")
        display_name = data.get("display_name", "")
        language = data.get("language", "en")

        # Validation
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        if len(email) > 255:
            return jsonify({"error": "Email too long"}), 400

        if display_name and len(display_name) > 100:
            return jsonify({"error": "Display name too long"}), 400

        # Check existing user
        existing = User.query.filter_by(email=email).first()
        if existing:
            logger.warning(f"Registration attempt for existing email: {email}")
            return jsonify({"error": "Email already registered"}), 409

        # Create user with encrypted PII
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        user = User(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            language=language,
        )

        # Set encrypted fields via properties
        if phone:
            user.phone_number = phone  # Encrypts + hashes automatically
        if social_handles:
            user.social_handles = social_handles  # AES-256 encrypted

        db.session.add(user)
        db.session.commit()

        logger.info(f"New user registered: {user.id}")

        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        # TODO: Register Celery periodic scan task for this user
        # from app.workers.tasks import register_user_scan
        # register_user_scan.delay(user.id)

        return jsonify({
            "message": "Registration successful. Your digital shield is active.",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }), 201

    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({"error": "Registration failed. Please try again."}), 500


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per hour")  # 10 login attempts per hour per IP
def login():
    """Authenticate user and return JWT tokens."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body required"}), 400

        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()

        if not user or not bcrypt.checkpw(
            password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            return jsonify({"error": "Invalid email or password"}), 401

        if not user.is_active:
            return jsonify({"error": "Account is deactivated"}), 403

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify({
            "message": "Login successful",
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error("Login error: %s", e, exc_info=True)
        return jsonify({"error": "Login failed. Please try again."}), 500


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token (token rotation)."""
    current_user_id = get_jwt_identity()

    # Token rotation — issue new pair
    new_access_token = create_access_token(identity=current_user_id)
    new_refresh_token = create_refresh_token(identity=current_user_id)

    return jsonify({
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get current authenticated user's profile."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": user.to_dict(include_sensitive=True)}), 200


@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    """Change password for authenticated user."""
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"error": "Both current and new password required"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400

    user = User.query.get(current_user_id)

    if not bcrypt.checkpw(
        current_password.encode("utf-8"), user.password_hash.encode("utf-8")
    ):
        return jsonify({"error": "Current password is incorrect"}), 401

    user.password_hash = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200
