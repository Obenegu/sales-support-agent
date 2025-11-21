import re
import logging
from typing import Tuple

logger = logging.getLogger("orchestrator.safety")

# Simple denylist (add entries as you discover abuse vectors)
DENYLIST = ["bomb", "kill", "attack", "terrorist", "explosive", "ssn", "password"]

# PII regex examples - tune them to your region
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"\+?\d[\d\s\-]{6,}\d")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")  # US SSN format (example)

MAX_INPUT_LENGTH = 2000  # characters - enforce a cap

def contains_denylist(text: str) -> Tuple[bool, str]:
    lowered = text.lower()
    for word in DENYLIST:
        if word in lowered:
            return True, word
    return False, ""

def detect_pii(text: str) -> dict:
    return {
        "emails": EMAIL_RE.findall(text),
        "phones": PHONE_RE.findall(text),
        "ssn": SSN_RE.findall(text),
    }

def sanitize_text(text: str) -> str:
    """Minimal sanitization: trim, collapse whitespace."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text

def validate_input(text: str) -> Tuple[bool, dict]:
    """
    Returns (ok, meta). If ok==False -> orchestrator should refuse.
    meta contains reasons and any detected pii.
    """
    if not text or not text.strip():
        return False, {"reason": "empty"}

    if len(text) > MAX_INPUT_LENGTH:
        return False, {"reason": "too_long", "length": len(text)}

    deny, word = contains_denylist(text)
    if deny:
        return False, {"reason": "denylist", "word": word}

    pii = detect_pii(text)
    if any(pii.values()):
        return False, {"reason": "pii_detected", "pii": pii}

    return True, {"reason": "ok"}
