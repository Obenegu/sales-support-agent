import pdfplumber
from sentence_transformers import SentenceTransformer
from config.settings import get_pg_pool
import nltk
nltk.download("punkt")
from nltk.tokenize import sent_tokenize

# Load embeddings model once
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def chunk_text(text: str, max_tokens=300):
    sentences = sent_tokenize(text)
    chunks = []
    current = ""

    for sent in sentences:
        if len((current + " " + sent).split()) <= max_tokens:
            current += " " + sent
        else:
            chunks.append(current.strip())
            current = sent

    if current:
        chunks.append(current.strip())

    return chunks


async def ingest_pdf(file_path: str, business_id: int):
    """
    Extract PDF text, chunk it, embed it, and store in DB.
    """
    pool = await get_pg_pool()

    # 1. Extract text
    with pdfplumber.open(file_path) as pdf:
        full_text = "\n".join([page.extract_text() or "" for page in pdf.pages])

    # 2. Chunk text
    chunks = chunk_text(full_text)

    # 3. Generate embeddings
    embeddings = embedder.encode(chunks).tolist()

    # 4. Store in database
    async with pool.acquire() as conn:
        for chunk, emb in zip(chunks, embeddings):
            await conn.execute(
                """
                INSERT INTO document_chunks (business_id, text, embedding, metadata)
                VALUES ($1, $2, $3, '{"source": "pdf"}')
                """,
                business_id,
                chunk,
                emb
            )

    return {
        "chunks": len(chunks),
        "status": "success"
    }
