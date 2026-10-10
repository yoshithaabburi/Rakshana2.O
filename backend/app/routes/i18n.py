# ============================================
# RAKSHANA 24/7 — i18n (Internationalisation) Route
# ============================================
# PRD: "JSON locale files, auto-detect browser language.
#        Adding a new language is adding one JSON file, no code change."

import os
import json

from flask import Blueprint, request, jsonify

# Load locale files at import time
LOCALES_DIR = os.path.join(os.path.dirname(__file__), "..", "locales")
LOADED_LOCALES = {}

SUPPORTED_LANGUAGES = ["en", "te"]  # English, Telugu (MVP)


def _load_locales():
    """Load all JSON locale files from the locales directory."""
    global LOADED_LOCALES
    for lang in SUPPORTED_LANGUAGES:
        filepath = os.path.join(LOCALES_DIR, f"{lang}.json")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                LOADED_LOCALES[lang] = json.load(f)


_load_locales()

# Import into legal since we don't have a separate i18n blueprint yet
# This will be registered as part of legal_bp or standalone

from flask import Blueprint

i18n_bp = Blueprint("i18n", __name__)


@i18n_bp.route("/languages", methods=["GET"])
def get_languages():
    """Get list of supported languages."""
    languages = [
        {"code": "en", "name": "English", "native_name": "English", "direction": "ltr"},
        {"code": "te", "name": "Telugu", "native_name": "తెలుగు", "direction": "ltr"},
    ]
    return jsonify({"languages": languages, "default": "en"}), 200


@i18n_bp.route("/strings", methods=["GET"])
def get_strings():
    """
    Get all UI strings for a language.

    Query params:
      - lang: language code (default: en)

    If language not found, falls back to English.
    """
    lang = request.args.get("lang", "en")

    # Auto-detect from Accept-Language header if not specified
    if lang == "auto":
        accept_lang = request.headers.get("Accept-Language", "en")
        # Simple parsing — get first lang code
        lang = accept_lang.split(",")[0].split("-")[0].strip().lower()

    if lang not in LOADED_LOCALES:
        lang = "en"

    return jsonify({
        "language": lang,
        "strings": LOADED_LOCALES.get(lang, LOADED_LOCALES.get("en", {})),
    }), 200


@i18n_bp.route("/strings/<key>", methods=["GET"])
def get_string(key):
    """
    Get a specific string key for a language.

    Supports nested keys with dot notation: "dashboard.safe"
    """
    lang = request.args.get("lang", "en")

    if lang not in LOADED_LOCALES:
        lang = "en"

    strings = LOADED_LOCALES.get(lang, {})

    # Navigate nested keys
    parts = key.split(".")
    value = strings
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = None
            break

    if value is None:
        return jsonify({"error": f"String key '{key}' not found"}), 404

    return jsonify({"key": key, "language": lang, "value": value}), 200
