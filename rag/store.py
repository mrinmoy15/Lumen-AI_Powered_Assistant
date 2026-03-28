"""rag/store.py — Per-thread RAG metadata store backed by Pinecone namespaces."""
import os
from typing import Any, Dict, Optional

from langchain_pinecone import PineconeVectorStore
from config import RETRIEVER_K, PINECONE_INDEX_NAME

# In-memory metadata (filename, filetype, etc.) — survives for the session.
# The actual vectors live in Pinecone under a namespace keyed by thread_id.
THREAD_METADATA: Dict[str, dict] = {}

_embeddings: Any = None


def init_store(embeddings):
    """Call once at startup with the shared OpenAIEmbeddings instance."""
    global _embeddings
    _embeddings = embeddings


def get_retriever(thread_id: Optional[str]):
    """Return a Pinecone retriever scoped to the thread's namespace, or None."""
    if not thread_id or thread_id not in THREAD_METADATA:
        return None
    vectorstore = PineconeVectorStore(
        index_name=PINECONE_INDEX_NAME,
        embedding=_embeddings,
        namespace=str(thread_id),
    )
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_K},
    )


def set_retriever(thread_id: str, metadata: dict):
    """Record that a document has been ingested for this thread."""
    THREAD_METADATA[str(thread_id)] = metadata


def clear_retriever(thread_id: str):
    """Remove in-memory metadata and delete all vectors for this thread's namespace."""
    THREAD_METADATA.pop(str(thread_id), None)
    try:
        from pinecone import Pinecone as PineconeClient
        pc = PineconeClient(api_key=os.getenv("PINECONE_API_KEY"))
        pc.Index(PINECONE_INDEX_NAME).delete(delete_all=True, namespace=str(thread_id))
    except Exception:
        pass  # namespace may not exist; safe to ignore
