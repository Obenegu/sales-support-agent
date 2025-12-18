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

    # Try RAG retrieval first (if relevant docs exist)
    # retrieved = await search_chunks(message, business_id=1, limit=4)

    # if retrieved:
    #     top_texts = [r["text"] for r in retrieved]

    #     rag_prompt = build_rag_prompt(message, top_texts)

    #     return {
    #         "type": "rag_query",
    #         "prompt": rag_prompt,
    #         "chunks_used": len(top_texts)
    #     }

    #Memory from PDF File
    # pdf_info = get_info_from_pdf(message, business_id=0)
    # if "answer" in pdf_info:
    #     file_context = pdf_info["answer"]
    #     return file_context
    # print(f"PDF info: {pdf_info}")
    # file_context = pdf_info["combined_context"]

    # -----------------------------------------------------------
    # 2. Intent detection
    # -----------------------------------------------------------
    # intent = classify_intent(message)

    # # -----------------------------------------------------------
    # # 3. Fetch memory relevant to this message
    # # -----------------------------------------------------------
    # memory_context = ""
    # relevant_memories = memory.mem0_search(user_id=user_id, query=message, limit=10)
    # print(f"user_id: {user_id}")

    # if relevant_memories and "results" in relevant_memories:
    #     print(f"Found {len(relevant_memories['results'])} relevant memories for user {user_id}")
    #     memory_context = "Relevant past context about the user:\n"
    #     for i, m in enumerate(relevant_memories["results"], 1):
    #         text = m.get("memory") or m.get("text") or str(m.get("value", ""))
    #         score = m.get("score", 0)
    #         memory_context += f"{i}. {text.strip()} (relevance: {score:.2f})\n"

    # else:
    #     print(f"No relevant memories found for user {user_id}, falling back to recent ones...")
    #     recent = await memory.read(user_id=user_id, limit=10)
    #     if recent:
    #         for m in recent:
    #             memory_context += f"- {m['key']}: {m['summary'] or m['value']}\n"
    #             print(f"Last_memory: {memory_context}")

    
    

    # # -----------------------------------------------------------
    # # 4. Objection detection (highest priority)
    # # -----------------------------------------------------------
    # objection = classify_objection(message)
    # if (
    #     objection
    #     and objection["confidence"] >= 0.6
    #     and objection["objection_type"] != "other"
    # ):
    #     # Objection-handling mode → return special prompt
    #     return (
    #         f"[objection_detected]\n"
    #         f"type: {objection['objection_type']}\n"
    #         f"confidence: {objection['confidence']}\n\n"
    #         f"User message: {message}\n\n"
    #         "You are now in `objection_handling` mode: respond using empathy, "
    #         "validate the objection, then apply the correct strategy "
    #         "(reframe value, give proof, propose cheaper options, ask clarifying questions), "
    #         "and end with a soft CTA.\n"
    #     )

    # # -----------------------------------------------------------
    # # 5. Intent-based behavioral context
    # # -----------------------------------------------------------
    # if intent == "sales":
    #     context = (
    #         "You are a professional sales agent for a small business.\n"
    #         "Your job is to persuade customers, answer pricing questions, "
    #         "Keep answers short and friendly.\n"
    #         "If a customer says 'a' or 'an', infer a quantity of 1.\n"
    #         "Important: If the product the customer asks for is not in the list, say we do not have that product.\n"
    #         "Important: if a user asks about a product we don't have you should tell him/her we dont have such products.\n"
    #     )

    # elif intent == "support":
    #     context = (
    #         "You are a friendly technical support assistant.\n"
    #         "Your job is to diagnose issues, give step-by-step help, "
    #         "explain things simply, and solve the customer's problem.\n"
    #     )
    #      # Use support diagnosis engine
    #     support_check = classify_support_issue(message)

    #     if support_check["is_issue"] and support_check["confidence"] >= 0.7:

    #         # category = support_check["category"]
    #         # support_reply = diagnose_support_issue(message)
    #         # final_prompt = format_support_template(support_reply)
    #         support_reply = diagnose_support_issue(message)
    #         return support_reply
        
    
    # else:
    #     context = (
    #         "You are a helpful assistant for a small business.\n"
    #         "Give clear and friendly responses.\n"
    #     )

    # # -----------------------------------------------------------
    # # 6. Hard-coded detection for quote/price inquiries
    # # -----------------------------------------------------------
    # lowered = message.lower()

    # if any(word in lowered for word in ["quote", "quotation", "price"]):

    #     # Try extracting product
    #     product = None
    #     for p in PRODUCTS.keys():
    #         if p.lower() in lowered:
    #             product = p
    #             break

    #     if product:
    #         return sales_tool.generate_quote("Customer", product, 1)

    # # -----------------------------------------------------------
    # # 7. Build the final orchestration prompt for the LLM
    # # -----------------------------------------------------------

    # final_prompt = f"""
    #     {context}
    #     {memory_context}

    #     Customer message: "{message}"

    #     You MUST output ONLY valid JSON. Do NOT wrap in markdown or codeblocks.
    #     The `content` field must contain ONLY plain text (no JSON inside it).

    #     Format:
    #     {{
    #     "response": "<plain text reply here>",
    #     "intent": "{intent}",
    #     "tool_used": "<tool name or none>"
    #     "role": "assistant"
    #     }}
    #     """


    # print(f"The intent: {intent}")
    # print(f"final_prompt: {memory_context}")

    final_prompt = message
    

    return final_prompt
