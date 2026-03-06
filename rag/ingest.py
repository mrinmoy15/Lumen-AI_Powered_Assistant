"""rag/ingest.py — Document loading, chunking and FAISS indexing."""
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
from langchain_community.vectorstores import FAISS

from config import CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_K
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
    Chunk and index a document into a per-thread FAISS retriever.

    Args:
        file_bytes:  Raw file content.
        thread_id:   The chat thread this document belongs to.
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

        retriever = FAISS.from_documents(chunks, embeddings).as_retriever(
            search_type="similarity",
            search_kwargs={"k": RETRIEVER_K},
        )

        metadata = {
            "filename": filename or os.path.basename(temp_path),
            "filetype": SUPPORTED_EXTENSIONS[ext],
            "documents": len(docs),
            "chunks": len(chunks),
        }
        set_retriever(thread_id, retriever, metadata)
        return metadata

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
