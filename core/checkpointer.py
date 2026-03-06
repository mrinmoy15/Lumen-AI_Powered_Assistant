"""core/checkpointer.py — Async SQLite checkpointer for LangGraph."""
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from config import DB_PATH


async def create_checkpointer() -> AsyncSqliteSaver:
    conn = await aiosqlite.connect(database=str(DB_PATH))
    return AsyncSqliteSaver(conn)
