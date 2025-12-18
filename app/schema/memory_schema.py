memory_schema = [
  # {
  #   "name": "memory_write",
  #   "description": "Store a short piece of information about the user (key, value).",
  #   "parameters": {
  #     "type": "object",
  #     "properties": {
  #       "user_id": {"type": "string"},
  #       "key": {"type": "string"},
  #       "value": {"type": "object"},
  #       "summary": {"type": "string"}
  #     },
  #     "required": ["user_id", "key", "value"]
  #   }
  # },
  # {
  #   "name": "memory_read",
  #   "description": "Read memory for a specific user and key.",
  #   "parameters": {
  #     "type": "object",
  #     "properties": {
  #       "user_id": {"type": "string"},
  #       "key": {"type": "string"}
  #     },
  #     "required": ["user_id", "key"]
  #   }
  # },
  # {
  #   "name": "memory_search",
  #   "description": "Search user's memories for relevant context.",
  #   "parameters": {
  #     "type": "object",
  #     "properties": {
  #       "user_id": {"type": "string"},
  #       "query": {"type": "string"},
  #       "limit": {"type": "number"}
  #     },
  #     "required": ["user_id", "query"]
  #   }
  # }

   {
    "name": "retrieve_memory",
    "description": "Search past conversations and user-specific context. REQUIRED when the user refers to previous interactions, unresolved issues, repeated problems, account status, or assumes shared history. This tool is the source of truth for anything related to the user's past.",
    "parameters": {
      "type": "object",
      "properties": {
        "user_id": {"type": "string"},
        "query": {"type": "string"}
      },
      "required": ["user_id", "query"]
    }
  },
  {
    "name": "search_knowledge_base",
    "description": "Search official company documents (PDFs, policies, FAQs). REQUIRED for answering questions about pricing, refunds, features, rules, procedures, or any factual business information. Do NOT answer these questions without searching this tool.",
    "parameters": {
      "type": "object",
      "properties": {
        "business_id": {"type": "string"},
        "query": {"type": "string"},
      },
      "required": ["business_id", "query"]
    }
  }
  

]
