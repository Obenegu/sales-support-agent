from app.logs.logging_helper import log_error, log_info
import fitz
from bs4 import BeautifulSoup
from fastapi import APIRouter, UploadFile, Form
from config.settings import db, async_db, memory
from sentence_transformers import SentenceTransformer
import uuid
import re
from services.memory.db_memory import document_chunks_table
import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector

async def init_services():
    await memory.init_vector_db()

model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")


async def ingest_document(
    file: UploadFile,
    businessId: int = Form(...)
):
    try:
        ext = file.filename.lower().split(".")[-1]
        raw_bytes = await file.read()

        if ext == "pdf":
            text = extract_pdf(raw_bytes)
        elif ext in ["html", "htm"]:
            text = extract_html(raw_bytes)
        else:
            text = raw_bytes.decode("utf-8", errors="ignore")

        # Normalize AFTER extraction but preserve sentence structure
        text = normalize_text(text)

        document_id = str(uuid.uuid4())

        # Fixed: chunk_size=200 words, overlap=30 words
        chunks = chunk_text(text=text, chunk_size=200, overlap=30)

        # Filter out empty or too-short chunks
        chunks = [c for c in chunks if len(c.split()) >= 15]

        log_info(f"Total chunks after filtering: {len(chunks)}")
        for i, c in enumerate(chunks):
            log_info(f"Chunk {i}: {c[:80]}...")  

        embeddings = model.encode(
            chunks,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True
        )

        await insert_chunks_to_db(
            document_id=document_id,
            business_id=businessId,
            filename=file.filename,
            file_type=ext,
            chunks=chunks,
            vectors=embeddings
        )

        log_info(f"Ingested {len(chunks)} chunks from {file.filename}")

        return {
            "message": "Ingestion complete",
            "document_id": document_id,
            "chunks": len(chunks)
        }

    except Exception as e:
        log_error(f"Ingestion failed: {e}")
        raise


def extract_pdf(raw_bytes: bytes) -> str:
    doc = fitz.open(stream=raw_bytes, filetype="pdf")
    pages = []
    for page in doc:
        pages.append(page.get_text())
    # Join pages with double newline to preserve page boundaries
    return "\n\n".join(pages)


def extract_html(raw_bytes: bytes) -> str:
    soup = BeautifulSoup(raw_bytes, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def normalize_text(text: str) -> str:
    # Preserve paragraph breaks (double newline)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Collapse spaces and tabs only
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 30) -> list[str]:
    """
    Section-aware chunker for legal/structured documents.
    Splits on Roman numeral sections first, then by size within each section.
    """
    # Split on Roman numeral headings like "I.", "II.", "III.", "IV." etc.
    section_pattern = r'(?=\b(?:I{1,3}|IV|VI{0,3}|IX|X{1,3}|XI)[\.\s])'
    sections = re.split(section_pattern, text)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        words = section.split()

        # Section fits in one chunk — keep it whole
        if len(words) <= chunk_size:
            chunks.append(section)
            continue

        # Section too long — split by sentence with overlap
        sentences = re.split(r'(?<=[.!?])\s+', section)
        current_words = []
        current_len = 0

        for sentence in sentences:
            s_words = sentence.split()
            s_len = len(s_words)

            if current_len + s_len > chunk_size and current_words:
                chunks.append(" ".join(current_words))
                # Keep overlap
                overlap_words = current_words[-overlap:] if overlap else []
                current_words = overlap_words + s_words
                current_len = len(current_words)
            else:
                current_words.extend(s_words)
                current_len += s_len

        if current_words:
            chunks.append(" ".join(current_words))

    return chunks


async def insert_chunks_to_db(
    document_id, business_id, filename,
    file_type, chunks, vectors
):
    # Use raw asyncpg — bypasses all SQLAlchemy type handling issues
    asyncpg_url = memory.db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(asyncpg_url)
    await register_vector(conn)
    
    try:
        async with conn.transaction():
            for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                # Ensure clean float32 numpy array
                embedding = np.array(vector, dtype=np.float32)
                
                await conn.execute(
                    """
                    INSERT INTO document_chunks 
                        (document_id, business_id, filename, file_type, chunk_index, text, embedding, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                    """,
                    document_id,
                    business_id,
                    filename,
                    file_type,
                    i,
                    chunk,
                    embedding  # asyncpg + register_vector handles this natively
                )
        log_info(f"Committed {len(chunks)} chunks for document {document_id}")
    finally:
        await conn.close()



# async def insert_chunks_to_db(
#     document_id, business_id, filename,
#     file_type, chunks, vectors
# ):
#     """Insert all chunks in a single transaction."""
#     async with memory.async_session() as session:
#         for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
#             await session.execute(
#                 document_chunks_table.insert().values(
#                     business_id=business_id,
#                     document_id=document_id,
#                     file_type=file_type,
#                     filename=filename,
#                     chunk_index=i,
#                     text=chunk,
#                     embedding=vector.tolist()
#                 )
#             )
#         # Single commit for all chunks
#         await session.commit()
#         log_info(f"Committed {len(chunks)} chunks for document {document_id}")