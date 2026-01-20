from config.settings import db
from app.safety import sanitize_text, validate_input, logger
from services.memory.db_memory import MemoryService
from services.memory.working_memory import WorkingMemory


working_mem = WorkingMemory()


db_memory = MemoryService(db_url=db)

async def init_services():
    await db_memory.init_db()
    
async def orchestrate(user_id: str, session_id: str):

    final_prompt = None
    # context=""
    # -----------------------------------------------------------
    # 1. Input sanitization / validation
    # -----------------------------------------------------------
    # raw = sanitize_text(message)
    # ok, meta = validate_input(raw)

    # if not ok:
    #     logger.warning("Rejected user input: %s", meta)
    #     return "I’m sorry — I can’t help with that request. If this is a mistake, please rephrase."
    
    WorkingMemory = working_mem.loadWorkingMemory(session_id=session_id, user_id=user_id)
    if WorkingMemory:
        context = f"""Here is this user's working memory: {WorkingMemory}."""
        final_prompt = f"{context}"
    else:
        final_prompt = f"No working memory found"
    

    return final_prompt
