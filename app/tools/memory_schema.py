memory_schema = [
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
