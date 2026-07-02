"""
50-Scenario Automated Test Suite
=================================
Runs all 50 test scenarios (sales, support, general) against /api/chat
via HTTP POST and saves results to test_results.json.

Usage:  python test_50_scenarios.py
"""

import asyncio
import json
import time
import uuid
import httpx

BASE_URL = "http://localhost:8000"

SCENARIOS = [
    # ── Sales (1–20) ──────────────────────────────────────────────────
    {"id": 1,  "category": "sales", "message": "How much does an iPhone 15 cost?"},
    {"id": 2,  "category": "sales", "message": "Do you have Samsung phones?"},
    {"id": 3,  "category": "sales", "message": "I want to buy a laptop."},
    {"id": 4,  "category": "sales", "message": "What colors are available for the watch?"},
    {"id": 5,  "category": "sales", "message": "Can I get a discount on bulk orders?"},
    {"id": 6,  "category": "sales", "message": "Show me your best selling products."},
    {"id": 7,  "category": "sales", "message": "I need 3 bags, how much total?"},
    {"id": 8,  "category": "sales", "message": "Do you sell MacBook Air?"},
    {"id": 9,  "category": "sales", "message": "What payment methods do you accept?"},
    {"id": 10, "category": "sales", "message": "Is there free delivery?"},
    {"id": 11, "category": "sales", "message": "Can I customize the product?"},
    {"id": 12, "category": "sales", "message": "Do you have a warranty?"},
    {"id": 13, "category": "sales", "message": "I want to place an order."},
    {"id": 14, "category": "sales", "message": "What's the price of a wireless mouse?"},
    {"id": 15, "category": "sales", "message": "Do you sell headphones?"},
    {"id": 16, "category": "sales", "message": "Can I get a quote for 5 chairs?"},
    {"id": 17, "category": "sales", "message": "Tell me about your refund policy."},
    {"id": 18, "category": "sales", "message": "Do you ship internationally?"},
    {"id": 19, "category": "sales", "message": "I want to compare two products."},
    {"id": 20, "category": "sales", "message": "How long does delivery take?"},

    # ── Support (21–40) ───────────────────────────────────────────────
    {"id": 21, "category": "support", "message": "My order still hasn't arrived."},
    {"id": 22, "category": "support", "message": "I can't log into my account."},
    {"id": 23, "category": "support", "message": "My payment was declined."},
    {"id": 24, "category": "support", "message": "The app is freezing on my phone."},
    {"id": 25, "category": "support", "message": "I received a damaged item."},
    {"id": 26, "category": "support", "message": "How do I reset my password?"},
    {"id": 27, "category": "support", "message": "My refund hasn't been processed."},
    {"id": 28, "category": "support", "message": "The website is not loading."},
    {"id": 29, "category": "support", "message": "I want to cancel my subscription."},
    {"id": 30, "category": "support", "message": "Where is my invoice?"},
    {"id": 31, "category": "support", "message": "The product doesn't match the description."},
    {"id": 32, "category": "support", "message": "I'm being charged twice."},
    {"id": 33, "category": "support", "message": "Can't update my shipping address."},
    {"id": 34, "category": "support", "message": "My promo code doesn't work."},
    {"id": 35, "category": "support", "message": "The app crashed after update."},
    {"id": 36, "category": "support", "message": "How do I track my order?"},
    {"id": 37, "category": "support", "message": "I need help with the installation."},
    {"id": 38, "category": "support", "message": "My account is locked."},
    {"id": 39, "category": "support", "message": "The product I want is out of stock."},
    {"id": 40, "category": "support", "message": "I'm not receiving order confirmation emails."},

    # ── General (41–50) ───────────────────────────────────────────────
    {"id": 41, "category": "general", "message": "Hello, how are you?"},
    {"id": 42, "category": "general", "message": "What are your business hours?"},
    {"id": 43, "category": "general", "message": "Where are you located?"},
    {"id": 44, "category": "general", "message": "Tell me about your company."},
    {"id": 45, "category": "general", "message": "Do you have a physical store?"},
    {"id": 46, "category": "general", "message": "How can I contact customer service?"},
    {"id": 47, "category": "general", "message": "Thanks for your help!"},
    {"id": 48, "category": "general", "message": "What industries do you serve?"},
    {"id": 49, "category": "general", "message": "Are you hiring?"},
    {"id": 50, "category": "general", "message": "Goodbye!"},
]

async def run_scenario(client: httpx.AsyncClient, scenario: dict) -> dict:
    """Submit one scenario to /api/chat and record the result."""
    payload = {
        "userId": f"test_user_{scenario['id']}",
        "message": scenario["message"],
        "role": "user",
        "sessionId": str(uuid.uuid4()),
        "businessId": 1,
    }
    start = time.perf_counter()
    try:
        resp = await client.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            timeout=45.0,
        )
        elapsed = round(time.perf_counter() - start, 3)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "scenario_id": scenario["id"],
                "category": scenario["category"],
                "message": scenario["message"],
                "status": "pass",
                "elapsed_s": elapsed,
                "intent": data.get("intent"),
                "tool_used": data.get("tool_used"),
                "response": data.get("response", "")[:300],
            }
        else:
            return {
                "scenario_id": scenario["id"],
                "category": scenario["category"],
                "message": scenario["message"],
                "status": "fail",
                "elapsed_s": elapsed,
                "http_code": resp.status_code,
                "error": resp.text[:300],
            }
    except Exception as e:
        elapsed = round(time.perf_counter() - start, 3)
        return {
            "scenario_id": scenario["id"],
            "category": scenario["category"],
            "message": scenario["message"],
            "status": "fail",
            "elapsed_s": elapsed,
            "error": str(e)[:300],
        }


async def main():
    print(f"Running 50 scenarios against {BASE_URL}/api/chat ...\n")

    results = []
    passed = 0
    failed = 0

    async with httpx.AsyncClient() as client:
        for scenario in SCENARIOS:
            result = await run_scenario(client, scenario)
            results.append(result)
            if result["status"] == "pass":
                passed += 1
                print(f"  [{result['scenario_id']:2d}] ✅ {result['elapsed_s']:.1f}s  intent={result.get('intent','?')}  tool={result.get('tool_used','?')}")
            else:
                failed += 1
                print(f"  [{result['scenario_id']:2d}] ❌ {result['elapsed_s']:.1f}s  {result.get('error','?')[:100]}")

    summary = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(results) * 100, 1) if results else 0,
        "results": results,
    }

    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"RESULTS: {passed}/{len(results)} passed ({summary['pass_rate']}%)")
    print(f"Results saved to test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
