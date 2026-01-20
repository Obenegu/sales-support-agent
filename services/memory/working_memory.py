import json
import time
from typing import Any, Dict, List, Optional
from pytz import timezone
import redis
from sqlalchemy import JSON
from datetime import datetime, timezone
from models.cart_item import CartItem  


r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def now():
    return datetime.now(timezone.utc).isoformat()

class WorkingMemory:
    def __init__(self):
        self.memory = None

    def createWorkingMemory(self, user_id, session_id):
        self.memory = {
            "session_id": session_id,
            "user_id": user_id,
            "mode": "idle",
            "current_intent": None,
            "cart": [],
            "checkout": { "status": "none", "checkout_link": None },
            "flags": { "awaiting_confirmation": False },
            "timestamps": {
                "created_at": now(),
                "updated_at": now()
            }
        }

        return self.memory

    def loadWorkingMemory(self, session_id, user_id):
        key = f"wm:{user_id}:{session_id}"
        data = r.get(key)
        if not data:
            return None

        wm = json.loads(data)
        wm.setdefault("user_id", user_id)
        return wm

    def save_working_memory(self, session_id: str, user_id: str):
        self.memory["timestamps"]["updated_at"] = now()
        key = f"wm:{user_id}:{session_id}"
        r.set(key, json.dumps(self.memory))

    def clear_working_memory(self, session_id: str, user_id: str):
        key = f"wm:{user_id}:{session_id}"
        r.delete(key)

    def add_item_to_order(self, item: CartItem, session_id: str, user_id: str):
        self.memory = self.loadWorkingMemory(session_id, user_id)
        if not self.memory:
            self.memory = self.createWorkingMemory(user_id, session_id)

        self.memory["cart"].append({
            "name": item["name"],
            "quantity": item["quantity"],
            "price": item["price"],
            "color": item["color"]
        })

        self.save_working_memory(session_id, user_id)

        return self.memory
    
    def remove_item_from_order(self, item_name: str, session_id: str, user_id: str):
        # Load working memory
        self.memory = self.loadWorkingMemory(session_id, user_id)

        if not self.memory:
            raise RuntimeError("No working memory found for this session.")

        original_len = len(self.memory["cart"])


        def should_keep(item):
            return item["name"].lower() != item_name.lower()

        self.memory["cart"] = list(filter(should_keep, self.memory["cart"]))

        if len(self.memory["cart"]) == original_len:
            raise ValueError(f"Item '{item_name}' not found in cart.")

        self.save_working_memory(session_id, user_id)
        return self.memory

    
    def clear_order(self):
        self.memory["cart"] = []
        self.memory["flags"]["awaiting_confirmation"] = False
        return self.memory