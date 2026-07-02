# app/tools/support_schema.py
support_schema = [
    {
        "name": "check_order_status",
        "description": "Check the status of an order by order_id and user_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "user_id": {"type": "string"}
            },
            "required": ["order_id", "user_id"]
        }
    },
    {
        "name": "check_payment_status",
        "description": "Check payment status for a given order_id and user_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "user_id": {"type": "string"}
            },
            "required": ["order_id", "user_id"]
        }
    },
    {
        "name": "restart_user_session",
        "description": "Try to restart or refresh a user's session by user_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "check_subscription",
        "description": "Return subscription status for a user.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"}
            },
            "required": ["user_id"]
        }
    }
]
