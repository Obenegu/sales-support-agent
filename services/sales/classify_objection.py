# app/services/classify_objection.py
from typing import Dict, Tuple
import re

# Simple rule-based + fallback to keyword scoring.
OBJECTION_KEYWORDS = {
    "price": ["too expensive", "price", "cost", "cheaper", "afford", "expensive", "costly"],
    "trust": ["trust", "scam", "reliable", "trustworthy", "prove", "references", "reviews", "reputation"],
    "time": ["later", "not now", "busy", "tomorrow", "next week", "schedule", "later on"],
    "need": ["don't need", "not interested", "no use", "not for me", "fit", "works for me", "unnecessary"],
    "competitor": ["cheaper at", "competitor", "they offer", "vs", "better price", "other company"],
    "thinking": ["think", "consider", "need to think", "not sure", "let me think", "I'll get back", "decide"],
}

# Helpful small normalization
def _normalize(text: str) -> str:
    return text.lower().strip()

def classify_objection(message: str) -> Dict:
    """
    Return a dict:
      {
        "objection_type": <one of taxonomy>,
        "confidence": float 0..1,
        "reasoning": "Why we picked it"
      }
    Uses simple keyword scoring and a small regex check for strong phrases.
    """

    text = _normalize(message)
    scores = {k: 0 for k in OBJECTION_KEYWORDS.keys()}

    # direct phrase patterns give high weight
    strong_patterns = {
        "price": [r"\btoo expensive\b", r"\bcan't afford\b", r"\bcan't afford\b", r"\bnot affordable\b"],
        "thinking": [r"\b(i will|i'll) (get back|decide)\b", r"\bneed to think\b"],
    }

    # check strong patterns first
    for typ, patterns in strong_patterns.items():
        for p in patterns:
            if re.search(p, text):
                return {
                    "objection_type": typ,
                    "confidence": 0.95,
                    "reasoning": f"Matched strong pattern `{p}`"
                }

    # keyword scoring
    for typ, keywords in OBJECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[typ] += 1

    # Normalize scores to confidence
    best_type = None
    best_score = 0
    for typ, score in scores.items():
        if score > best_score:
            best_score = score
            best_type = typ

    # If nothing matched, return other
    if best_score == 0:
        return {
            "objection_type": "other",
            "confidence": 0.2,
            "reasoning": "No keywords matched; low confidence fallback"
        }

    # Confidence mapping: score -> [0.5 .. 0.95]
    # (cap large scores)
    conf = min(0.95, 0.5 + (best_score / 10))
    return {
        "objection_type": best_type,
        "confidence": round(conf, 2),
        "reasoning": f"Matched {best_score} keyword(s) for type '{best_type}'"
    }
