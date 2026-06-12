from config.settings import db, async_db, get_pg_pool, sales_tool, client, memory
from app.safety import sanitize_text, validate_input, logger
from services.memory.working_memory import WorkingMemory
from app.logs.logging_helper import log_error, log_info
from google.genai import types
from services.memory.mem0_memory import Mem0MemoryManager
from services.memory.db_memory import MemoryService


working_mem = WorkingMemory()
mem0_memory = Mem0MemoryManager()
memory_service = MemoryService(db_url=async_db)


async def init_services():
    await memory.init_vector_db()

# ─── Constants ───────────────────────────────────────────────────────────────

SUMMARIZE_AFTER_N_MESSAGES = 12
KEEP_LAST_N_VERBATIM       = 4
HISTORY_WINDOW             = 8


# ─── Summarization ───────────────────────────────────────────────────────────

async def maybe_summarize(session_id: str, user_id: str):
    """
    Fires when history hits SUMMARIZE_AFTER_N_MESSAGES.
    Compresses older messages, chains with existing summary,
    trims Redis, and persists immediately to PostgreSQL.
    """
    total = working_mem.get_history_length(session_id, user_id)

    if total < SUMMARIZE_AFTER_N_MESSAGES:
        return

    log_info(f"Summarization triggered at {total} messages for session {session_id}")

    all_messages = working_mem.load_full_history(session_id, user_id)
    old_messages = all_messages[:-KEEP_LAST_N_VERBATIM]

    old_text = "\n".join(
        [f"{m['role'].upper()}: {m['content']}" for m in old_messages]
    )

    existing_summary = working_mem.load_summary(session_id, user_id)
    prior_context    = f"Prior summary:\n{existing_summary}\n\n" if existing_summary else ""

    summary_prompt = f"""
You are a memory assistant for a sales and support agent.
Compress this conversation into a short, dense summary under 200 words.

Capture ALL of the following if present:
- Customer name or identifier
- What the customer wants (product interest, complaint, question)
- Items discussed or added to cart
- Decisions made or confirmed
- Unresolved issues or pending actions
- Customer tone (frustrated, happy, undecided)

Be factual, no filler.

{prior_context}New conversation to summarize:
{old_text}
"""

    try:
        summary_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Content(
                role="user",
                parts=[types.Part(text=summary_prompt)]
            )]
        )
        summary = summary_response.text.strip()

        # Save to Redis (hot cache)
        working_mem.save_summary(session_id, user_id, summary)

        # Trim Redis history to only recent messages
        working_mem.trim_history(session_id, user_id, keep_last_n=KEEP_LAST_N_VERBATIM)

        # Persist to PostgreSQL immediately so it survives Redis expiry
        recent_messages = working_mem.load_history(session_id, user_id, last_n=KEEP_LAST_N_VERBATIM)
        await memory_service.write(
            user_id=user_id,
            key=f"session:{session_id}:history",
            value={"messages": recent_messages},
            summary=summary
        )

        log_info(f"Summary saved to Redis + PostgreSQL for session {session_id}")

    except Exception as e:
        log_error(f"Summarization failed: {e}")


# ─── Session Loader (Redis → PostgreSQL fallback) ────────────────────────────

async def load_session(session_id: str, user_id: str):
    """
    Try Redis first. On miss (expired session or returning user),
    fall back to PostgreSQL and warm Redis back up.

    Returns:
        recent_messages : list of {role, content} dicts
        summary         : str or None
    """

    # Fast path — Redis hit
    recent  = working_mem.load_history(session_id, user_id, last_n=HISTORY_WINDOW)
    summary = working_mem.load_summary(session_id, user_id)

    if recent or summary:
        log_info("Session loaded from Redis cache")
        return recent, summary

    # Slow path — Redis miss, fall back to PostgreSQL
    log_info("Redis miss — loading session from PostgreSQL")

    try:
        db_records = await memory.read(user_id=user_id, limit=1)
    except Exception as e:
        log_error(f"Failed to load session from PostgreSQL: {e}")
        return [], None

    if not db_records:
        log_info("No session found in PostgreSQL — new user")
        return [], None

    latest   = db_records[0]
    messages = latest.get("value", {}).get("messages", [])
    summary  = latest.get("summary")

    # Warm Redis back up with the most recent messages
    for msg in messages[-HISTORY_WINDOW:]:
        working_mem.add_message(session_id, user_id, msg["role"], msg["content"])

    if summary:
        working_mem.save_summary(session_id, user_id, summary)

    log_info(f"Session restored — {len(messages)} messages, summary={'yes' if summary else 'no'}")
    return messages[-HISTORY_WINDOW:], summary


# ─── Orchestrator ────────────────────────────────────────────────────────────

async def orchestrate(user_id: str, session_id: str) -> dict:
    """
    Assemble the three-layer memory context for the agent.

    Returns a dict with:
        recent_messages : list of {role, content}   (short-term)
        summary         : str or None                (mid-term)
        preferences     : str or None                (long-term / mem0)
        session_state   : dict or None               (cart, intent, flags)
    """

    # Short-term + mid-term with DB fallback
    recent_messages, summary = await load_session(session_id, user_id)

    # Long-term — customer preferences and history from mem0
    preferences = None
    try:
        mem0_result = mem0_memory.mem0_search(
            user_id=user_id,
            query="customer preferences purchase history support issues",
            limit=5
        )
        if mem0_result:
            preferences = str(mem0_result)
            log_info("Long-term preferences loaded from mem0")
    except Exception as e:
        log_error(f"mem0 search failed: {e}")

    # Session state — cart, checkout, flags
    session_state = working_mem.loadWorkingMemory(session_id, user_id)

    return {
        "recent_messages": recent_messages,
        "summary": summary,
        "preferences": preferences,
        "session_state": session_state
    }
