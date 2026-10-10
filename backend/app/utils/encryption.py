# ============================================
# RAKSHANA 24/7 — AES-256 Encryption Utility
# ============================================
# PRD: "Phone numbers, photos, and profile data are encrypted at rest
#        using AES-256. A DB breach exposes ciphertext only."

import base64
import hashlib
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _get_fernet_key() -> bytes:
    """Derive a Fernet-compatible key from the ENCRYPTION_KEY env var."""
    raw_key = os.getenv(
        "ENCRYPTION_KEY", "rakshana-aes-256-key-must-be-32-bytes!!"
    ).encode()
    # Use PBKDF2 to derive a proper 32-byte key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"rakshana-salt-v1",  # Fixed salt for deterministic key derivation
        iterations=100_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(raw_key))
    return key


# Singleton Fernet instance
_fernet = Fernet(_get_fernet_key())


def encrypt_field(plaintext: str) -> str:
    """Encrypt a string field using AES-256 (via Fernet).

    Returns a base64-encoded ciphertext string safe for DB storage.
    """
    if not plaintext:
        return ""
    token = _fernet.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted field back to plaintext."""
    if not ciphertext:
        return ""
    try:
        plaintext = _fernet.decrypt(ciphertext.encode("utf-8"))
        return plaintext.decode("utf-8")
    except Exception:
        return "[DECRYPTION_FAILED]"


def hash_phone(phone: str) -> str:
    """SHA-256 hash of phone number for deterministic scanning lookups.

    PRD: "Phone number is hashed (SHA-256) for scanning use."
    The hash is deterministic so the scanner can match without decrypting.
    """
    if not phone:
        return ""
    # Normalise: strip spaces, dashes, ensure starts with country code
    normalised = phone.strip().replace(" ", "").replace("-", "")
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def generate_anonymous_token() -> str:
    """Generate a random token for anonymous report tracking."""
    return hashlib.sha256(os.urandom(32)).hexdigest()
