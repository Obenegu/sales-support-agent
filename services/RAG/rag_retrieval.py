import numpy as np
from sentence_transformers import SentenceTransformer
from config.settings import get_pg_pool

embedder = SentenceTransformer("all-MiniLM-L6-v2")

async def search_chunks(query: str, business_id: int, limit: int = 5):
    """
    Embed the query, perform vector similarity search, return top chunks.
    """
    pool = await get_pg_pool()

    # Embed user query
    query_vec = embedder.encode([query])[0].tolist()

    # CRITICAL FIX: Ensure business_id is int!
    # business_id = int(business_id)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, text, embedding,
                   (embedding <-> $1::vector) AS distance
            FROM document_chunks
            WHERE business_id = $2
            ORDER BY embedding <-> $1::vector
            LIMIT $3;
            """,
            query_vec,
            business_id,
            limit
        )

    # Convert to plain dict
    return [
        {
            "id": r["id"],
            "text": r["text"],
            "distance": float(r["distance"]),
        }
        for r in rows
    ]


def build_rag_prompt(query: str, chunks: list[str]) -> str:
    """
    Create a final message prompt including relevant context.
    """
    context = "\n\n---\n\n".join(chunks)

    return f"""
You are an AI assistant. Use the document context below to answer the user's question.
Only answer from the context. If the context does not contain the answer, say so.

### DOCUMENT CONTEXT:
{context}

### USER QUESTION:
{query}

### FINAL ANSWER:
"""
