"""core/nodes.py — LangGraph node functions."""
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from rag.store import get_retriever, THREAD_METADATA
from core.state import ChatState


async def chat_node(state: ChatState, config: RunnableConfig, llm_with_tools):
    """
    Main LLM node. Prepends a base system message and, if a document is
    loaded for this thread, a RAG-specific instruction.
    """
    messages = state["messages"]

    try:
        thread_id = str(config["configurable"]["thread_id"])
    except (KeyError, TypeError):
        thread_id = None

    # Base system message — always present
    system_messages = [SystemMessage(content=(
        "You are LUMEN, a helpful and knowledgeable assistant. "
        "Always respond in clear, well-formatted prose. "
        "Use markdown for structure (headers, bullets, bold) where helpful. "
        "For mathematical expressions, always use LaTeX delimiters: "
        "inline math as $...$ and block math as $$...$$. "
        "Never output raw JSON, Python dicts, or tool result structures to the user."
    ))]

    # Append RAG instruction when a document is available for this thread
    if thread_id and get_retriever(thread_id) is not None:
        meta  = THREAD_METADATA.get(thread_id, {})
        fname = meta.get("filename", "a document")
        ftype = meta.get("filetype", "Document")
        system_messages.append(SystemMessage(content=(
            f"The user has uploaded a {ftype} called '{fname}' for this conversation. "
            "Whenever they ask about the document, its contents, or any topic it may cover, "
            "you MUST call rag_tool with a relevant search query before answering. "
            "After rag_tool returns, use ONLY the 'context' field from the result to compose "
            "a clear, well-formatted natural language answer. "
            "NEVER output raw JSON, tool results, dict structures, or metadata to the user."
        )))

    response = await llm_with_tools.ainvoke(system_messages + messages)
    return {"messages": [response]}
