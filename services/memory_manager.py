import os
from config.settings import mem0
from typing import Any, Dict, List, Optional

class Mem0MemoryManager:

    @staticmethod
    def save_memory(user_id: str, namespace: str, messages: List[Dict[str, str]]):
        """
        Save memory to Mem0 under namespace (businessId) + userId
        """
        return mem0.add(
            messages=messages,
            user_id=user_id,
            namespace=namespace
        )

    @staticmethod
    def search_memory(user_id: str, namespace: str, query: str):
        """
        Search memories for this user/business
        """
        return mem0.search(
            query=query,
            user_id=user_id,
            namespace=namespace
        )

    @staticmethod
    def get_all_memories(user_id: str, namespace: str):
        """
        List all memories for this user/business
        """
        return mem0.get_all(
            user_id=user_id,
            namespace=namespace
        )

    @staticmethod
    def delete_memory(memory_id: str):
        """
        Delete a single memory by ID
        """
        return mem0.delete(memory_id)

    @staticmethod
    def wipe_namespace(namespace: str):
        """
        Delete EVERYTHING under a business/tenant
        """
        return mem0.delete_all(namespace=namespace)
