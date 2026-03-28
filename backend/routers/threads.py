"""backend/routers/threads.py — Thread CRUD + message history endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

import core.graph as graph
from db.database_utils import delete_thread, _get_conn

router = APIRouter(prefix="/threads", tags=["threads"])


class ThreadCreate(BaseModel):
    thread_id: str
    label: str


@router.get("")
async def list_threads() -> list[dict]:
    """Return all threads with their opening message as the label."""
    seen, threads = set(), []
    async for checkpoint in graph.checkpointer.alist(None):
        tid = checkpoint.config["configurable"]["thread_id"]
        if tid in seen:
            continue
        seen.add(tid)
        messages = checkpoint.checkpoint.get("channel_values", {}).get("messages", [])
        first_human = next(
            (
                m.content[:40] + ("..." if len(m.content) > 40 else "")
                for m in messages
                if isinstance(m, HumanMessage)
            ),
            None,
        )
        if first_human:
            threads.append({"thread_id": tid, "label": first_human})
    return threads


@router.post("")
def register_thread(body: ThreadCreate):
    """Register a new thread in the thread_tracker table."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO thread_tracker (thread_id) VALUES (%s) ON CONFLICT DO NOTHING",
                (body.thread_id,),
            )
        conn.commit()
    return {"thread_id": body.thread_id}


@router.delete("/{thread_id}")
def remove_thread(thread_id: str):
    """Delete a thread and all its checkpoint data."""
    delete_thread(thread_id)
    return {"deleted": True}


@router.get("/{thread_id}/messages")
async def get_messages(thread_id: str) -> list[dict]:
    """Return the conversation history for a thread as role/content dicts."""
    state = await graph.chatbot.aget_state(
        config={"configurable": {"thread_id": thread_id}}
    )
    messages = state.values.get("messages", [])
    result = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        if isinstance(msg.content, str) and msg.content.strip():
            result.append({"role": role, "content": msg.content})
    return result
