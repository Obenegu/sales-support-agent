# app/tools/support_tools.py
import datetime
from typing import Dict, Any

# NOTE: Replace stub logic with real DB/API queries in production.

def check_order_status(order_id: str) -> Dict[str, Any]:
    """
    Return a simulated order status. Replace with DB/API call.
    """
    # Basic validation
    if not order_id:
        return {"error": "order_id required"}

    # Example stubbed results (in production, query your orders DB)
    fake_db = {
        "1234": {"status": "shipped", "shipped_at": "2025-11-12T14:23:00Z", "eta": "2025-11-18"},
        "5678": {"status": "processing", "placed_at": "2025-11-15T09:00:00Z"}
    }

    order = fake_db.get(order_id)
    if not order:
        return {"error": f"Order {order_id} not found."}

    return {"order_id": order_id, "order": order}

def check_payment_status(order_id: str) -> Dict[str, Any]:
    """
    Return a simulated payment status for an order.
    """
    if not order_id:
        return {"error": "order_id required"}

    fake_payments = {
        "1234": {"paid": True, "method": "card", "paid_at": "2025-11-12T14:20:00Z"},
        "5678": {"paid": False, "method": None}
    }

    payment = fake_payments.get(order_id)
    if not payment:
        return {"error": f"No payment record for order {order_id}."}

    return {"order_id": order_id, "payment": payment}

def restart_user_session(user_id: str) -> Dict[str, Any]:
    """
    Attempt to restart a user session. Real implementation: clear session tokens etc.
    """
    if not user_id:
        return {"error": "user_id required"}

    # stub: pretend we restarted the session
    return {
        "user_id": user_id,
        "result": "session_restarted",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

def check_subscription(user_id: str) -> Dict[str, Any]:
    """
    Return subscription status (simulated).
    """
    if not user_id:
        return {"error": "user_id required"}
    
    print(f"User Id: {user_id}")
    
    fake_subs = {
        "user_1": {"status": "active", "plan": "pro", "renewal": "2026-01-01"},
        "user_2": {"status": "canceled", "plan": "free"}
    }

    sub = fake_subs.get(user_id)
    if not sub:
        return {"user_id": user_id, "status": "none"}

    return {"user_id": user_id, "subscription": sub}
