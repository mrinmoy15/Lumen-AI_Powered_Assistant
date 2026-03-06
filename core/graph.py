"""core/graph.py — Builds and compiles the LangGraph chatbot graph."""
import asyncio
import threading
from functools import partial

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import LLM_MODEL, LLM_TEMPERATURE, EMBEDDING_MODEL, MCP_PATH
from core.state import ChatState
from core.nodes import chat_node
from core.checkpointer import create_checkpointer
from tools.rag_tool import rag_tool
from tools.search_tool import search_tool


# ── Shared async event loop (runs in a background thread) ────
_ASYNC_LOOP   = asyncio.new_event_loop()
_ASYNC_THREAD = threading.Thread(target=_ASYNC_LOOP.run_forever, daemon=True)
_ASYNC_THREAD.start()


def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP).result()

def submit_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)


# ── Models ───────────────────────────────────────────────────
llm        = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)


# ── MCP tools ────────────────────────────────────────────────
async def _init_mcp_tools():
    client = MultiServerMCPClient({
        "stock": {
            "command": "python",
            "args": [str(MCP_PATH)],
            "transport": "stdio",
        }
    })
    return client, await client.get_tools()

mcp_client, mcp_tools = run_async(_init_mcp_tools())


# ── Tool list + LLM binding ───────────────────────────────────
tools          = [search_tool, rag_tool, *mcp_tools]
llm_with_tools = llm.bind_tools(tools)


# ── Graph ────────────────────────────────────────────────────
def build_graph(checkpointer):
    # Bind llm_with_tools into chat_node via partial so the graph node
    # signature stays compatible with LangGraph's (state, config) convention.
    bound_chat_node = partial(chat_node, llm_with_tools=llm_with_tools)

    tool_node = ToolNode(tools)
    graph     = StateGraph(ChatState)

    graph.add_node("chat_node", bound_chat_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")

    return graph.compile(checkpointer=checkpointer)


# ── Initialise checkpointer + compiled graph ─────────────────
checkpointer = run_async(create_checkpointer())
chatbot      = build_graph(checkpointer)
