# scripts/test_memory.py
import asyncio
import os
from dotenv import load_dotenv
from services.memory import MemoryService

load_dotenv()

async def main():
    db = os.environ.get("DATABASE_URL")
    mem = MemoryService(db_url=db)
    await mem.init_db()
    # user_id = "a4d474d4-a7a5-4495-a597-85b9647306fe"
    user_id = "customer_5"
    # print("writing memory...")
    # res = await mem.write(user_id, "least_preferred_sport", {"sport": "Cricket"}, summary="my least favorite sport is Cricket")
    # print("write result:", res)
    # print("reading memory...")
    # print("reading last 10 memories...")
    # recent = await mem.read(user_id)
    # for item in recent:
    #     print(item)

    # r = await mem.read(user_id, "preferred_language")
    # print("read:", r)
    print("searching for 'favorite sport'...")
    found = await mem.search(user_id, "which sport do i like")
    print("search:", found)
    # deleted = await mem.delete(user_id, "preferred_language")
    # print("deleted:", deleted)

asyncio.run(main())
