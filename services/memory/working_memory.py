import json
import time
from typing import Any, Dict, List, Optional
from pytz import timezone
import redis
from sqlalchemy import JSON
from datetime import datetime, timezone
from models.cart_item import CartItem  


r = redis.Redis(host="redis", port=6379, decode_responses=True)
r.set('status', 'redid it works!')
print(r.get('status'))

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

    # ─── Cart Operations ─────────────────────────────────────────────────────────

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
    

    # ─── Conversation History ────────────────────────────────────────────────────

    def add_message(self, session_id: str, user_id: str, role: str, content: str):
        """Append a single message to the conversation history list in Redis."""
        key = f"history:{user_id}:{session_id}"
        message = json.dumps({"role": role, "content": content, "ts": now()})
        r.rpush(key, message)
        r.expire(key, 60 * 60 * 24)  # TTL: 24 hours

    def load_history(self, session_id: str, user_id: str, last_n: int = 10) -> List[Dict]:
        """Load the last N messages from conversation history."""
        key = f"history:{user_id}:{session_id}"
        raw = r.lrange(key, -last_n, -1)
        return [json.loads(m) for m in raw]

    def load_full_history(self, session_id: str, user_id: str) -> List[Dict]:
        """Load the entire conversation history."""
        key = f"history:{user_id}:{session_id}"
        raw = r.lrange(key, 0, -1)
        return [json.loads(m) for m in raw]

    def get_history_length(self, session_id: str, user_id: str) -> int:
        """Return the total number of messages stored in history."""
        key = f"history:{user_id}:{session_id}"
        return r.llen(key)

    def trim_history(self, session_id: str, user_id: str, keep_last_n: int = 4):
        """
        Trim the history list to only the last N messages.
        Called after summarization to keep Redis lean.
        """
        key = f"history:{user_id}:{session_id}"
        all_messages = self.load_full_history(session_id, user_id)
        recent = all_messages[-keep_last_n:]

        # Clear and rewrite only the recent messages
        r.delete(key)
        for msg in recent:
            r.rpush(key, json.dumps(msg))
        r.expire(key, 60 * 60 * 24)

    # ─── Mid-term Summary ────────────────────────────────────────────────────────

    def save_summary(self, session_id: str, user_id: str, summary: str):
        """Persist a compressed mid-term summary of the conversation."""
        key = f"summary:{user_id}:{session_id}"
        r.set(key, summary, ex=60 * 60 * 24)  # TTL: 24 hours

    def load_summary(self, session_id: str, user_id: str) -> Optional[str]:
        """Load the mid-term summary if one exists."""
        key = f"summary:{user_id}:{session_id}"
        return r.get(key)

    def clear_summary(self, session_id: str, user_id: str):
        """Delete the summary (e.g. when a session fully resets)."""
        key = f"summary:{user_id}:{session_id}"
        r.delete(key)
