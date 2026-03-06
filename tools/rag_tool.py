"""tools/rag_tool.py — LangChain tool for retrieving document context."""
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from rag.store import get_retriever, THREAD_METADATA


@tool
def rag_tool(query: str, config: RunnableConfig) -> dict:
    """
    Retrieve relevant information from the document uploaded in this conversation.
    Use this whenever the user asks about the contents of an uploaded document
    (PDF, Word, CSV, PowerPoint, or text file).
    """
    try:
        thread_id = str(config["configurable"]["thread_id"])
    except (KeyError, TypeError):
        thread_id = None

    retriever = get_retriever(thread_id)
    if retriever is None:
        return {
            "error": "No document indexed for this chat. Please upload a document first.",
            "query": query,
        }

    results = retriever.invoke(query)
    return {
        "query": query,
        "context":     [doc.page_content for doc in results],
        "metadata":    [doc.metadata     for doc in results],
        "source_file": THREAD_METADATA.get(thread_id, {}).get("filename"),
    }
