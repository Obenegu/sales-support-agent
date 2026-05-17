from typing import Any, Literal
from config.settings import client
from google.genai import types
from app.logs.logging_helper import log_error, log_info
import json




def classify_intent(message: str, past_messages) -> Literal["sales", "support", "general"]:
    intent = None

    contents = [
    types.Content(
        role="user",
        parts=[types.Part(text=intent_system_prompt)]  # Assume SYSTEM_PROMPT includes ReAct instructions
    ),
    types.Content(
        role="model",
        parts=[types.Part(text="Understood. I am ready to assist\n" + f"Thesae are the user past messages in right order:\n {past_messages}")]
    ),
    types.Content(
        role="user",
        parts=[types.Part(text=f"Current user query:\n{message}")]
    )
]
    
    config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=10,
        top_p=1.0,
        top_k=1
    )

    try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite", # gemini-1.5-pro for stronger reasoning
                contents=contents,
                config=config
            )
    except Exception as e:
        log_error(f"LLM Intent request failed: {e}")
        return "Sorry, something went wrong."

    intent = response.candidates[0].content.parts[0].text.strip().lower()

    if intent == "sales":
        return "sales"
    elif intent == "support":
        return "support"
    else:
        return intent
    

def is_task_complete(response_text: str, outputs) -> bool:

    contents = [
    types.Content(
        role="user",
        parts=[types.Part(text=task_completion_judge)]  # Assume task_completion_judge includes ReAct instructions
    ),
    types.Content(
        role="model",
        parts=[types.Part(text="Understood. I am ready to assist\n" + f"These are the model's previous outputs\n {outputs}")]
    ),
    types.Content(
        role="user",
        parts=[types.Part(text=f"This is the model's final response:\n{response_text}")]
    )
]
    
    config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=10,
        top_p=1.0,
        top_k=1
    )

    try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite", # gemini-1.5-pro for stronger reasoning
                contents=contents,
                config=config
            )
    except Exception as e:
        log_error(f"LLM is_task_complete request failed: {e}")
        return True

    # is_complete = response.candidates[0].content.parts[0].text.strip().lower()
    raw_text = response.candidates[0].content.parts[0].text.strip()

    try:
        data = json.loads(raw_text)
        return bool(data.get("task_complete", False))
    except Exception as e:
        log_error(f"Failed to parse task judge output: {raw_text} | {e}")
        # fail-safe: assume complete to avoid infinite loops
        return True
    

def is_context_sufficient(question: str, context: str, past_messages: str) -> dict:
    """
    Returns dict with context_sufficient (bool) and search_query (str or None).
    """
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=memory_retrieval_judge)]
        ),
        types.Content(
            role="model",
            parts=[types.Part(text="Understood. I am the MEMORY RETRIEVAL JUDGE. I will evaluate context sufficiency and respond only with valid JSON.")]
        ),
        types.Content(
            role="user",
            parts=[types.Part(text=f"""
User's current question:
{question}

Retrieved PDF context:
{context if context else "No PDF context retrieved."}

Last 10 conversation exchanges:
{past_messages}
""")]
        ),
    ]

    config = types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=150,
        top_p=1.0,
        top_k=1
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config=config
        )
        raw_text = response.candidates[0].content.parts[0].text.strip()
        # Strip markdown code fences if model adds them
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_text)
        return {
            "context_sufficient": bool(data.get("context_sufficient", False)),
            "search_query": data.get("search_query", None),
            "reason": data.get("reason", "")
        }
    except Exception as e:
        log_error(f"Judge failed: {e}")
        # Fail-safe: treat as sufficient to avoid infinite loops
        return {"context_sufficient": True, "search_query": None, "reason": "judge failed"}


intent_system_prompt = """
You are an intent classification model.

Your ONLY task is to analyze the user's message and determine their primary intent.

Possible intents:
- sales → The user is asking about prices, plans, packages, upgrades, availability, purchasing, subscriptions, or comparisons before buying.
- support → The user is experiencing a problem, error, failure, bug, or is asking for help using or fixing something they already have.
- general → The user is asking for general information, explanations, definitions, advice, or conversation not related to buying or fixing a product.

Rules:
- Respond with ONLY ONE word: sales, support, or general.
- Do NOT explain your reasoning.
- Do NOT include punctuation, formatting, or extra text.
- If the intent is ambiguous, choose the MOST LIKELY intent based on context.
- Assume previous chat messages may be provided and should be used to infer intent.
- Ignore greetings unless they include a clear intent.
- Never ask questions.

Output format:
sales
OR
support
OR
general

"""

memory_retrieval_judge = """
You are a MEMORY RETRIEVAL JUDGE.

Your ONLY responsibility is to determine whether the provided
conversation history contains SUFFICIENT CONTEXT to answer
the user's current question accurately.

You do NOT answer the question.
You do NOT call tools.
You do NOT suggest what the answer might be.
You ONLY evaluate whether enough context exists.

────────────────────────────────────────
INPUT YOU WILL RECEIVE
────────────────────────────────────────
You will be given:
1. The user's current message
2. The last 10 conversation exchanges (user message + agent response pairs)
3. A piece of information retrieved from the company's files or past interactions that is relevant to the user's question

The conversation exchanges are the SOURCE OF TRUTH.
Do NOT assume knowledge that is not present in them.

────────────────────────────────────────
HOW TO DECIDE SUFFICIENCY
────────────────────────────────────────
Context is SUFFICIENT if and ONLY if:

1. The user's question can be answered directly
   from the provided exchanges

AND

2. No critical background information is missing
   that would change or invalidate the answer

AND

3. The question does NOT reference a past event,
   issue, or interaction that is absent from the exchanges

If ANY condition is missing,
context is INSUFFICIENT.

────────────────────────────────────────
CRITICAL RULES
────────────────────────────────────────
- NEVER assume facts not present in the exchanges
- NEVER guess what a previous interaction might have contained
- NEVER treat a partial match as sufficient
- NEVER allow a vague or incomplete answer to pass as sufficient
- If the user references "last time", "previously", "the issue I had",
  or any past event — verify it exists in the exchanges before marking sufficient

If the exchanges do not clearly satisfy the informational
needs of the user's question, context is INSUFFICIENT.

────────────────────────────────────────
OUTPUT FORMAT (STRICT)
────────────────────────────────────────
You MUST respond with ONLY valid JSON.
No markdown. No explanations. No preamble.

Schema:
{
  "context_sufficient": true | false,
  "search_query": "<specific query to search memory — ONLY if context_sufficient is false, else null>",
  "reason": "<short, precise reason>"
}

Examples of valid reasons:
- "User references a past delivery issue not found in the last 10 exchanges"
- "No prior mention of this product in the conversation history"
- "All relevant context for this question is present in the exchanges"
- "User says 'last time' but no matching prior exchange exists"

────────────────────────────────────────
FINAL REMINDER
────────────────────────────────────────
You are the GATE before the agent speaks.
If you mark context as sufficient when it is not,
the agent will give an incomplete or incorrect answer.
Be strict.

"""


task_completion_judge = """
You are a TASK COMPLETION JUDGE.

Your ONLY responsibility is to determine whether the user's request
has been FULLY completed.

You do NOT execute actions.
You do NOT call tools.
You do NOT suggest next steps.
You ONLY evaluate completion.

────────────────────────────────────────
INPUT YOU WILL RECEIVE
────────────────────────────────────────
You will be given:
1. The user's original request
2. The latest assistant response
3. The current Working Memory state (authoritative)
4. The list of tools that were actually executed

The Working Memory is the SOURCE OF TRUTH.
Textual promises or intentions DO NOT count as completion.

────────────────────────────────────────
HOW TO DECIDE COMPLETION
────────────────────────────────────────
A task is COMPLETE if and ONLY if:

1. All required state changes requested by the user
   are reflected in Working Memory

AND

2. No required action remains pending

AND

3. The assistant did NOT merely promise to act
   (e.g. "I will add...", "I am going to update...")
   without evidence in Working Memory

If ANY required condition is missing,
the task is NOT complete.

────────────────────────────────────────
CRITICAL RULES
────────────────────────────────────────
• NEVER trust natural language confirmations
• NEVER assume actions were performed
• NEVER infer missing state
• NEVER accept partial completion
• NEVER allow termination if the state is incorrect

If Working Memory does not clearly satisfy the user's request,
the task is NOT complete.

────────────────────────────────────────
OUTPUT FORMAT (STRICT)
────────────────────────────────────────
You MUST respond with ONLY valid JSON.
No markdown. No explanations.

Schema:
{
  "task_complete": true | false,
  "reason": "<short, precise reason>"
}

Examples of valid reasons:
- "Cart quantity does not match requested value"
- "Required item not present in cart"
- "Assistant promised an action that was not executed"
- "Working Memory reflects all requested changes"

────────────────────────────────────────
FINAL REMINDER
────────────────────────────────────────
You are the FINAL GATE.
If you allow termination when the task is incomplete,
the system is incorrect.
Be strict.

"""