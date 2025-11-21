# services/support_engine.py
from services.support_template import SUPPORT_TEMPLATES, SYMPTOM_DIAGNOSIS_MAP, SYMPTOM_KEYWORDS_MAP
from app.safety import sanitize_text
from rapidfuzz import fuzz


def diagnose_support_issue(user_message: str) -> str:
    text = sanitize_text(user_message).lower()

    best_score = 0
    best_category = None

    for category, keywords in SYMPTOM_KEYWORDS_MAP.items():
        for keyword in keywords:
            score = fuzz.partial_ratio(text, keyword)
            if score > best_score and score > 70:  # threshold
                best_score = score
                best_category = category

    if best_category:
        return SUPPORT_TEMPLATES.get(best_category, SUPPORT_TEMPLATES["general_issue"])

    return SUPPORT_TEMPLATES["general_issue"]