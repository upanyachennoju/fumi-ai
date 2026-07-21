import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from apps.backend.app.api.chat import router as chat_router
import uvicorn

# Import packages needed for background scheduler and check-ins
from packages.knowledge.vault import Vault
from packages.knowledge.index import VectorIndex
from packages.knowledge.retriever import Retriever
from packages.providers.factory import get_llm_provider
from packages.providers.ollama import OllamaEmbeddingProvider
from packages.tools.registry import ToolRegistry
from packages.tools.goals import ListGoalsTool
from packages.tools.memories import SearchMemoryTool
from packages.tools.checkins import CreateCheckinTool, ListPendingCheckinsTool, MarkCheckinReadTool
from packages.tools.reminders import CreateReminderTool, ListRemindersTool, UpdateReminderTool, DeleteReminderTool
from packages.schedulers.scheduler import FumiScheduler
from packages.schedulers.checkins import CheckInManager

load_dotenv()

# Setup dependencies
vault = Vault()
index = VectorIndex()
embedding_provider = OllamaEmbeddingProvider()
retriever = Retriever(index, embedding_provider)
llm_provider = get_llm_provider()

# Build ToolRegistry and register tools
registry = ToolRegistry()
registry.register(ListGoalsTool(vault))
registry.register(SearchMemoryTool(retriever))
registry.register(CreateCheckinTool(vault))
registry.register(ListPendingCheckinsTool(vault))
registry.register(MarkCheckinReadTool(vault))
registry.register(CreateReminderTool(vault))
registry.register(ListRemindersTool(vault))
registry.register(UpdateReminderTool(vault))
registry.register(DeleteReminderTool(vault))

# Initialize components
scheduler = FumiScheduler(registry=registry, llm_provider=llm_provider)
checkin_manager = CheckInManager(vault)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start scheduler (Daily check-in every 24h, reminders check every 10s)
    scheduler.start(daily_interval_hours=24.0, reminder_interval_seconds=10.0)
    yield
    # Shutdown: Stop scheduler
    scheduler.shutdown()


app = FastAPI(
    title="Fumi AI Backend",
    description="FastAPI backend supporting local intelligence, memory, and tool execution.",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(chat_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://127.0.0.1:1420",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Fumi AI Backend",
        "version": "0.1.0"
    }


@app.get("/config")
def get_config():
    return {
        "chroma_db_path": os.getenv("CHROMA_DB_PATH", "./chroma"),
        "vault_path": os.getenv("VAULT_PATH", "./vault"),
        "llm_provider": os.getenv("llm_provider", "ollama"),
        "llm_model": os.getenv("llm_model", "qwen2.5:7b-instruct"),
        "llm_embed": os.getenv("llm_embed", "nomic-embed-text")
    }


@app.get("/checkins/pending")
def get_pending_checkins():
    """
    Get all pending (unread) check-in messages.
    """
    return checkin_manager.get_pending_checkins()


@app.post("/checkins/{checkin_id}/read")
def mark_checkin_read(checkin_id: str):
    """
    Mark a check-in message as read.
    """
    success = checkin_manager.mark_as_read(checkin_id)
    return {"id": checkin_id, "success": success}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=port, reload=True)
