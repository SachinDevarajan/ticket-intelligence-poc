from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.ticket_router import router as ticket_router
from app.core.config import settings
from app.db.session import Base, engine
from app.models.ticket import TicketAnalysis  # noqa: F401 - registers model metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="LLM-powered ticket analysis POC using Groq or Ollama.",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "ticket-intelligence-api", "provider": settings.llm_provider}


app.include_router(ticket_router, prefix=settings.api_v1_prefix)
