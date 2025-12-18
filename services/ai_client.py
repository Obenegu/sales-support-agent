import json
from pydantic import BaseModel
from services.classify_intent import classify_intent
from google.genai import types
from config.settings import client, sales_tool, SYSTEM_PROMPT, db
from app.orchestrator import orchestrate
from services.memory.mem0_memory import Mem0MemoryManager
from app.schema.sales_schema import sales_schema
from app.logs.logging_helper import log_error, log_info
from app.schema.support_schema import support_schema
from app.schema.memory_schema import memory_schema
import time
from services.RAG.rag_query import get_info_from_pdf
from app.tools.execute_tools import execute_tools

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


mem0_memory = Mem0MemoryManager()

async def ai_chat(user_message, user_id):


    intent = classify_intent(user_message)

    orchestrated_message = await orchestrate(message=user_message, user_id=user_id)

    log_info(f"USER: {orchestrated_message}")

    # Save to memory
    try:
        memory_result = mem0_memory.mem0_add(
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


    combined_schema = sales_schema + support_schema + memory_schema

    tools = types.Tool(function_declarations=combined_schema)

    config = types.GenerateContentConfig(
        tools=[tools],
        temperature=0.6,
        max_output_tokens=4096
    )


    contents = [
    types.Content(
        role="user",
        parts=[types.Part(text=SYSTEM_PROMPT)]  # Assume SYSTEM_PROMPT includes ReAct instructions
    ),
    types.Content(
        role="model",
        parts=[types.Part(text="Understood. I am ready to assist using tools when needed.")]
    ),
    types.Content(
        role="user",
        parts=[types.Part(text=f"Current user query:\n{user_message}")]
    )
]

    all_tools_used = []
    max_itrs = 20
    for i in range(max_itrs):

        log_info(f"Agent step {i + 1}")
    # ----------------------------
    # First LLM call
    # ----------------------------
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", # gemini-1.5-pro for stronger reasoning
                contents=contents,
                config=config
            )
        except Exception as e:
            log_error(f"LLM request failed: {e}")
            return normalize_output("Sorry, something went wrong.", "none", intent)

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
            tool_names, tool_outputs = await execute_tools(function_calls, user_id, orchestrated_message)
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
                    role="user",
                    parts=[types.Part(text=observation_content)]
                )
            )
            # Continue the loop
            continue

        # No function calls → this should be the final response
        final_reply = response.text.strip()

        # Extract the actual response if it used "Action: respond"
        # Optional: strip any lingering reasoning prefixes if your SYSTEM_PROMPT forces ReAct format
        if final_reply.startswith("Thought:") or final_reply.startswith("Action:"):
            # Take everything after the last "Action: respond" or fallback to full text
            if "Action: respond" in final_reply:
                final_reply = final_reply.split("Action: respond", 1)[-1].strip()
            else:
                final_reply = final_reply.split("Thought:", 1)[-1].strip()

        # final_reply = followup.text
        log_info(f"MODEL FINAL: {final_reply}")

        # Save to memory
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

    log_info(f"MODEL RESPONSE: {response.text}")
    
    # Fallback if max steps reached
    tools_str = ",".join(all_tools_used) if all_tools_used else "none"
    return normalize_output(
        "I got stuck in a loop and couldn't complete the task. Please try rephrasing.",
        tools_str,
        intent
    )
