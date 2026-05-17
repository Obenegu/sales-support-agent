import json
from typing import Any, Dict, List

from fastapi import APIRouter, Form
import psycopg2
import os
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from app.logs.logging_helper import log_error, log_info
from config.strict_llm import call_llm_strict
from services.classify_intent import is_context_sufficient
from config.settings import db, async_db, memory
from sqlalchemy import text
# from pgvector import Vector as PgVector
from sqlalchemy import text, bindparam
from pgvector.sqlalchemy import Vector
import time
from services.memory.mem0_memory import Mem0MemoryManager
import uuid






router = APIRouter()

model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

# pg = psycopg2.connect(
#     host=os.getenv("PG_HOST", "db"),
#     user=os.getenv("PG_USER", "tabot"),
#     password=os.getenv("PG_PASS", "hello"),
#     dbname=os.getenv("PG_DB", "agent_memory")
# )
# pg.autocommit = True

SIMILARITY_THRESHOLD = 0.40  # strict mode cutoff
SIMILARITY_WEAK_THRESHOLD = 0.28


class RAGQueryRequest(BaseModel):
    businessId: int
    userId: str
    question: str

mem0_memory = Mem0MemoryManager()

@router.post("/rag/query")
async def rag_query(payload: RAGQueryRequest):
    query = payload.question
    business_id = payload.businessId
    user_id = payload.userId

    print(f"Received query: {query}")

    log_info(f"USER_QUESTION: {query}")

    # Save question to mem0 memory
    try:
        memory_result = mem0_memory.mem0_add(
        user_id=user_id,
        namespace="business",
        messages=[{"role": "user", "content": query}],
        metadata={"ts": time.time()}
        )

        if memory_result is None:
            log_error("Memory add failed.")
        else:
            log_info(f"Memory add succeeded: {query}")
            print(memory_result)

    except Exception as e:
        log_error(f"Failed to save user question to memory: {e}")


    # Get past messages for context
    past_messages = await memory.read(user_id=user_id)
    formatted_history = format_exchanges(past_messages)
    print(f"Past messages for user {user_id}: {formatted_history}")

    # Get info from pdf
    retrieved = await get_info_from_pdf(query, business_id, top_k=5)

    if not retrieved:
        return {
            "short_answer": "I don't have information about that.",
            "key_points": [],
            "important_warnings": []
        }

    best = retrieved[0]

    # Complete miss — don't even try
    if best["similarity"] < SIMILARITY_WEAK_THRESHOLD:
       return {
            "short_answer": "I don't have information about that.",
            "key_points": [],
            "important_warnings": []
        }

    # Filter by similarity threshold
    good_chunks = [r for r in retrieved if r["similarity"] >= SIMILARITY_WEAK_THRESHOLD]

    pdf_context = "\n\n".join(r["text"] for r in good_chunks)

    # Strong match — skip judge, answer directly
    if best["similarity"] >= SIMILARITY_THRESHOLD:
        log_info("Strong match — answering directly.")
        answer = generate_strict_answer(query, pdf_context, formatted_history)

        print("Generated answer for strong match:", answer)

        await memory.write(
        user_id=user_id,
        key=f"conv:{uuid.uuid4()}",
        value={
            "user_message": query,
            "agent_response": answer
        },
        summary=f"User asked: {query[:100]}"
        )

        return {
            "answer": answer,
            "similarity": best["similarity"]
        }

    # 4. Judge whether context is sufficient
    # Weak match — ask judge if we need more context
    log_info("Weak match — running context judge.")
    judge_result = is_context_sufficient(
        question=query,
        context=pdf_context,
        past_messages=formatted_history
    )

    final_context = pdf_context

    # 5. If not sufficient, search memory and inject
    if not judge_result["context_sufficient"]:
        search_query = judge_result.get("search_query", query)
        log_info(f"Context insufficient — searching memory with: {search_query}")

        memory_results = await memory.search(
            user_id=user_id,
            query=search_query,
            limit=5
        )

        if memory_results:
            memory_text = "\n\n".join(
                item["text"] for item in memory_results
            )
            # THIS is where you inject — always, not just in the else block
            final_context = f"{pdf_context}\n\n--- Relevant Past Exchanges ---\n\n{memory_text}"
            log_info(f"Memory search injected into context.")
        else:
            log_info("Memory search returned no results.")


    if not final_context.strip():
        return {"answer": "I don’t have information about that."}
    

    answer = generate_strict_answer(query, final_context, formatted_history)

    #  Persist the full exchange (user message + agent answer)
    await memory.write(
        user_id=user_id,
        key=f"conv:{uuid.uuid4()}",
        value={
            "user_message": query,
            "agent_response": answer
        },
        summary=f"User asked: {query[:100]}"
    )

    return {
        "answer": answer,
        "similarity": best["similarity"]
    }


def generate_strict_answer(question: str, context: str, past_messages: Any) -> str:
    """
    Produce an answer strictly from the context (no hallucinations).
    """
    # Hard constraint: AI cannot invent content
    if len(context.strip()) == 0:
        return {
            "short_answer": "I don't have information about that.",
            "key_points": [],
            "important_warnings": []
        }

    prompt = f"""
You are a helpful assistant that explains documents clearly to users.

Rules:
- Use ONLY the information from the document
- DO NOT invent new facts
- BUT you MUST explain and simplify the answer in a human-friendly way
- If the text is complex (e.g. legal), summarize it clearly
- Answer the user's question directly
- Avoid copying large chunks of text
- You must read the information and understand it to answer well
- If the answer is not found in the context, set short_answer to "I don't have information about that." and leave key_points and important_warnings empty

---

DOCUMENT TEXT:
{context}

---

PAST MESSAGES:
{past_messages}

---

USER QUESTION:
{question}

---
────────────────────────────────────────
OUTPUT FORMAT (STRICT)
────────────────────────────────────────
You MUST respond with ONLY valid JSON.
No markdown. No explanations. No preamble. No code fences.

Schema:
{{
  "short_answer": "<1-2 sentence direct answer to the question>",
  "key_points": ["<point 1>", "<point 2>", "<point 3>"],
  "important_warnings": ["<warning 1>", "<warning 2>"]
}}

- short_answer: direct, plain English answer in 1-2 sentences
- key_points: list of 2-5 specific facts from the document relevant to the question
- important_warnings: list of penalties, deadlines, or consequences the user must know. Empty list [] if none.

IMPORTANT: important_warnings must NEVER be empty if the context mentions penalties, fees, interest rates, or legal consequences.

Now give a CLEAR and HUMAN-FRIENDLY and Respond with ONLY the JSON object. Nothing else.
"""

    # this uses your orchestrator’s LLM call
    raw = call_llm_strict(prompt)

    # print("Raw call_llm_strict output:", raw)

    # Strip markdown fences if model adds them
    # raw = raw.strip().replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)

        print("Raw call_llm_strict output:", parsed)

        return parsed
    except Exception as e:
        log_error(f"Failed to parse answer JSON: {raw} | {e}")
        return {
            "short_answer": raw,
            "key_points": [],
            "important_warnings": []
        }

async def get_info_from_pdf(query: str, business_id: int, top_k: int = 5) -> dict:
    query_vec = model.encode([query], normalize_embeddings=True)[0]
    
    # Convert to postgres vector literal — bypasses codec entirely
    vec_str = "[" + ",".join(str(x) for x in query_vec.tolist()) + "]"

    async with memory.async_session() as session:
        stmt = text("""
            SELECT 
                text,
                1 - (embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM document_chunks
            WHERE business_id = :business_id
            ORDER BY embedding <=> CAST(:query_vec AS vector)
            LIMIT :top_k
        """)

        result = await session.execute(
            stmt,
            {
                "query_vec": vec_str,   # plain string, postgres casts it
                "business_id": business_id,
                "top_k": top_k
            }
        )
        rows = result.fetchall()

    return [
        {"text": r.text, "similarity": float(r.similarity)}
        for r in rows
    ]


def format_exchanges(exchanges: list) -> str:
    """Format DB memory rows into readable conversation history."""
    if not exchanges:
        return "No previous conversation history."
    
    lines = []
    for ex in reversed(exchanges):  # oldest first
        val = ex.get("value", {})
        user_msg = val.get("user_message", "")
        agent_msg = val.get("agent_response", "")
        if user_msg and agent_msg:
            lines.append(f"User: {user_msg}\nAgent: {agent_msg}")
    
    return "\n\n".join(lines) if lines else "No previous conversation history."