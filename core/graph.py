"""core/graph.py — LangGraph chatbot graph builder.

Module-level:  sync objects (llm, embeddings) created immediately.
Runtime:       call ``await init_graph()`` once from FastAPI lifespan to
               populate ``chatbot`` and ``checkpointer`` before handling requests.
"""
import sys
from functools import partial

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import LLM_MODEL, LLM_TEMPERATURE, EMBEDDING_MODEL, MCP_PATH
from core.state import ChatState
from core.nodes import chat_node
from core.checkpointer import create_checkpointer
from tools.rag_tool import rag_tool
from tools.search_tool import search_tool
from rag.store import init_store


# ── Sync models (created at import time) ─────────────────────
llm        = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
init_store(embeddings)   # wire embeddings into the PGVector retriever store


# ── Populated by init_graph() — None until then ───────────────
chatbot      = None
checkpointer = None
_mcp_client  = None


# ── Async MCP initialiser ─────────────────────────────────────
async def _init_mcp_tools():
    try:
        client = MultiServerMCPClient({
            "stock": {
                "command": sys.executable,   # always the current Python interpreter
                "args":    [str(MCP_PATH)],
                "transport": "stdio",
            }
        })
        return client, await client.get_tools()
    except Exception as e:
        print(f"[WARN] MCP stock tool failed to initialize: {e}. Stock prices will be unavailable.")
        return None, []


# ── Graph compiler ────────────────────────────────────────────
def _compile_graph(checkpointer_obj, all_tools):
    llm_with_tools  = llm.bind_tools(all_tools)
    bound_chat_node = partial(chat_node, llm_with_tools=llm_with_tools)
    tool_node       = ToolNode(all_tools)

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", bound_chat_node)
    graph.add_node("tools",     tool_node)
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")

    return graph.compile(checkpointer=checkpointer_obj)


# ── Public async init (called from FastAPI lifespan) ──────────
async def init_graph():
    """Initialise checkpointer, MCP tools, and compiled chatbot graph.

    Must be awaited before any graph operations are performed.
    FastAPI's lifespan handler is the right place to call this.
    """
    global chatbot, checkpointer, _mcp_client

    checkpointer_obj       = await create_checkpointer()
    _mcp_client, mcp_tools = await _init_mcp_tools()
    all_tools              = [search_tool, rag_tool, *mcp_tools]

    chatbot      = _compile_graph(checkpointer_obj, all_tools)
    checkpointer = checkpointer_obj
