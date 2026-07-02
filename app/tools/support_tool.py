"""
Support Tools — order status, payment status, session restart, subscription check.
All data comes from the live ecommerce backend (NOT hardcoded stubs).
"""

import os
import requests
from typing import Any, Dict


BACKEND_URL = os.getenv("BACKEND_URL", "http://host.docker.internal:5132")


def check_order_status(order_id: str, user_id: str = "") -> Dict[str, Any]:
    """Fetch real order status from the backend."""
    if not order_id:
        return {"error": "order_id required"}

    endpoint = f"{BACKEND_URL}/api/order/{order_id}"
    try:
        resp = requests.get(endpoint, params={"userId": user_id}, timeout=5)
        if resp.status_code == 404:
            return {"error": f"Order {order_id} not found."}
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            order = data[0]
            return {
                "order_id": order_id,
                "status": order.get("status", "unknown"),
                "created_at": order.get("createdAt", ""),
                "items": order.get("items", []),
            }
        return {"error": f"Order {order_id} not found."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Could not reach order service.", "details": str(e)}


def check_payment_status(order_id: str, user_id: str = "") -> Dict[str, Any]:
    """Fetch payment status from the backend's order record."""
    if not order_id:
        return {"error": "order_id required"}

    order = check_order_status(order_id, user_id)
    if "error" in order:
        return order

    status = order.get("status", "")
    paid = status.lower() == "paid"
    return {
        "order_id": order_id,
        "paid": paid,
        "status": status,
        "message": "Order has been paid." if paid else "Order has not been paid yet."
    }


def restart_user_session(user_id: str) -> Dict[str, Any]:
    """Clear backend sessions for this user to force a fresh start."""
    if not user_id:
        return {"error": "user_id required"}

    # GET all sessions for user, then DELETE each
    endpoint = f"{BACKEND_URL}/api/session"
    try:
        # List sessions
        resp = requests.get(endpoint, params={"userId": user_id}, timeout=5)
        resp.raise_for_status()
        sessions = resp.json()

        if not sessions:
            return {"user_id": user_id, "result": "no_sessions_found"}

        # Delete each session
        deleted = 0
        for s in sessions:
            sid = s.get("id", "")
            if sid:
                try:
                    d = requests.delete(f"{endpoint}/{sid}", timeout=5)
                    if d.status_code == 200:
                        deleted += 1
                except requests.exceptions.RequestException:
                    pass

        return {
            "user_id": user_id,
            "result": "session_restarted",
            "sessions_cleared": deleted,
            "message": "Your session has been refreshed."
        }
    except requests.exceptions.RequestException as e:
        return {"error": "Unable to restart session.", "details": str(e)}


def check_subscription(user_id: str) -> Dict[str, Any]:
    """Check if user has active orders (inferred subscription from order history)."""
    if not user_id:
        return {"error": "user_id required"}

    endpoint = f"{BACKEND_URL}/api/order"
    try:
        resp = requests.get(endpoint, timeout=5)
        resp.raise_for_status()
        all_orders = resp.json()

        user_orders = [
            o for o in all_orders
            if o.get("userId") == user_id
        ]

        if not user_orders:
            return {
                "user_id": user_id,
                "has_orders": False,
                "order_count": 0,
                "message": "No orders found for this account."
            }

        paid = [o for o in user_orders if o.get("status", "").lower() == "paid"]
        return {
            "user_id": user_id,
            "has_orders": True,
            "order_count": len(user_orders),
            "paid_orders": len(paid),
            "message": f"{len(user_orders)} order(s), {len(paid)} paid."
        }
    except requests.exceptions.RequestException as e:
        return {"error": "Unable to check subscription.", "details": str(e)}
