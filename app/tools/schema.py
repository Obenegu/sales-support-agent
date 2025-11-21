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
    {
    "name": "memory_write",
    "description": "Store a short piece of information about the user (key, value).",
    "parameters": {
      "type": "object",
      "properties": {
        "user_id": {"type": "string"},
        "key": {"type": "string"},
        "value": {"type": "object"},
        "summary": {"type": "string"}
      },
      "required": ["user_id", "key", "value"]
    }
  },
  {
    "name": "memory_read",
    "description": "Read memory for a specific user and key.",
    "parameters": {
      "type": "object",
      "properties": {
        "user_id": {"type": "string"},
        "key": {"type": "string"}
      },
      "required": ["user_id", "key"]
    }
  },
  {
    "name": "memory_search",
    "description": "Search user's memories for relevant context.",
    "parameters": {
      "type": "object",
      "properties": {
        "user_id": {"type": "string"},
        "query": {"type": "string"},
        "limit": {"type": "number"}
      },
      "required": ["user_id", "query"]
    }
  }
]