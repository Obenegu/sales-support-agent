sales_schema = [
    {
        "name": "calculate_price",
        "description": "Calculate price for a service/product.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "quantity": {"type": "number"},
            },
            "required": ["product_name"],
        },
    },
    {
        "name": "generate_quote",
        "description": "Generate a customer quotation.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string"},
                "product": {"type": "string"},
                "quantity": {"type": "number"},
            },
            "required": ["customer_name", "product"],
        },
    },
    {
        "name": "suggest_upsells",
        "description": "Suggest upsells based on the selected product.",
        "parameters": {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
            },
            "required": ["product"],
        },
    },
]