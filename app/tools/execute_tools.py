from app.logs.logging_helper import log_error, log_info
from app.tools import support_tool
import time
from config.settings import sales_tool
from services.RAG.rag_query import get_info_from_pdf
from services.memory.mem0_memory import Mem0MemoryManager
from services.memory.working_memory import WorkingMemory
import json

mem0_memory = Mem0MemoryManager()
working_mem = WorkingMemory()

async def execute_tools(function_calls, user_id, orchestrated_message):
    results = []
    tool_names = []

    for fc in function_calls:
        fn_name = fc.name
        args = fc.args or {}
        tool_names.append(fn_name)

        try:
            if fn_name == "calculate_total_product_cost":
                output = sales_tool.calculate_total_product_cost(
                    product_id=args.get("product_id"),
                    quantity=args.get("quantity", 1),
                )

            elif fn_name == "search_product":
                output = sales_tool.search_product(name=args.get("name"))

            elif fn_name == "process_payment":
                output = sales_tool.process_payment(order=args.get("order"), amount=args.get("amount"))

            elif fn_name == "generate_quote":
                output = sales_tool.generate_quote(
                    customer_name=args.get("customer_name"),
                    product=args.get("product"),
                    quantity=args.get("quantity", 1),
                )

            elif fn_name == "add_item_to_order":
                # print("Adding item to order with args:", args)
                output = working_mem.add_item_to_order(
                    item=args.get("item"),
                    session_id=args.get("session_id"),
                    user_id=args.get("user_id")
                )
            elif fn_name == "remove_item_from_order":
                output = working_mem.remove_item_from_order(
                    item_name=args.get("item_name"),
                    session_id=args.get("session_id"),
                    user_id=args.get("user_id")
                )

            elif fn_name == "generate_quote":
                output = sales_tool.generate_quote(
                    customer_name=args.get("customer_name"),
                    product=args.get("product"),
                    quantity=args.get("quantity", 1),
                )

            elif fn_name == "suggest_upsells":
                output = sales_tool.suggest_upsells(product=args.get("product"))

            elif fn_name == "retrieve_memory":
                mem = mem0_memory.mem0_search(user_id=user_id, query=orchestrated_message, limit=10)
                output = json.dumps(mem or {})

            elif fn_name == "search_knowledge_base":
                found = get_info_from_pdf(business_id=0, query=orchestrated_message)
                output = json.dumps(found)

            elif fn_name == "check_order_status":
                result = support_tool.check_order_status(args.get("order_id"))
                output = json.dumps(result)

            elif fn_name == "check_payment_status":
                result = support_tool.check_payment_status(args.get("order_id"))
                output = json.dumps(result)

            elif fn_name == "restart_user_session":
                result = support_tool.restart_user_session(args.get("user_id"))
                output = json.dumps(result)

            elif fn_name == "check_subscription":
                result = support_tool.check_subscription(args.get("user_id"))
                output = json.dumps(result)

            else:
                output = "Tool not recognized."

            # Save tool use + result to memory
            try:
                mem0_memory.mem0_add(
                    user_id=user_id,
                    namespace="business",
                    messages=[{"role": "assistant", "content": f"{fn_name} = {output}"}],
                    metadata={"ts": time.time()}
                )
            except Exception as e:
                log_error(f"Failed to save tool output to memory: {e}")

            results.append(output)

        except Exception as e:
            log_error(f"Tool {fn_name} execution failed: {e}")
            results.append(f"Error executing {fn_name}: {str(e)}")

    return tool_names, results