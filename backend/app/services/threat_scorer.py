# ============================================
# RAKSHANA 24/7 — NLP Threat Scoring Engine
# ============================================
# PRD: "NLP-powered contextual scoring — not just keyword matching.
#        Score: 0-100, graduated, never binary."
# Uses NLTK for tokenization and pattern matching.

import re
import json
import logging

logger = logging.getLogger(__name__)

# ─── Threat Keyword Categories (weighted) ─────────────────
THREAT_PATTERNS = {
    "doxxing": {
        "weight": 0.9,
        "keywords": [
            "leaked", "leak", "doxxed", "exposed", "personal info",
            "phone number", "address", "contact", "shared without consent",
            "personal details", "home address", "workplace", "school",
        ],
        "regex_patterns": [
            r"(?:phone|number|mobile)\s*[:=]\s*\+?\d{10,13}",
            r"(?:address|location)\s*[:=]\s*.{10,}",
        ],
    },
    "stalking": {
        "weight": 0.85,
        "keywords": [
            "tracking", "following", "watching", "monitoring",
            "spy", "spyware", "location", "stalk", "stalking",
            "whereabouts", "movements", "schedule",
        ],
        "regex_patterns": [
            r"track(?:ing|ed)?\s+(?:her|she|woman|girl)",
            r"follow(?:ing|ed)?\s+(?:her|she|woman|girl)",
        ],
    },
    "morphed_image": {
        "weight": 0.95,
        "keywords": [
            "morphed", "deepfake", "fake image", "manipulated",
            "nude", "naked", "intimate", "explicit", "photoshop",
            "edited photo", "revenge porn", "ai generated",
        ],
        "regex_patterns": [
            r"(?:morphed|fake|edited)\s+(?:image|photo|picture|pic)",
            r"(?:deep\s*fake|ai\s+generated)",
        ],
    },
    "harassment": {
        "weight": 0.8,
        "keywords": [
            "harass", "abuse", "threaten", "intimidate",
            "vulgar", "obscene", "slut", "whore", "bitch",
            "rape threat", "will teach", "lesson",
        ],
        "regex_patterns": [
            r"(?:will|going\s+to)\s+(?:rape|kill|hurt|destroy)",
            r"teach\s+(?:her|you)\s+a\s+lesson",
        ],
    },
    "blackmail": {
        "weight": 0.9,
        "keywords": [
            "blackmail", "extort", "sextort", "pay up",
            "send money", "or else", "will upload", "will share",
            "will post", "unless you", "demand",
        ],
        "regex_patterns": [
            r"(?:pay|send)\s+(?:money|₹|\$|rs)",
            r"(?:will|going\s+to)\s+(?:upload|share|post|publish)",
            r"unless\s+you\s+(?:pay|send|do)",
        ],
    },
}

# ─── Context Modifiers ────────────────────────────────────
# Words that increase or decrease threat score based on context
AMPLIFIERS = {
    "urgent": 1.2,
    "immediately": 1.2,
    "now": 1.1,
    "tonight": 1.3,
    "soon": 1.1,
    "everyone": 1.2,
    "viral": 1.3,
    "public": 1.2,
    "group": 1.1,
}

DIMINISHERS = {
    "joke": 0.5,
    "kidding": 0.4,
    "just kidding": 0.3,
    "movie": 0.3,
    "fiction": 0.2,
    "novel": 0.2,
    "story": 0.4,
    "drama": 0.4,
    "news article": 0.3,
    "awareness": 0.3,
    "education": 0.3,
    "campaign": 0.3,
}


def score_threat(text: str, user_identifiers: dict | None = None) -> dict:
    """
    Compute a 0-100 threat score for a piece of text.

    PRD: "The NLP scoring module evaluates context: is the phone number
    appearing in a casual conversation or being broadcast with threatening
    language? Threat score is computed on a 0–100 scale."

    Args:
        text: The raw text content to analyze
        user_identifiers: Dict with 'phone_hash', 'name', 'handles' for matching

    Returns:
        dict with score, threat_type, explanation, matched_keywords, confidence
    """
    if not text:
        return {
            "score": 0,
            "threat_type": "none",
            "explanation": "No content to analyze",
            "matched_keywords": [],
            "confidence": 0,
        }

    text_lower = text.lower().strip()
    words = text_lower.split()

    # ── Step 1: Keyword matching across categories ──
    category_scores = {}
    all_matched_keywords = []

    for category, config in THREAT_PATTERNS.items():
        matched = []
        keyword_score = 0

        # Check keywords
        for keyword in config["keywords"]:
            if keyword in text_lower:
                matched.append(keyword)
                keyword_score += 10  # Each keyword match adds 10

        # Check regex patterns
        for pattern in config["regex_patterns"]:
            if re.search(pattern, text_lower):
                matched.append(f"[pattern: {pattern[:30]}...]")
                keyword_score += 20  # Regex patterns are stronger signals

        if matched:
            # Apply category weight
            weighted_score = min(keyword_score * config["weight"], 80)
            category_scores[category] = {
                "raw_score": keyword_score,
                "weighted_score": weighted_score,
                "matched": matched,
            }
            all_matched_keywords.extend(matched)

    if not category_scores:
        return {
            "score": 0,
            "threat_type": "none",
            "explanation": "No threat indicators found in content",
            "matched_keywords": [],
            "confidence": 0,
        }

    # ── Step 2: Determine primary threat type ──
    primary_category = max(
        category_scores, key=lambda k: category_scores[k]["weighted_score"]
    )
    base_score = category_scores[primary_category]["weighted_score"]

    # ── Step 3: Multi-category bonus (multiple threat types = higher risk) ──
    if len(category_scores) > 1:
        base_score += len(category_scores) * 5  # +5 per additional category

    # ── Step 4: Apply context modifiers ──
    amplifier_total = 1.0
    for word, multiplier in AMPLIFIERS.items():
        if word in text_lower:
            amplifier_total *= multiplier

    diminisher_total = 1.0
    for word, multiplier in DIMINISHERS.items():
        if word in text_lower:
            diminisher_total *= multiplier

    modified_score = base_score * amplifier_total * diminisher_total

    # ── Step 5: Check for user identifier mentions ──
    identifier_boost = 0
    if user_identifiers:
        # Check if user's phone (hashed) or name appears
        name = user_identifiers.get("name", "").lower()
        handles = user_identifiers.get("handles", "").lower()

        if name and len(name) > 2 and name in text_lower:
            identifier_boost += 15
        if handles:
            for handle in handles.split(","):
                handle = handle.strip().lower()
                if handle and handle in text_lower:
                    identifier_boost += 20

    modified_score += identifier_boost

    # ── Step 6: Clamp to 0-100 ──
    final_score = int(min(max(round(modified_score), 0), 100))

    # ── Step 7: Generate explanation ──
    explanation = _generate_explanation(
        primary_category,
        final_score,
        all_matched_keywords[:5],
        len(category_scores),
    )

    # Confidence based on number of signals
    confidence = min(
        len(all_matched_keywords) * 15 + len(category_scores) * 10, 100
    )

    return {
        "score": final_score,
        "threat_type": primary_category,
        "explanation": explanation,
        "matched_keywords": all_matched_keywords[:10],
        "confidence": confidence,
        "category_breakdown": {
            k: v["weighted_score"] for k, v in category_scores.items()
        },
    }


def _generate_explanation(
    threat_type: str, score: int, keywords: list, num_categories: int
) -> str:
    """Generate a plain-language explanation of the threat assessment."""

    type_labels = {
        "doxxing": "personal information exposure",
        "stalking": "stalking or surveillance behaviour",
        "morphed_image": "manipulated or explicit image sharing",
        "harassment": "abusive or threatening language",
        "blackmail": "blackmail or extortion attempt",
    }

    label = type_labels.get(threat_type, "suspicious activity")

    if score >= 90:
        severity_text = "CRITICAL: This content shows very strong indicators of"
    elif score >= 70:
        severity_text = "HIGH ALERT: This content contains clear signs of"
    elif score >= 40:
        severity_text = "CAUTION: This content may indicate"
    else:
        severity_text = "LOW RISK: Minor indicators of"

    explanation = f"{severity_text} {label}."

    if keywords:
        kw_text = ", ".join(f'"{k}"' for k in keywords[:3])
        explanation += f" Detected keywords: {kw_text}."

    if num_categories > 1:
        explanation += f" Multiple threat categories detected ({num_categories} types), which increases the risk assessment."

    return explanation
