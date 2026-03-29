"""backend/routers/chat.py — Server-Sent Events streaming chat endpoint."""
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

import core.graph as graph

router = APIRouter(prefix="/threads", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("/{thread_id}/chat")
async def stream_chat(thread_id: str, body: ChatRequest):
    """Stream the assistant reply as SSE chunks.

    Each event is:  data: <json-encoded string>\\n\\n
    Final event is: data: [DONE]\\n\\n
    """
    config = {
        "configurable": {"thread_id": thread_id},
        "metadata":     {"thread_id": thread_id},
        "run_name":     "chat_turn",
    }

    async def event_generator():
        async for chunk, meta in graph.chatbot.astream(
            {"messages": [HumanMessage(content=body.message)]},
            config=config,
            stream_mode="messages",
        ):
            if (
                chunk.content
                and not isinstance(chunk.content, list)
                and meta.get("langgraph_node") == "chat_node"
            ):
                yield f"data: {json.dumps(chunk.content)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
