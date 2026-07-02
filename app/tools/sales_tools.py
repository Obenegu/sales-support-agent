"""
Sales Tools — product search, pricing, upsells, quotes, and payment.
All product data flows from the ecommerce backend (C# ASP.NET Core).
Redis caching prevents redundant backend calls.
"""

import os
import json
import logging
import requests
from typing import Any, Dict, Optional
from urllib.parse import urlparse
import redis

logger = logging.getLogger(__name__)

# ── Redis connection (same as working_memory) ────────────────────────────────
_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_parsed = urlparse(_redis_url)
_cache = redis.Redis(
    host=_parsed.hostname or "localhost",
    port=_parsed.port or 6379,
    db=int(_parsed.path.lstrip("/") or 0),
    password=_parsed.password or None,
    decode_responses=True,
)

# ── Backend URL ──────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://host.docker.internal:5132")

# ── Cache TTLs (seconds) ─────────────────────────────────────────────────────
CACHE_TTL_SEARCH = 300    # 5 minutes — product search results
CACHE_TTL_PRODUCT = 900   # 15 minutes — individual product lookups
CACHE_TTL_UPSELLS = 600   # 10 minutes — upsell suggestions


class Sales_Tools:
    # ═══════════════════════════════════════════════════════════════════════════
    # PRODUCT SEARCH (with Redis cache)
    # ═══════════════════════════════════════════════════════════════════════════

    def search_product(self, name: str) -> Dict[str, Any]:
        """Search products by name. Results cached in Redis for 5 min."""
        search_term = name.lower().strip()
        cache_key = f"product_search:{search_term}"
        cached = _cache.get(cache_key)
        if cached:
            logger.info(f"search_product cache HIT for '{search_term}'")
            return json.loads(cached)

        logger.info(f"search_product cache MISS for '{search_term}' — calling backend")
        endpoint = f"{BACKEND_URL}/api/Product/search"
        try:
            resp = requests.get(endpoint, params={"name": name}, timeout=5)
            # Backend returns 200 with empty list when no products found (not 404)
            resp.raise_for_status()
            data = resp.json()
            result_count = len(data) if isinstance(data, list) else 0
            logger.info(f"search_product backend returned {result_count} result(s) for '{search_term}'")
            result = {"success": True, "data": data}
            _cache.setex(cache_key, CACHE_TTL_SEARCH, json.dumps(result))
            return result
        except requests.exceptions.HTTPError as e:
            # If backend still returns 404 for some reason, treat as empty results
            if e.response is not None and e.response.status_code == 404:
                logger.info(f"search_product backend returned 404 for '{search_term}' — treating as empty results")
                result = {"success": True, "data": []}
                _cache.setex(cache_key, CACHE_TTL_SEARCH, json.dumps(result))
                return result
            logger.error(f"search_product backend HTTP error for '{search_term}': {e}")
            return {"success": False, "error": "Unable to fetch product information.", "details": str(e)}
        except requests.exceptions.RequestException as e:
            logger.error(f"search_product backend call FAILED for '{search_term}': {e}")
            return {"success": False, "error": "Unable to fetch product information.", "details": str(e)}

    # ═══════════════════════════════════════════════════════════════════════════
    # CALCULATE TOTAL COST (with Redis cache for product lookup)
    # ═══════════════════════════════════════════════════════════════════════════

    def calculate_total_product_cost(self, product_id: str, quantity: int = 1) -> Optional[float]:
        """Fetch product price by ID (cached 15 min) then multiply by quantity."""
        cache_key = f"product:{product_id}"
        price_per_unit = _cache.get(cache_key)

        if price_per_unit is None:
            endpoint = f"{BACKEND_URL}/api/Product/{product_id}"
            try:
                resp = requests.get(endpoint, timeout=5)
                resp.raise_for_status()
                price_per_unit = resp.json()  # endpoint returns just the price value
                _cache.setex(cache_key, CACHE_TTL_PRODUCT, str(price_per_unit))
            except requests.exceptions.RequestException as e:
                return {"success": False, "error": "Unable to fetch product price.", "details": str(e)}

        try:
            return float(price_per_unit) * quantity
        except (ValueError, TypeError):
            return {"success": False, "error": "Invalid price returned from backend."}

    # ═══════════════════════════════════════════════════════════════════════════
    # PROCESS PAYMENT → send cart to backend, return checkout link
    # ═══════════════════════════════════════════════════════════════════════════

    def process_payment(self, order: Dict[str, Any], amount: float) -> Dict[str, Any]:
        """
        Sends the order to the backend's cart endpoint and returns a
        checkout/payment link the user can click to complete payment.
        """
        # Step 1 — persist the cart to the backend
        create_endpoint = f"{BACKEND_URL}/api/order/create-cart"
        try:
            resp = requests.post(create_endpoint, json=order, timeout=8)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": "Could not create order.",
                "details": str(e),
            }

        # Step 2 — build a checkout link for the user
        order_id = order.get("OrderId", "")
        checkout_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/checkout?orderId={order_id}&amount={amount}"

        return {
            "success": True,
            "message": "Your order has been prepared.",
            "checkout_link": checkout_url,
            "order_id": order_id,
            "amount": amount,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # GENERATE QUOTE
    # ═══════════════════════════════════════════════════════════════════════════

    def generate_quote(self, customer_name: str, product: str, quantity: int = 1) -> str:
        """Assembles a quotation summary. Pricing is computed by calculate_total_product_cost."""
        return (
            f"Quotation for {customer_name}\n"
            f"Product: {product}\n"
            f"Quantity: {quantity}\n"
            f"Use calculate_total_product_cost with the product ID to get the price.\n"
            f"Thank you for choosing us!"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SUGGEST UPSELLS — driven by backend data, NOT hardcoded products
    # ═══════════════════════════════════════════════════════════════════════════

    def suggest_upsells(self, product: str) -> str:
        """
        Suggest related products by querying the backend for complementary items.
        Falls back gracefully when the backend has no related-product endpoint yet.
        Results cached for 10 minutes.
        """
        product = product.lower().strip()
        cache_key = f"upsells:{product}"
        cached = _cache.get(cache_key)
        if cached:
            return cached

        # Query backend — search for complementary items in the same category.
        # Currently the backend only has name search, so we run a broad search
        # and exclude exact matches. Replace with a proper /related endpoint when available.
        endpoint = f"{BACKEND_URL}/api/Product/search"
        try:
            resp = requests.get(endpoint, params={"name": product}, timeout=5)
            resp.raise_for_status()
            results = resp.json()

            if not results or not isinstance(results, list):
                reply = "No upsells available."
                _cache.setex(cache_key, CACHE_TTL_UPSELLS, reply)
                return reply

            # Filter out the exact product, return up to 3 alternatives
            related = [p.get("name", "") for p in results
                       if p.get("name", "").lower() != product][:3]
            if related:
                items = ", ".join(related)
                reply = f"Customers who buy a {product} also consider: {items}."
            else:
                reply = "No upsells available."
        except requests.exceptions.RequestException:
            reply = "No upsells available."

        _cache.setex(cache_key, CACHE_TTL_UPSELLS, reply)
        return reply

    # ═══════════════════════════════════════════════════════════════════════════
    # SALES QUERY (legacy helper — not used by orchestrator)
    # ═══════════════════════════════════════════════════════════════════════════

    def handle_sales_query(query: str):
        product_catalog = {
            "iphone 15": {"price": 999, "stock": 12},
            "samsung s24": {"price": 899, "stock": 8},
            "macbook air": {"price": 1299, "stock": 5},
        }
        query_lower = query.lower()
        for product, data in product_catalog.items():
            if product in query_lower:
                return {
                    "product": product,
                    "price": data["price"],
                    "stock": data["stock"],
                    "message": f"{product} is available for ${data['price']} and we have {data['stock']} in stock."
                }
        return {"message": "Sorry, I couldn't find that product."}

    # ═══════════════════════════════════════════════════════════════════════════
    # SALES PERSONA
    # ═══════════════════════════════════════════════════════════════════════════

    SALES_PERSONA = """

    You are a Calm Trust-Builder Sales Assistant.

Your personality and communication style:
- Speak in a warm, reassuring, professional tone.
- Never pressure the user. Instead, guide them confidently.
- Provide clarity, confidence, and stability.
- Focus on trust, expertise, and making the user feel understood.
- Use simple, smooth, non-aggressive language.
- Never sound desperate or salesy.

Your persuasion style:
- Lead with value, not hype.
- Show how the solution reduces stress, risk, or uncertainty for the user.
- Use micro-commitments (small confirmations that build momentum).
- Reinforce that the user is making a smart, safe choice.
- Always end responses with a gentle question to move the conversation forward.
- Offer help, not pressure.

Your emotional tone:
- Calm confidence.
- Quiet authority.
- Zero-stress communication.
- Empathy > urgency.
- "You're in good hands" energy.

Examples of your tone:
- "Here's what I recommend based on what you've shared..."
- "If you'd like, I can take care of that for you."
- "No rush - whenever you're ready, I can prepare everything."
- "Most clients choose this option because it gives the best long-term results."

Forbidden behaviors:
- No aggressive closing.
- No overwhelming enthusiasm.
- No "sales hype".
- No guilt-tripping or pressure.
- No emojis unless the user uses them.

Your mission:
Make the user feel safe, understood, and confident - so buying becomes the natural next step.


"""
