# scripts/test_memory.py
import asyncio
import os
from dotenv import load_dotenv
from services.memory import MemoryService

load_dotenv()

async def main():
    db = os.environ.get("DATABASE_URL")
    # print(f"Memo Api key: {os.environ.get('MEM0_API_KEY')}")
    mem = MemoryService(db_url=db)
    await mem.init_db()

    # res = mem.mem0_add(
    # "user123",
    # "business",
    # messages=[{"role": "user", "content": "my favorite sport is football"}]
    # )

    result = mem.mem0_add(
    user_id="string",
    namespace="business",
    messages=[{"role": "user", "content": "I have a technical issue"}],
    metadata={"ts": "1733560000"},
)

    print(result)

    # print("write result:", res)

    # test mem0 add/search if mem0 configured
    # result = mem.mem0_search(user_id="user123", query="which sport do i like most", limit=5)
    # print("mem0 save result:", result)

asyncio.run(main())
