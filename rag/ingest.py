"""rag/ingest.py — Document loading, chunking and Pinecone indexing."""
import os
import tempfile
from typing import Optional

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
    UnstructuredPowerPointLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore

from config import CHUNK_SIZE, CHUNK_OVERLAP, PINECONE_INDEX_NAME
from rag.store import set_retriever

# Human-readable labels, also used for validation
SUPPORTED_EXTENSIONS = {
    ".pdf":  "PDF Document",
    ".docx": "Word Document",
    ".doc":  "Word Document",
    ".txt":  "Text File",
    ".csv":  "CSV File",
    ".pptx": "PowerPoint Presentation",
}

_LOADERS = {
    ".pdf":  lambda p: PyPDFLoader(p),
    ".docx": lambda p: Docx2txtLoader(p),
    ".doc":  lambda p: Docx2txtLoader(p),
    ".txt":  lambda p: TextLoader(p, encoding="utf-8"),
    ".csv":  lambda p: CSVLoader(p, encoding="utf-8"),
    ".pptx": lambda p: UnstructuredPowerPointLoader(p),
}


def _get_loader(ext: str, file_path: str):
    if ext not in _LOADERS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return _LOADERS[ext](file_path)


def ingest_document(
    file_bytes: bytes,
    thread_id: str,
    embeddings,
    filename: Optional[str] = None,
) -> dict:
    """
    Chunk and index a document into Pinecone under the thread's namespace.

    Args:
        file_bytes:  Raw file content.
        thread_id:   The chat thread this document belongs to (used as namespace).
        embeddings:  An OpenAIEmbeddings (or compatible) instance.
        filename:    Original filename, used to detect extension.

    Returns:
        Metadata dict: filename, filetype, documents, chunks.
    """
    if not file_bytes:
        raise ValueError("No bytes received for ingestion.")

    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(file_bytes)
        temp_path = tmp.name

    try:
        docs   = _get_loader(ext, temp_path).load()
        chunks = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""],
        ).split_documents(docs)

        # Clear any existing vectors for this thread namespace before re-indexing.
        try:
            from pinecone import Pinecone as PineconeClient
            pc = PineconeClient(api_key=os.getenv("PINECONE_API_KEY"))
            pc.Index(PINECONE_INDEX_NAME).delete(delete_all=True, namespace=str(thread_id))
        except Exception:
            pass  # namespace doesn't exist yet on first upload; safe to ignore

        # Each thread gets its own Pinecone namespace — vectors persist across restarts.
        PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            index_name=PINECONE_INDEX_NAME,
            namespace=str(thread_id),
        )

        metadata = {
            "filename": filename or os.path.basename(temp_path),
            "filetype": SUPPORTED_EXTENSIONS[ext],
            "documents": len(docs),
            "chunks": len(chunks),
        }
        set_retriever(thread_id, metadata)
        return metadata

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
