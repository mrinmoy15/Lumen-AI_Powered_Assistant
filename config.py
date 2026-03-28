"""
config.py — Central configuration for LUMEN.
All constants, model names, paths and tuneable settings live here.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
UI_DIR     = BASE_DIR / "ui"
ASSETS_DIR = UI_DIR / "assets"
CSS_PATH   = ASSETS_DIR / "style.css"
HTML_PATH  = ASSETS_DIR / "welcome.html"
MCP_PATH   = BASE_DIR / "tools" / "stock_mcp.py"

# ── Backend API ──────────────────────────────────────────────
# Frontend uses this to reach the FastAPI backend.
# Local dev: http://localhost:8000  |  Cloud Run: full service URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── Database (conversation persistence) ──────────────────────
# Format: postgresql://user:password@host:5432/dbname
# Local dev:  postgresql://postgres:password@localhost:5432/lumen
# Cloud SQL:  postgresql://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
DATABASE_URL = os.getenv("DATABASE_URL")

# ── Pinecone (vector store for RAG) ──────────────────────────
# PINECONE_API_KEY is read directly from env by langchain-pinecone.
# Create an index in the Pinecone console (dimensions=1536, metric=cosine).
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "lumen-rag")

# ── LLM ─────────────────────────────────────────────────────
LLM_MODEL         = "gpt-4o"
LLM_TEMPERATURE   = 0.7
EMBEDDING_MODEL   = "text-embedding-3-small"

# ── RAG ─────────────────────────────────────────────────────
CHUNK_SIZE        = 1000
CHUNK_OVERLAP     = 200
RETRIEVER_K       = 4

# ── UI ───────────────────────────────────────────────────────
MAX_SIDEBAR_THREADS  = 10
THREAD_CLEANUP_DAYS  = 7
