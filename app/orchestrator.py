from config.settings import db
from app.safety import sanitize_text, validate_input, logger
from services.memory.db_memory import MemoryService



db_memory = MemoryService(db_url=db)

async def init_services():
    await db_memory.init_db()
    
async def orchestrate(message: str, user_id: str):

    final_prompt = None
    # context=""
    # -----------------------------------------------------------
    # 1. Input sanitization / validation
    # -----------------------------------------------------------
    raw = sanitize_text(message)
    ok, meta = validate_input(raw)

    if not ok:
        logger.warning("Rejected user input: %s", meta)
        return "I’m sorry — I can’t help with that request. If this is a mistake, please rephrase."

    final_prompt = message
    

    return final_prompt
