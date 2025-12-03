# orchestrator/routes/rag_query.py

from fastapi import APIRouter, Form
import psycopg2
import os
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from config.strict_llm import call_llm_strict

router = APIRouter()

model = SentenceTransformer("all-MiniLM-L6-v2")

pg = psycopg2.connect(
    host=os.getenv("PG_HOST", "localhost"),
    user=os.getenv("PG_USER", "tabot"),
    password=os.getenv("PG_PASS", "yourStrongP@ss"),
    dbname=os.getenv("PG_DB", "agent_memory")
)
pg.autocommit = True

SIMILARITY_THRESHOLD = 0.20  # strict mode cutoff


class RAGQueryRequest(BaseModel):
    businessId: int
    question: str


@router.post("/rag/query")
async def rag_query(payload: RAGQueryRequest):
    query = payload.question
    business_id = payload.businessId

    print(f"Received query: {query}")
    print(f"Business ID: {business_id}")


    # Step 1: Embed query
    query_vec = model.encode([query])[0]
    print(f"Query embedding (first 10 dims): {query_vec[:10]}")

    cur = pg.cursor()
    cur.execute(
        """
        SELECT text,
        1 - (embedding <=> %s::vector) AS similarity
        FROM document_chunks
        WHERE business_id = %s
        ORDER BY embedding <=> %s::vector
        LIMIT 5
        """,
        (query_vec.tolist(), business_id, query_vec.tolist())
    )

    results = cur.fetchall()
    print(f"Raw DB results: {results}")


    if not results:
        return {"answer": "I don’t have information about that."}

    # Get best match
    best_text, best_similarity = results[0]

    # Step 2: Strict check — reject if similarity is too low
    if float(best_similarity) < SIMILARITY_THRESHOLD:
        return {"answer": "I don’t have information about that."}

    # Step 3: Build final response strictly from chunks
    combined_context = " ".join([r[0] for r in results])

    answer = generate_strict_answer(query, combined_context)

    return {
        "answer": answer,
        "similarity": best_similarity
    }


def generate_strict_answer(question: str, context: str) -> str:
    """
    Produce an answer strictly from the context (no hallucinations).
    If information is insufficient, return 'not found'.
    """
    # Hard constraint: AI cannot invent content
    if len(context.strip()) == 0:
        return "I don’t have information about that."

    prompt = f"""
You are a STRICT document-based assistant.

Answer the question ONLY using the text below.
If the answer is not directly found in the text, reply:
"I don’t have information about that."

---
DOCUMENT TEXT:
{context}
---
QUESTION:
{question}

Answer using ONLY the document text:
"""

    # this uses your orchestrator’s LLM call
    return call_llm_strict(prompt)


