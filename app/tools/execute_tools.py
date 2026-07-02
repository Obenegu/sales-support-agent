"""
Tool execution dispatcher.
Routes LLM function calls to the correct tool and returns observations.
"""

from app.logs.logging_helper import log_error, log_info
from app.tools import support_tool
import time
from config.settings import sales_tool
from services.memory.mem0_memory import Mem0MemoryManager
from services.memory.working_memory import WorkingMemory
import json

mem0_memory = Mem0MemoryManager()
working_mem = WorkingMemory()


async def execute_tools(function_calls, user_id, orchestrated_message, business_id: int = 1):
    results = []
    tool_names = []

    for fc in function_calls:
        fn_name = fc.name
        args = fc.args or {}
        tool_names.append(fn_name)
        log_info(f"Executing tool '{fn_name}' with args: {args}")

        try:
            # ── Sales tools ────────────────────────────────────────────────
            if fn_name == "calculate_total_product_cost":
                output = sales_tool.calculate_total_product_cost(
                    product_id=args.get("product_id"),
                    quantity=args.get("quantity", 1),
                )

            elif fn_name == "search_product":
                output = sales_tool.search_product(name=args.get("name"))

            elif fn_name == "process_payment":
                # Read the REAL cart from Redis — never trust the LLM's dict
                session_id = args.get("session_id", "")
                cart_wm = working_mem.loadWorkingMemory(session_id, user_id)
                real_cart = cart_wm.get("cart", []) if cart_wm else []

                order = {
                    "userId": user_id,
                    "OrderId": args.get("order_id", ""),
                    "items": real_cart,
                }
                output = sales_tool.process_payment(order=order, amount=args.get("amount", 0))

            elif fn_name == "generate_quote":
                output = sales_tool.generate_quote(
                    customer_name=args.get("customer_name"),
                    product=args.get("product"),
                    quantity=args.get("quantity", 1),
                )

            elif fn_name == "suggest_upsells":
                output = sales_tool.suggest_upsells(product=args.get("product"))

            elif fn_name == "add_item_to_order":
                output = working_mem.add_item_to_order(
                    item=args.get("item"),
                    session_id=args.get("session_id"),
                    user_id=user_id,
                )

            elif fn_name == "remove_item_from_order":
                output = working_mem.remove_item_from_order(
                    item_name=args.get("item_name"),
                    session_id=args.get("session_id"),
                    user_id=user_id,
                )

            # ── Support tools (real backend calls) ──────────────────────────
            elif fn_name == "check_order_status":
                result = support_tool.check_order_status(
                    order_id=args.get("order_id"),
                    user_id=args.get("user_id", user_id),
                )
                output = json.dumps(result)

            elif fn_name == "check_payment_status":
                result = support_tool.check_payment_status(
                    order_id=args.get("order_id"),
                    user_id=args.get("user_id", user_id),
                )
                output = json.dumps(result)

            elif fn_name == "restart_user_session":
                result = support_tool.restart_user_session(
                    user_id=args.get("user_id", user_id)
                )
                output = json.dumps(result)

            elif fn_name == "check_subscription":
                result = support_tool.check_subscription(
                    user_id=args.get("user_id", user_id)
                )
                output = json.dumps(result)

            else:
                output = f"Tool '{fn_name}' not recognized."

            # Save tool use to mem0 for long-term memory
            try:
                mem0_memory.mem0_add(
                    user_id=user_id,
                    namespace="business",
                    messages=[{"role": "assistant", "content": f"{fn_name} = {output}"}],
                    metadata={"ts": time.time()}
                )
            except Exception as e:
                log_error(f"Failed to save tool output to memory: {e}")

            # ── Log tool result summary ───────────────────────────────────
            output_preview = str(output)
            if len(output_preview) > 300:
                output_preview = output_preview[:300] + "..."
            log_info(f"Tool '{fn_name}' result: {output_preview}")

            results.append(output)

        except Exception as e:
            log_error(f"Tool {fn_name} execution failed: {e}")
            results.append(f"Error executing {fn_name}: {str(e)}")

    return tool_names, results
