import os
from config.settings import mem0
from typing import Any, Dict, List, Optional

class Mem0MemoryManager:

    def __init__(self):
        self.mem0 = mem0  # Provided by config.settings
    
    def mem0_add(self, user_id: str, namespace: str, messages: List[Dict[str, str]], metadata: Optional[Dict[str, str]] = None,):
        if not self.mem0:
            return None
        try:
            return self.mem0.add(user_id=user_id, namespace=namespace, messages=messages, metadata=metadata,)
        except Exception as e:
            print(f"Mem0 add error: {e}")
            # log error if needed
            return None

    def mem0_search(self, user_id: str, query: str, limit: int = 5):
        if not self.mem0:
            return []
        try:
            # Build required filters: Wrap user_id in AND for single-condition structure
            filters = {
                "AND": [  # Top-level logical operator (required for simple filters)
                    {"user_id": user_id} # Direct field match (implicit equality)
                ]
            }
            # Ignore namespace since it's not a supported filter field
            
            # Pass query first (positional), then kwargs
            return self.mem0.search(
                query,  # Positional first
                filters=filters,
                limit=limit  # Maps to top_k
            )
        except Exception as e:
            print(f"Mem0 search error: {e}")
            return []

    def mem0_delete(self, user_id: str):
        if not self.mem0:
            return False
        try:
            self.mem0.delete_users(user_id=user_id)
            return "Memory Deleted"
        except Exception as e:
            print(f"Mem0 delete error: {e}")
            return "Memory Not Deleted"
    
    def mem0_get_user(self, user_id: str) -> List[Dict[str, Any]]:
        if not self.mem0:
            return []
        try:
            filters = {
                "AND": [  # Top-level logical operator (required for simple filters)
                    {"user_id": user_id} # Direct field match (implicit equality)
                ]
            }

            return self.mem0.get_all(user_id=user_id, filters=filters)
        except Exception as e:
            print(f"Mem0 get_user error: {e}")
            return "error getting memories"
    # ----------------------------
    # Convenience: extract conversation memories and add to mem0
    # ----------------------------
    def extract_and_save_memory(self, user_id: str, business_id: str, user_msg: str, agent_msg: str):
        """
        Add conversation snippets to mem0 for semantic memory. Returns mem0 result or None.
        """
        if not self.mem0:
            return None

        messages = [ 
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": agent_msg}
        ]
        return self.mem0_add(user_id=user_id, namespace=str(business_id), messages=messages)

    def get_memory_for_user(self, user_id: str, business_id: str) -> List[Dict[str, Any]]:
        """
        Return mem0 stored memories for user in namespace business_id. Returns list of raw memories.
        """
        if not self.mem0:
            return []
        raw = self.mem0_get_user(user_id=user_id, namespace=str(business_id))
        # normalize
        return [item.get("memory") or item for item in raw]
    