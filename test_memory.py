# scripts/test_memory.py
import asyncio
import os
from dotenv import load_dotenv
from services.memory.mem0_memory import Mem0MemoryManager
from services.memory.working_memory import WorkingMemory
from services.classify_intent import classify_intent
import redis

load_dotenv()

working_mem = WorkingMemory()  

async def main():
    db = os.environ.get("DATABASE_URL")
    # print(f"Memo Api key: {os.environ.get('MEM0_API_KEY')}")
    mem = Mem0MemoryManager()
    # await mem.init_db()

    # res = mem.mem0_add(
    # "user123",
    # "business",
    # messages=[{"role": "user", "content": "my favorite sport is football"}]
    # )

    #result = mem.mem0_delete(user_id="simnon")

    #print(result)

    # r = redis.Redis(host="localhost", port=6379)
    # print(r.ping())

    # working_memory = working_mem.createWorkingMemory(user_id="user124", session_id="sess456")
    # print("Created Working Memory:", working_memory)

    # add_to_cart = working_mem.add_item_to_order( session_id="sess456", user_id="user123",
    #     item={"name": "Widget", "quantity": "2", "price": 19.99, "color": "red"}
    # )

    # print("After adding item to order:", add_to_cart)

    # working_mem.clear_working_memory(session_id="sess456", user_id="user123")

    # print("write result:", res)

    # test mem0 add/search if mem0 configured
    # result = mem.mem0_search(user_id="user123", query="which sport do i like most", limit=5)
    # print("mem0 save result:", result)

    # 1️⃣ Create memory FIRST
    # working_mem.createWorkingMemory(
    #     user_id="user123",
    #     session_id="sess456"
    # )

    # 2️⃣ Then add items
    # add_to_cart = working_mem.add_item_to_order( user_id="user123", session_id="sess456",
    #     item={
    #         "Name": "ruler",
    #         "Quantity": "2",
    #         "Price": 0.5,
    #         "Color": "blue"
    #     }
    # )

    # print("After adding item to order:", add_to_cart)

    # memory = mem.mem0_get_user("junior")
    # # print("Mem0 get user memories:", memory)

    # intent = classify_intent("what is my name", memory)
    # print("Intent:", intent)

    memory = working_mem.loadWorkingMemory( session_id="sess456", user_id="user123" )
    print("Loaded Working Memory:", memory)

    # removed_items = working_mem.remove_item_from_order(session_id="sess456", user_id="user123", item_name="ruler")
    # print("Current Items in Cart", removed_items)



asyncio.run(main())
