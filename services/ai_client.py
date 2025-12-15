import json
from pydantic import BaseModel
from services.classify_intent import classify_intent
from google.genai import types
from config.settings import client, sales_tool, SYSTEM_PROMPT, db
from app.orchestrator import orchestrate, memory
from app.tools.schema import sales_schema
from app.logs.logging_helper import log_error, log_info
from app.tools.support_schema import support_schema
from app.tools import support_tool
from app.orchestrator import memory
import time


class ChatResponse(BaseModel):
    response: str
    intent: str
    tool_used: str


def normalize_output(raw_text, tool_used, intent):
    """Ensures the model output ALWAYS has the correct schema."""
    try:
        data = json.loads(raw_text)
    except:
        return {
            "response": raw_text,
            "intent": intent,
            "tool_used": tool_used,
            "role": "assistant"
        }

    # Fix missing fields
    response_text = data.get("response") or data.get("content") or raw_text
    intent_value = data.get("intent", intent)
    tool_value = data.get("tool_used", tool_used)

    # ❗ force tool_used to always be a string
    tool_value = data.get("tool_used") or tool_used or "none"
    if tool_value is None:
        tool_value = "none"

    return {
        "response": response_text,
        "intent": intent_value,
        "tool_used": str(tool_value),
        "role": "assistant"
    }


async def ai_chat(user_message, user_id):

    log_info(f"USER: {user_message}")

    combined_schema = sales_schema + support_schema

    tools = types.Tool(function_declarations=combined_schema)

    intent = classify_intent(user_message)

    orchestrated_message = await orchestrate(message=user_message, user_id=user_id)

    # Save to memory
    try:
        memory_result = memory.mem0_add(
        user_id=user_id,
        namespace="business",
        messages=[{"role": "user", "content": user_message}],
        metadata={"ts": time.time()}
        )

        if memory_result is None:
            log_error("Memory add failed.")
        else:
            log_info(f"Memory add succeeded: {user_message}")
            print(memory_result)

    except Exception as e:
        log_error(f"Failed to save user message to memory: {e}")



    config = types.GenerateContentConfig(
        tools=[tools],
        temperature=0.6,
        max_output_tokens=4096
    )

    contents = types.Content(role="user", parts=[
        types.Part(text=SYSTEM_PROMPT + "\n\n" + orchestrated_message)
    ])

    max_itrs = 20
    for i in range(0, max_itrs):

    # ----------------------------
    # First LLM call
    # ----------------------------
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[contents],
                config=config
            )
        except Exception as e:
            log_error(f"LLM request failed: {e}")
            return {
                "response": "Sorry, something went wrong.",
                "intent": intent,
                "tool_used": "none",
                "role": "assistant"
            }

        candidate = response.candidates[0]
        parts = candidate.content.parts if candidate.content else []

        # ----------------------------------------
        # If LLM triggered a tool
        # ----------------------------------------
        if parts and hasattr(parts[0], "function_call"):

            fn_call = parts[0].function_call

            if fn_call is None:
                # Should not happen, but safe fallback
                log_info("Function call part exists but no fn_call object.")
                normalized = normalize_output(response.text, tool_used="none", intent=intent)
                return normalized

            fn_name = fn_call.name
            args = fn_call.args

            log_info(f"Tool triggered: {fn_name} | Args: {args}")

            try:
                # Execute tool
                if fn_name == "calculate_price":
                    result = sales_tool.calculate_price(
                        product_name=args.get("product_name"),
                        quantity=args.get("quantity", 1),
                    )
                    tool_output = f"The total price is: ${result}"

                elif fn_name == "generate_quote":
                    tool_output = sales_tool.generate_quote(
                        customer_name=args.get("customer_name"),
                        product=args.get("product"),
                        quantity=args.get("quantity", 1),
                    )

                elif fn_name == "suggest_upsells":
                    tool_output = sales_tool.suggest_upsells(
                        product=args.get("product")
                    )
                # # Memory Tool
                # elif fn_name == "memory_write":
                #     # IMPORTANT: DO NOT allow user-supplied arbitrary user_id in prod — extract from JWT
                #     # user_id = args.get("user_id")
                #     # value should be parsed as a JSON object from the LLM args
                #     value = args.get("value") or {}
                #     summary = args.get("summary")
                #     mem_result = await memory.write(user_id=user_id, key=args["key"], value=value, summary=summary)
                #     tool_output = json.dumps(mem_result)

                # elif fn_name == "memory_read":
                #     # user_id = args.get("user_id")
                #     mem = await memory.read(user_id=user_id, limit=10)
                #     tool_output = json.dumps(mem or {})

                # elif fn_name == "memory_search":
                #     # user_id = args.get("user_id")
                #     # user_id = args.get("user_id")
                #     # found = await memory.search(user_id=user_id, query=args["query"], limit=int(args.get("limit", 5)))
                #     found = await memory.search(user_id=user_id, query=user_message, limit=10)
                #     tool_output = json.dumps(found)

                # ---------- support handlers ----------
                
                elif fn_name == "check_order_status":
                    result = support_tool.check_order_status(args.get("order_id"))
                    tool_output = json.dumps(result)

                elif fn_name == "check_payment_status":
                    result = support_tool.check_payment_status(args.get("order_id"))
                    tool_output = json.dumps(result)

                elif fn_name == "restart_user_session":
                    result = support_tool.restart_user_session(args.get("user_id"))
                    tool_output = json.dumps(result)

                elif fn_name == "check_subscription":
                    result = support_tool.check_subscription(args.get("user_id"))
                    tool_output = json.dumps(result)

                else:
                    tool_output = "Tool not recognized."

                # Save to memory
                try:
                    memory_result = memory.mem0_add(
                    user_id=user_id,
                    namespace="business",
                    messages=[{"role": "assistant", "content": f"{fn_name} = {tool_output}"}],
                    metadata={"ts": time.time()}
                    )

                    if memory_result is None:
                        log_error("Tool Memory add failed.")
                    else:
                        log_info(f"Tool Memory add succeeded\n: {fn_name}:  {tool_output}")
                        print(memory_result)
                
                except Exception as e:
                    log_error(f"Failed to save tool output to memory: {e}")

                

                # ----------------------------
                # Second LLM call (polish reply)
                # ----------------------------
                followup = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Content(role="user", parts=[types.Part(text=orchestrated_message)]),
                        types.Content(role="model", parts=[parts[0]]),
                        types.Content(role="user", parts=[types.Part(text=json.dumps(tool_output))]),
                    ],
                )

                final_reply = followup.text
                log_info(f"MODEL FINAL: {final_reply}")

                # Save to memory
                try:
                    memory.mem0_add(
                    user_id=user_id,
                    namespace="business",
                    messages=[{"role": "assistant", "content": final_reply}],
                    metadata={"ts": time.time()}
                    )
                except Exception as e:
                    log_error(f"Failed to save final reply to memory: {e}")

                return normalize_output(final_reply, tool_used=fn_name, intent=intent)

            except Exception as e:
                log_error(f"Tool execution failure: {e}")
                return {
                    "response": "An internal tool error occurred.",
                    "intent": intent,
                    "tool_used": fn_name,
                    "role": "assistant"
                }

        # --------------------------------------------------------
        # NO TOOL CALL — Just return the model output normally
        # --------------------------------------------------------
        # log_info(f"MODEL RESPONSE: {response.text}")
        # return normalize_output(response.text, tool_used=fn_name, intent=intent)
    
    log_info(f"MODEL RESPONSE: {response.text}")
    # Save to memory
    try:
        memory.mem0_add(
        user_id=user_id,
        namespace="business",
        messages=[{"role": "assistant", "content": response.text}],
        metadata={"ts": time.time()}
        )
    except Exception as e:
        log_error(f"Failed to save final response to memory: {e}")

    return normalize_output(response.text, tool_used=fn_name, intent=intent)
