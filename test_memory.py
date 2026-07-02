# scripts/test_memory.py
import asyncio
import os
import asyncpg
from dotenv import load_dotenv
from pydantic import BaseModel
from services.memory.mem0_memory import Mem0MemoryManager
# from services.memory.working_memory import WorkingMemory
from services.classify_intent import classify_intent

from config.settings import db, async_db
from services.memory.db_memory import MemoryService
from typing import Any, Dict, List, Optional
from services.RAG.rag_query import rag_query

load_dotenv()

# working_mem = WorkingMemory()  

memory = MemoryService(db_url="postgresql+asyncpg://tabot:hello@localhost:5432/agent_memory")

mem0_memory = Mem0MemoryManager()

class RAGQueryRequest(BaseModel):
    businessId: int
    userId: str
    question: str

# async def init_services():
#     await memory.init_vector_db()


# services/memory/mem0_memory.py

# def add_conversation_turn(self, user_id: str, user_msg: str, agent_response: str, metadata: Optional[Dict[str, str]] = None):
#     if not self.mem0:
#         return None
    
#     # We create a conversation payload
#     messages = [
#         {"role": "user", "content": user_msg},
#         {"role": "assistant", "content": agent_response}
#     ]
    
#     try:
#         # metadata is great for your analytics requirement!
#         return self.mem0.add(
#             messages, 
#             user_id=user_id,
#             metadata={
#                 "type": "conversation_turn",
#                 "agent_id": "sales-support-v1"
#             }
#         )
#     except Exception as e:
#         print(f"Error adding to Mem0: {e}")
#         return None



async def main():
    # result = mem0_memory.add_conversation_turn(
    #     user_id="user007",
    #     user_msg="Hello, who is the best footballer?",
    #     agent_response="Hi! LIonel Messi is often considered the best footballer in the world due to his incredible skill, vision, and goal-scoring ability. However, opinions on this can vary, and some may argue that players like Cristiano Ronaldo also deserve the title."
    # )

    # result = await memory.write(
    #     user_id="user007",
    #     key="test_key_124",
    #     value={"user_query": "I am starting a new project. I need tool recommendations.", "retrieved_info": "tools: Next js, React, Vue, VsCode, Xampp, Docker", "final_answer": "i recommend using tools like Next js for frontend, VsCode for development, and Docker for containerization."}
    # )

    # result = await memory.search(user_id="user007", query="what is vs code used for?")
    result = await rag_query(payload=RAGQueryRequest(businessId=1, userId="user007", question="What happens if i am unable to complete payment of a good????"))

    print("result:", result)


asyncio.run(main())
