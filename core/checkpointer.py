"""core/checkpointer.py — Async PostgreSQL checkpointer for LangGraph."""
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from config import DATABASE_URL

_pool: AsyncConnectionPool | None = None


async def create_checkpointer() -> AsyncPostgresSaver:
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=DATABASE_URL,
            max_size=20,
            kwargs={"autocommit": True, "prepare_threshold": 0},
            open=False,
        )
        await _pool.open()
    checkpointer = AsyncPostgresSaver(_pool)
    await checkpointer.setup()   # creates tables on first run
    return checkpointer
