"""
config.py — Central configuration for LUMEN.
All constants, model names, paths and tuneable settings live here.
"""
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
UI_DIR     = BASE_DIR / "ui"
ASSETS_DIR = UI_DIR / "assets"
CSS_PATH   = ASSETS_DIR / "style.css"
HTML_PATH  = ASSETS_DIR / "welcome.html"
DB_PATH    = BASE_DIR / "chatbot.db"
MCP_PATH   = BASE_DIR / "tools" / "stock_mcp.py"

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
