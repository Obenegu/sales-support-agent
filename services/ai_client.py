import json
import asyncio
import socket
from pydantic import BaseModel
from services.classify_intent import classify_intent, is_task_complete
from google.genai import types
from config.settings import client, sales_tool, SYSTEM_PROMPT, db, memory
from app.orchestrator import orchestrate, maybe_summarize
from services.memory.mem0_memory import Mem0MemoryManager
from app.schema.sales_schema import sales_schema
from app.logs.logging_helper import log_error, log_info
from app.schema.support_schema import support_schema
from app.schema.memory_schema import memory_schema
import time
from services.RAG.rag_query import get_info_from_pdf
from app.tools.execute_tools import execute_tools
from services.memory.working_memory import WorkingMemory
from app.safety import sanitize_text, validate_input, logger

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

def build_model_preamble(memory: dict) -> str:
    """
    Build the model's grounding turn from all three memory layers.
    Injected as the first assistant message so the agent is always
    oriented before reading any conversation history.
    """
    parts = ["Understood. I am ready to assist.\n"]

    if memory.get("preferences"):
        parts.append(f"[CUSTOMER PROFILE - long-term memory]\n{memory['preferences']}\n")

    if memory.get("summary"):
        parts.append(f"[CONVERSATION SUMMARY - mid-term]\n{memory['summary']}\n")

    if memory.get("session_state"):
        state = memory["session_state"]
        cart  = state.get("cart", [])
        if cart:
            cart_lines = "\n".join(
                [f"  - {i['name']} x{i['quantity']} @ {i['price']}" for i in cart]
            )
            parts.append(f"[CURRENT CART]\n{cart_lines}\n")
        intent = state.get("current_intent")
        if intent:
            parts.append(f"[CURRENT INTENT] {intent}\n")

    return "\n".join(parts)


mem0_memory = Mem0MemoryManager()

working_mem = WorkingMemory()

observation_content = "No observations"

# ─── Retry Logic ─────────────────────────────────────────────────────────────

RETRYABLE_HTTP_CODES = {429, 502, 503, 504}
NON_RETRYABLE_HTTP_CODES = {400, 401, 403, 404}
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 2


def _is_retryable_error(exc: Exception) -> bool:
    """
    Classify an exception as retryable or non-retryable.
    Retryable: transient network/server issues.
    Non-retryable: bad requests, auth failures, client errors.
    """
    # DNS resolution errors (Errno -5, gaierror)
    if isinstance(exc, socket.gaierror):
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        # OSError with errno -5 is DNS failure
        if hasattr(exc, 'errno') and exc.errno == -5:
            return True
        return True

    # Check for HTTP status codes in the exception message
    exc_str = str(exc)
    # Extract status code from common error formats
    for code in RETRYABLE_HTTP_CODES:
        if str(code) in exc_str:
            return True
    for code in NON_RETRYABLE_HTTP_CODES:
        if str(code) in exc_str:
            return False

    # Default: retry unknown errors (safer for network blips)
    return True


async def _call_llm_with_retry(
    model: str,
    contents,
    config,
    max_retries: int = MAX_RETRIES,
    base_delay: float = BACKOFF_BASE_SECONDS
):
    """
    Call Gemini LLM with exponential backoff retry.
    Only retries transient errors (5xx, timeouts, DNS failures).
    Immediately fails on client errors (4xx).
    """
    last_exc = None

    for attempt in range(1, max_retries + 1):
        try:
            log_info(f"LLM call attempt {attempt}/{max_retries}")
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
        except Exception as e:
            last_exc = e
            is_retryable = _is_retryable_error(e)

            if not is_retryable:
                log_error(f"Non-retryable error on attempt {attempt}: {e}")
                raise  # Don't retry 4xx errors

            if attempt >= max_retries:
                log_error(f"All {max_retries} retries exhausted. Last error: {e}")
                raise

            # Exponential backoff: 2s, 4s, 8s
            delay = base_delay * (2 ** (attempt - 1))
            log_info(f"Retryable error on attempt {attempt}: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)

    # Should never reach here, but satisfy type checker
    raise last_exc


async def ai_chat(user_message, user_id, session_id):

    # Sanitize the user message
    raw = sanitize_text(user_message)
    ok, meta = validate_input(raw)
    if not ok:
        logger.warning("Rejected user input: %s", meta)
        return "I’m sorry — I can’t help with that request. If this is a mistake, please rephrase."
    # Sanitize the user message

    log_info(f"USER: {user_message}")

    # ── Save user message to Redis history ───────────────────────────────────
    working_mem.add_message(session_id, user_id, "user", user_message)

    # ── Trigger summarization if history is getting long ─────────────────────
    # Note: maybe_summarize also persists to PostgreSQL when it fires
    await maybe_summarize(session_id, user_id)

    # ── Intent classification ─────────────────────────────────────────────────
    recent_for_intent = working_mem.load_history(session_id, user_id, last_n=6)
    intent = classify_intent(user_message, recent_for_intent)

    # Save user message to mem0 (long-term preferences)
    try:
        mem0_memory.mem0_add(
        user_id=user_id,
        namespace="business",
        messages=[{"role": "user", "content": user_message}],
        metadata={"ts": time.time()}
        )
    except Exception as e:
        log_error(f"Failed to save user message to memory: {e}")

    # ── Orchestrate: assemble three-layer memory ──────────────────────────────
    agent_full_memory = await orchestrate(user_id, session_id)

    # ── Build contents array ──────────────────────────────────────────────────
    #
    # Layout:
    #   [0]   user  → SYSTEM_PROMPT
    #   [1]   model → preamble (preferences + summary + cart state)
    #   [2..N] alternating user/model → recent conversation history
    #   [N+1] user  → current message + detected intent
    #
    preamble = build_model_preamble(agent_full_memory)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=SYSTEM_PROMPT)]
        ),
        types.Content(
            role="model",
            parts=[types.Part(text=preamble)]
        ),
    ]

    # Inject recent messages as proper conversation turns.
    # We skip the very last entry (the user message we just saved)
    # to avoid duplicating it — it's added below as the current query.
    recent = agent_full_memory["recent_messages"]
    history_to_inject = recent[:-1] if recent else []

    for msg in history_to_inject:
        # Gemini only accepts "user" and "model" roles — map "assistant" → "model"
        role = msg["role"]
        if role == "assistant":
            role = "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            )
        )

    # Current user query
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(
                text=f"Current query: {user_message}\nDetected intent: {intent}"
            )]
        )
    )


    combined_schema = sales_schema + support_schema + memory_schema

    tools = types.Tool(function_declarations=combined_schema)

    config = types.GenerateContentConfig(
        tools=[tools],
        temperature=0.6,
        max_output_tokens=2096
    )


#     contents = [
#     types.Content(
#         role="user",
#         parts=[types.Part(text=SYSTEM_PROMPT)]  # Assume SYSTEM_PROMPT includes ReAct instructions
#     ),
#     types.Content(
#         role="model",
#         parts=[types.Part(text="Understood. I am ready to assist using tools when needed.\n" + working_memory)]
#     ),
#     types.Content(
#         role="user",
#         parts=[types.Part(text=f"Current user query:\n{user_message}" + f"\nUser current intent: {intent}")]
#     )
# ]

    all_tools_used = []
    max_itrs = 20
    observation_texts= []
    
    for i in range(max_itrs):

        log_info(f"Agent step {i + 1}")
    # ----------------------------
    # First LLM call
    # ----------------------------
        try:
            response = await _call_llm_with_retry(
                model="gemini-2.5-flash",
                contents=contents,
                config=config,
                max_retries=MAX_RETRIES,
                base_delay=BACKOFF_BASE_SECONDS
            )
        except Exception as e:
            log_error(f"LLM request failed after retries: {e}")
            return normalize_output("Sorry, something went wrong. Please try again in a moment.", "none", intent)

        candidate = response.candidates[0]
        parts = candidate.content.parts if candidate.content else []


        # Append model's raw output to history
        contents.append(types.Content(role="model", parts=parts))

        # Check for function calls (can be multiple)
        function_calls = [p.function_call for p in parts if p.function_call is not None]

        if not function_calls:
            log_info("No valid function calls detected this turn.")
        else:
            log_info(f"Detected {len(function_calls)} function call(s): {[fc.name for fc in function_calls]}")

        # ----------------------------------------
        # If LLM triggered a tool
        # ----------------------------------------
        if function_calls:

            tool_names, tool_outputs = await execute_tools(function_calls, user_id, user_message)
            all_tools_used.extend(tool_names)

            log_info(f"All Tool used: {all_tools_used}")

            # Feed all observations back (one per tool, in order)
            observation_texts = [
                f"Observation from {name}: {output}"
                for name, output in zip(tool_names, tool_outputs)
            ]

            observation_content = "\n\n".join(observation_texts)

            log_info(f"Observations per tool call: {observation_content}")

            contents.append(
                types.Content(
                    role="model",
                    parts=[types.Part(text=observation_content)]
                )
            )
            # Continue the loop
            continue

        # No function calls → this should be the final response
        final_reply = response.text.strip()

        if not observation_texts:
            observation_content = "No Observations"

        print(observation_content)


        if not is_task_complete(final_reply, observation_content):
            log_error("Model stopped before completing task — forcing continuation")

            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part(
                        text=(
                            "The task is not complete yet. "
                            "You must perform the remaining required actions using tools. "
                            "Do NOT respond with text until the task is complete."
                        )
                    )]
                )
            )
            continue  # 🔁 loop again

        # Extract the actual response if it used "Action: respond"
        # Optional: strip any lingering reasoning prefixes if your SYSTEM_PROMPT forces ReAct format
        if final_reply.startswith("Thought:") or final_reply.startswith("Action:"):
            # Take everything after the last "Action: respond" or fallback to full text
            if "Action: respond" in final_reply:
                final_reply = final_reply.split("Action: respond", 1)[-1].strip()
            else:
                final_reply = final_reply.split("Thought:", 1)[-1].strip()

        
        log_info(f"MODEL FINAL: {final_reply}")

        # ── Save assistant reply to Redis ─────────────────────────────────────
        working_mem.add_message(session_id, user_id, "assistant", final_reply)

        # ── Persist full session to PostgreSQL ────────────────────────────────
        # This runs after every reply so returning users are never lost
        try:
            all_messages = working_mem.load_full_history(session_id, user_id)
            current_summary = working_mem.load_summary(session_id, user_id)

            await memory.write(
                user_id=user_id,
                key=f"session:{session_id}:history",
                value={"messages": all_messages},
                summary=current_summary
            )
            log_info(f"Session persisted to PostgreSQL for user {user_id}")
        except Exception as e:
            log_error(f"Failed to persist session to PostgreSQL: {e}")

        # Save assistant reply to mem0
        try:
            mem0_memory.mem0_add(
            user_id=user_id,
            namespace="business",
            messages=[{"role": "assistant", "content": final_reply}],
            metadata={"ts": time.time()}
            )
        except Exception as e:
            log_error(f"Failed to save final reply to memory: {e}")

        tools_str = ",".join(all_tools_used) if all_tools_used else "none"

        return normalize_output(final_reply, tool_used=tools_str, intent=intent)
    
    # Fallback if max steps reached
    log_info(f"Max iterations reached. Last response: {response.text}")
    tools_str = ",".join(all_tools_used) if all_tools_used else "none"
    return normalize_output(
        "I got stuck in a loop and couldn't complete the task. Please try rephrasing.",
        tools_str,
        intent
    )
