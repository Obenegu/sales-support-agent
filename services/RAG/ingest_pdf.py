from app.logs.logging_helper import log_error, log_info
import io
import fitz  # PyMuPDF pymupdf
from bs4 import BeautifulSoup
from fastapi import APIRouter, UploadFile, Form
import psycopg2
import os
from config.settings import db
from sentence_transformers import SentenceTransformer
from services.memory.db_memory import MemoryService

memory = MemoryService(db_url=db)

async def init_services():
    await memory.init_vector_db()

# Load embedding model (MiniLM or bge-small)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to Postgres
pg = psycopg2.connect(
    host=os.getenv("PG_HOST", "localhost"),
    user=os.getenv("PG_USER", "tabot"),
    password=os.getenv("PG_PASS", "yourStrongP@ss"),
    dbname=os.getenv("PG_DB", "agent_memory")
)
pg.autocommit = True

async def ingest_document(
    file: UploadFile,
    businessId: int = Form(...)
):
    ext = file.filename.lower().split(".")[-1]

    raw_bytes = await file.read()

    if ext == "pdf":
        text = extract_pdf(raw_bytes)
    elif ext in ["html", "htm"]:
        text = extract_html(raw_bytes)
    else:
        text = raw_bytes.decode("utf-8", errors="ignore")

    # Chunk the text
    chunks = chunk_text(text, chunk_size=500)

    # Embed each chunk
    embeddings = model.encode(chunks)

    # Store in pgvector DB
    insert_chunks_to_db(
        business_id=businessId,
        filename=file.filename,
        chunks=chunks,
        vectors=embeddings
    )

    return {"message": "Ingestion complete", "chunks": len(chunks)}



def extract_pdf(raw_bytes: bytes) -> str:
    doc = fitz.open(stream=raw_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def extract_html(raw_bytes: bytes) -> str:
    soup = BeautifulSoup(raw_bytes, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def insert_chunks_to_db(business_id, filename, chunks, vectors):
    cur = pg.cursor()

    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        cur.execute(
            """
            INSERT INTO document_chunks 
            (business_id, filename, chunk_index, text, embedding)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (business_id, filename, i, chunk, vector.tolist())
        )

    