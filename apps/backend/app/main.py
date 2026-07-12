import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from apps.backend.app.api.chat import router as chat_router
import uvicorn

load_dotenv()

app = FastAPI(
    title="Fumi AI Backend",
    description="FastAPI backend supporting local intelligence, memory, and tool execution.",
    version="0.1.0"
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
        "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo")
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=port, reload=True)
