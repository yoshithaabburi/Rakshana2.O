# ============================================
# RAKSHANA 24/7 — Test Suite
# ============================================

import json
import pytest

from app import create_app, db
from app.models.user import User
from app.utils.encryption import encrypt_field, decrypt_field, hash_phone


@pytest.fixture
def app():
    """Create test app with in-memory database."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner."""
    return app.test_cli_runner()


# ─── Health Check ─────────────────────────────────────────

class TestHealth:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "Rakshana 24/7 API"


# ─── Encryption ──────────────────────────────────────────

class TestEncryption:
    def test_encrypt_decrypt(self):
        original = "+919876543210"
        encrypted = encrypt_field(original)
        assert encrypted != original
        assert decrypt_field(encrypted) == original

    def test_encrypt_empty(self):
        assert encrypt_field("") == ""
        assert decrypt_field("") == ""

    def test_hash_phone(self):
        phone = "+919876543210"
        h1 = hash_phone(phone)
        h2 = hash_phone(phone)
        assert h1 == h2  # Deterministic
        assert len(h1) == 64  # SHA-256 hex
        assert h1 != phone  # Not plaintext

    def test_hash_phone_normalisation(self):
        h1 = hash_phone("+91 98765 43210")
        h2 = hash_phone("+919876543210")
        assert h1 == h2  # Same after normalisation


# ─── Authentication ──────────────────────────────────────

class TestAuth:
    def test_register(self, client):
        response = client.post("/api/auth/register", json={
            "email": "test@rakshana.in",
            "password": "testpass123",
            "display_name": "Test User",
            "phone_number": "+919876543210",
            "language": "en",
        })
        assert response.status_code == 201
        data = response.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "test@rakshana.in"

    def test_register_duplicate(self, client):
        # First registration
        client.post("/api/auth/register", json={
            "email": "test@rakshana.in",
            "password": "testpass123",
        })
        # Duplicate
        response = client.post("/api/auth/register", json={
            "email": "test@rakshana.in",
            "password": "testpass123",
        })
        assert response.status_code == 409

    def test_register_short_password(self, client):
        response = client.post("/api/auth/register", json={
            "email": "test@rakshana.in",
            "password": "short",
        })
        assert response.status_code == 400

    def test_login(self, client):
        # Register first
        client.post("/api/auth/register", json={
            "email": "test@rakshana.in",
            "password": "testpass123",
        })
        # Login
        response = client.post("/api/auth/login", json={
            "email": "test@rakshana.in",
            "password": "testpass123",
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "email": "test@rakshana.in",
            "password": "testpass123",
        })
        response = client.post("/api/auth/login", json={
            "email": "test@rakshana.in",
            "password": "wrongpass",
        })
        assert response.status_code == 401

    def test_get_me(self, client):
        # Register
        reg_response = client.post("/api/auth/register", json={
            "email": "test@rakshana.in",
            "password": "testpass123",
        })
        token = reg_response.get_json()["access_token"]

        # Get profile
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert response.status_code == 200
        assert response.get_json()["user"]["email"] == "test@rakshana.in"

    def test_protected_route_without_token(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401


# ─── Anonymous Reports ───────────────────────────────────

class TestReports:
    def test_submit_report(self, client):
        response = client.post("/api/reports/submit", json={
            "incident_type": "harassment",
            "description": "Receiving threatening messages on WhatsApp from unknown number.",
            "platform": "WhatsApp",
            "language": "en",
        })
        assert response.status_code == 201
        data = response.get_json()
        assert "anonymous_token" in data
        assert len(data["anonymous_token"]) == 64
        assert len(data["applicable_laws"]) > 0

    def test_check_report_status(self, client):
        # Submit report
        submit_response = client.post("/api/reports/submit", json={
            "incident_type": "stalking",
            "description": "Someone is tracking my location using a spyware app.",
        })
        token = submit_response.get_json()["anonymous_token"]

        # Check status
        response = client.get(f"/api/reports/status/{token}")
        assert response.status_code == 200
        assert response.get_json()["report"]["status"] == "submitted"

    def test_submit_report_invalid_type(self, client):
        response = client.post("/api/reports/submit", json={
            "incident_type": "invalid_type",
            "description": "Test description here.",
        })
        assert response.status_code == 400

    def test_report_types(self, client):
        response = client.get("/api/reports/types")
        assert response.status_code == 200
        types = response.get_json()["types"]
        assert len(types) >= 5


# ─── Legal Routes ────────────────────────────────────────

class TestLegal:
    def test_get_laws(self, client):
        response = client.get("/api/legal/laws")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["laws"]) > 0

    def test_search_laws(self, client):
        response = client.get("/api/legal/laws?q=stalking")
        assert response.status_code == 200
        data = response.get_json()
        assert any("stalk" in law["title"].lower() for law in data["laws"])

    def test_get_rights(self, client):
        response = client.get("/api/legal/rights")
        assert response.status_code == 200
        assert len(response.get_json()["rights"]) > 0

    def test_get_helplines(self, client):
        response = client.get("/api/legal/helplines")
        assert response.status_code == 200
        helplines = response.get_json()["helplines"]
        assert any(h["number"] == "1930" for h in helplines)

    def test_laws_for_incident(self, client):
        response = client.get("/api/legal/for-incident/blackmail")
        assert response.status_code == 200
        laws = response.get_json()["applicable_laws"]
        assert len(laws) > 0


# ─── i18n Routes ─────────────────────────────────────────

class TestI18n:
    def test_get_languages(self, client):
        response = client.get("/api/i18n/languages")
        assert response.status_code == 200
        langs = response.get_json()["languages"]
        codes = [l["code"] for l in langs]
        assert "en" in codes
        assert "te" in codes

    def test_get_strings_en(self, client):
        response = client.get("/api/i18n/strings?lang=en")
        assert response.status_code == 200
        data = response.get_json()
        assert data["language"] == "en"
        assert "app_name" in data["strings"]

    def test_get_strings_te(self, client):
        response = client.get("/api/i18n/strings?lang=te")
        assert response.status_code == 200
        data = response.get_json()
        assert data["language"] == "te"
        assert "రక్షణ" in data["strings"]["app_name"]

    def test_fallback_to_english(self, client):
        response = client.get("/api/i18n/strings?lang=xx")
        assert response.status_code == 200
        assert response.get_json()["language"] == "en"


# ─── Threat Scorer ───────────────────────────────────────

class TestThreatScorer:
    def test_safe_content(self):
        from app.services.threat_scorer import score_threat
        result = score_threat("The weather today is sunny and warm in Hyderabad.")
        assert result["score"] < 40
        assert result["threat_type"] == "none"

    def test_doxxing_detection(self):
        from app.services.threat_scorer import score_threat
        result = score_threat(
            "Phone number leaked: +91-98765-43210. Personal info exposed. "
            "Contact details shared without consent."
        )
        assert result["score"] >= 40
        assert result["threat_type"] == "doxxing"
        assert len(result["matched_keywords"]) > 0

    def test_harassment_detection(self):
        from app.services.threat_scorer import score_threat
        result = score_threat(
            "Will teach her a lesson. Going to destroy her reputation. "
            "Harass and threaten until she pays."
        )
        assert result["score"] >= 40
        assert result["threat_type"] in ["harassment", "blackmail"]

    def test_morphed_image_detection(self):
        from app.services.threat_scorer import score_threat
        result = score_threat(
            "Deepfake nude images created using AI generated photoshop. "
            "Morphed photo of victim. Revenge porn uploaded."
        )
        assert result["score"] >= 50
        assert result["threat_type"] == "morphed_image"

    def test_context_amplifiers(self):
        from app.services.threat_scorer import score_threat
        base = score_threat("Phone number leaked without consent")
        amplified = score_threat(
            "Phone number leaked without consent. Make it viral NOW everyone share immediately!"
        )
        assert amplified["score"] >= base["score"]

    def test_context_diminishers(self):
        from app.services.threat_scorer import score_threat
        base = score_threat("Stalking and harassment case details")
        diminished = score_threat(
            "Movie story about stalking and harassment. Fiction novel drama."
        )
        assert diminished["score"] <= base["score"]
