from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
import os

app = FastAPI()

# Gemini Client
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

class ChatRequest(BaseModel):
    userId: str
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[request.message]
    )
    return ChatResponse(reply=response.text)
