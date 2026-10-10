# ============================================
# RAKSHANA 24/7 — Application Configuration
# ============================================

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is required")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Database connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))
    )
    # The browser API client sends the access/refresh JWTs as Bearer headers.
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = "Strict"
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"
    JWT_ALGORITHM = "HS256"

    # Encryption (AES-256)
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    if not ENCRYPTION_KEY or len(ENCRYPTION_KEY) != 32:
        raise ValueError("ENCRYPTION_KEY must be 32 bytes (set via environment variable)")

    # Redis / Celery
    REDIS_URL = os.getenv("REDIS_URL")
    if not REDIS_URL:
        raise ValueError("REDIS_URL environment variable is required")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    # Telegram
    TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "")
    TELEGRAM_CHANNELS = [
        ch.strip()
        for ch in os.getenv("TELEGRAM_CHANNELS", "").split(",")
        if ch.strip()
    ]

    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
    TWILIO_WHATSAPP_FROM = os.getenv(
        "TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"
    )

    # Scan / Threat Thresholds
    SCAN_INTERVAL_HOURS = int(os.getenv("SCAN_INTERVAL_HOURS", 4))
    THREAT_WATCH_THRESHOLD = int(os.getenv("THREAT_WATCH_THRESHOLD", 40))
    THREAT_ALERT_THRESHOLD = int(os.getenv("THREAT_ALERT_THRESHOLD", 70))
    THREAT_CRITICAL_THRESHOLD = int(os.getenv("THREAT_CRITICAL_THRESHOLD", 90))

    # CORS - restrict to specific origins
    CORS_ORIGINS = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost,http://127.0.0.1,http://localhost:3000",
        ).split(",")
        if o.strip()
    ]

    # Security
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
    RATELIMIT_STORAGE_URL = REDIS_URL


class DevelopmentConfig(BaseConfig):
    """Development configuration — SQLite, debug on."""

    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(BaseConfig):
    """Production configuration — PostgreSQL, debug off."""

    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(BaseConfig):
    """Testing configuration — in-memory SQLite."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Config map
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
