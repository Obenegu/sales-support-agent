from typing import Literal

def classify_intent(message) -> Literal["sales", "support", "general"]:
    message_lower = message.lower()

    sales_keywords = [
        "buy", "purchase", "price", "pricing", "cost", "quote", "quotation", "subscribe", "how much"
    ]

    support_keywords = [
        "problem", "issue", "support", "help", "not working", "not", "not loading",
        "error", "complaint", "refund", "troubleshoot", "repair", "where"
    ]

    if any(k in message_lower for k in sales_keywords):
        return "sales"

    if any(k in message_lower for k in support_keywords):
        return "support"

    return "general"
