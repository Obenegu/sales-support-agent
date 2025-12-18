SUPPORT_TEMPLATES = {
    "account_issue": (
        "It seems you’re having trouble with your account. "
        "Please try resetting your password or check your login credentials. "
        "If the problem persists, contact support with your registered email."
    ),
    "payment_issue": (
        "We noticed a problem with your payment. "
        "Please check your card details, ensure sufficient funds, "
        "or try an alternative payment method. Contact support if this continues."
    ),
    "technical_issue": (
        "It looks like you’re experiencing a technical issue. "
        "Try restarting the app or clearing your cache. "
        "If the issue persists, provide the error code and our tech team will assist you."
    ),
    "order_issue": (
        "There seems to be an issue with your order. "
        "Check your order status online. "
        "If you don’t see an update, contact our support team with your order ID."
    ),
    "general_issue": (
        "I’m here to help! Can you provide more details about the problem?"
    )
}

SYMPTOM_KEYWORDS_MAP = {
    "account_issue": ["login problem", "can't log in", "forgot password", "login failed"],
    "payment_issue": ["payment failed", "transaction declined", "card declined"],
    "technical_issue": ["app crashing", "not loading", "feature not working", "error code", "freezing"],
    "order_issue": ["shipping delay", "order not received", "wrong order"],
}

SYMPTOM_DIAGNOSIS_MAP = {
    "login problem": "account_issue",
    "can't log in": "account_issue",
    "forgot password": "account_issue",
    "payment failed": "payment_issue",
    "transaction declined": "payment_issue",
    "app crashing": "technical_issue",
    "feature not working": "technical_issue",
    "error code": "technical_issue",
    "shipping delay": "order_issue",
    "order not received": "order_issue",
}