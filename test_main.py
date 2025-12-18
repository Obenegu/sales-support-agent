# test_ai_chat.py
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from app.routes import ai_chat  # replace with your actual module path

app = FastAPI()

class TestRequest(BaseModel):
    user_id: str
    message: str

class TestResponse(BaseModel):
    response: str
    intent: str
    tool_used: str
    role: str

# -------------------------------------------------------
# Simple async test function
# -------------------------------------------------------
async def run_test():
    test_user_id = "user_123"
    test_message = "My order from yesterday still hasn’t arrived"

    print(f"Sending message: {test_message}")

    result = await ai_chat(test_message, test_user_id)
    print("Agent response:")
    print(result)

# -------------------------------------------------------
# If run directly, execute test
# -------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(run_test())
