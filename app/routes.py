from fastapi import APIRouter, Request
from pydantic import BaseModel
from services.ai_client import ai_chat
from services.ingest_pdf import ingest_document
from services.rag_query import rag_query
from fastapi import APIRouter, UploadFile, Form, File

router = APIRouter(prefix="/api")

class ChatRequest(BaseModel):
    userId: str
    message: str
    role: str

# class IngestRequest(BaseModel):
#     file: UploadFile = File(...),
#     businessId: int = Form(...)

class ChatResponse(BaseModel):
    response: str
    intent: str
    tool_used: str
    role: str

class RAGQueryRequest(BaseModel):
    businessId: int
    question: str
    

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    return await ai_chat(request.message, request.userId)

@router.post("/ingest")
async def ingest_endpoint(
    file: UploadFile = File(...),           # the PDF file
    businessId: int = Form(...),):

    return await ingest_document(file, businessId)

@router.post("/rag/query")
async def rag_query_endpoint(request: RAGQueryRequest):
    return await rag_query(request)
