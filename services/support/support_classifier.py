def classify_support_issue(message: str):
    text = message.lower()

    keywords = {
        "login": ["can't log in", "cant login", "login fails", "password not working"],
        "payment": ["payment failed", "card declined", "can't pay", "billing issue"],
        "performance": ["slow", "lag", "not loading", "freezing"],
        "delivery": ["didn't receive", "missing file", "where is my file"],
        "configuration": ["how to setup", "configure", "settings", "integration issue"],
    }

    for category, kw_list in keywords.items():
        for kw in kw_list:
            if kw in text:
                return {
                    "is_issue": True,
                    "category": category,
                    "confidence": 0.9
                }

    return {
        "is_issue": False,
        "category": "none",
        "confidence": 0.3
    }
