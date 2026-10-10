# ============================================
# RAKSHANA 24/7 — User Model
# ============================================
# Encrypted fields: phone_number, photo_vector, social_handles
# PRD: AES-256 field-level encryption, SHA-256 phone hash for scanning

import uuid
from datetime import datetime, timezone

from app import db
from app.utils.encryption import encrypt_field, decrypt_field, hash_phone


class User(db.Model):
    """Registered user with encrypted PII."""

    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Encrypted PII (AES-256)
    phone_encrypted = db.Column(db.Text, nullable=True)
    photo_vector_encrypted = db.Column(db.Text, nullable=True)
    social_handles_encrypted = db.Column(db.Text, nullable=True)

    # Hashed phone for scanning lookups (SHA-256, deterministic)
    phone_hash = db.Column(db.String(64), nullable=True, index=True)

    # Profile
    display_name = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(10), default="en")  # en, te, kn, hi

    # Trusted contacts (JSON array of phone numbers, encrypted)
    trusted_contacts_encrypted = db.Column(db.Text, nullable=True)

    # Scan settings
    scan_interval_hours = db.Column(db.Integer, default=4)
    scan_enabled = db.Column(db.Boolean, default=True)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    last_scan_at = db.Column(db.DateTime, nullable=True)
    current_threat_score = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    alerts = db.relationship("Alert", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    scan_results = db.relationship("ScanResult", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    # ── Property helpers for encrypted fields ──
    @property
    def phone_number(self):
        if self.phone_encrypted:
            return decrypt_field(self.phone_encrypted)
        return None

    @phone_number.setter
    def phone_number(self, value):
        if value:
            self.phone_encrypted = encrypt_field(value)
            self.phone_hash = hash_phone(value)
        else:
            self.phone_encrypted = None
            self.phone_hash = None

    @property
    def photo_vector(self):
        if self.photo_vector_encrypted:
            return decrypt_field(self.photo_vector_encrypted)
        return None

    @photo_vector.setter
    def photo_vector(self, value):
        if value:
            self.photo_vector_encrypted = encrypt_field(value)
        else:
            self.photo_vector_encrypted = None

    @property
    def social_handles(self):
        if self.social_handles_encrypted:
            return decrypt_field(self.social_handles_encrypted)
        return None

    @social_handles.setter
    def social_handles(self, value):
        if value:
            self.social_handles_encrypted = encrypt_field(value)
        else:
            self.social_handles_encrypted = None

    @property
    def trusted_contacts(self):
        if self.trusted_contacts_encrypted:
            return decrypt_field(self.trusted_contacts_encrypted)
        return None

    @trusted_contacts.setter
    def trusted_contacts(self, value):
        if value:
            self.trusted_contacts_encrypted = encrypt_field(value)
        else:
            self.trusted_contacts_encrypted = None

    def to_dict(self, include_sensitive=False):
        """Serialise to dict. Sensitive fields only included when explicitly requested."""
        data = {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "language": self.language,
            "scan_interval_hours": self.scan_interval_hours,
            "scan_enabled": self.scan_enabled,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "current_threat_score": self.current_threat_score,
            "last_scan_at": self.last_scan_at.isoformat() if self.last_scan_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            data["phone_number"] = self.phone_number
            data["social_handles"] = self.social_handles
        return data

    def __repr__(self):
        return f"<User {self.id} ({self.email})>"
