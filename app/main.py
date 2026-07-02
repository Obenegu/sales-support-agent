from fastapi import FastAPI, Request
from app.routes import router
from services.RAG.rag_query import router as rag_router
from contextlib import asynccontextmanager
from app.orchestrator import init_services
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await init_services()
    yield
    # Shutdown logic (optional)



app = FastAPI(
    title="Sales & Support AI Agent",
    version="1.0.0",
    description="AI agent for small businesses — sales and support automation",
    lifespan=lifespan

)

# ←←← ADD THIS BLOCK (Bug 2 fix) ←←←
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "hint": "Check that you're sending multipart/form-data with 'file' and 'businessId' fields "
                    "if you're uploading a document, or proper JSON for other endpoints."
        }
    )
# ←←← END OF FIX ←←←

@app.get("/")
async def health_check():
    return {"status": "ok", "service": "Sales & Support AI Agent"}

app.include_router(router)
app.include_router(rag_router)