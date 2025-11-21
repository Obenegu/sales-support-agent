from fastapi import FastAPI
from app.routes import router
from contextlib import asynccontextmanager
from app.orchestrator import init_services


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

app.get("/")

app.include_router(router)