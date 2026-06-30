"""api/main.py - LUMEN FastAPI application.

Run with (from backend/ directory):
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import threads, chat, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise DB, graph, checkpointer, MCP tools."""
    from db.database_utils import initialize_thread_tracker, cleanup_old_threads
    from core.graph import init_graph
    from config import THREAD_CLEANUP_DAYS

    initialize_thread_tracker()
    cleanup_old_threads(days=THREAD_CLEANUP_DAYS)
    await init_graph()

    yield


app = FastAPI(title="LUMEN API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(threads.router)
app.include_router(chat.router)
app.include_router(documents.router)
