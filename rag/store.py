"""rag/store.py — In-memory per-thread retriever and metadata store."""
from typing import Any, Dict, Optional

THREAD_RETRIEVERS: Dict[str, Any]   = {}
THREAD_METADATA:   Dict[str, dict]  = {}


def get_retriever(thread_id: Optional[str]):
    """Return the FAISS retriever for a thread, or None if not loaded."""
    if thread_id and thread_id in THREAD_RETRIEVERS:
        return THREAD_RETRIEVERS[thread_id]
    return None


def set_retriever(thread_id: str, retriever, metadata: dict):
    """Store a retriever and its metadata for a thread."""
    THREAD_RETRIEVERS[str(thread_id)] = retriever
    THREAD_METADATA[str(thread_id)]   = metadata


def clear_retriever(thread_id: str):
    """Remove the retriever for a thread (e.g. after document removal)."""
    THREAD_RETRIEVERS.pop(str(thread_id), None)
    THREAD_METADATA.pop(str(thread_id), None)
