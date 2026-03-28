"""backend/routers/documents.py — Document upload and removal endpoints."""
import os

from fastapi import APIRouter, File, HTTPException, UploadFile

import core.graph as graph
from rag.ingest import ingest_document, SUPPORTED_EXTENSIONS
from rag.store import clear_retriever

router = APIRouter(prefix="/threads", tags=["documents"])


@router.post("/{thread_id}/documents")
async def upload_document(thread_id: str, file: UploadFile = File(...)):
    """Ingest an uploaded document into PGVector for the given thread."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            ),
        )
    file_bytes = await file.read()
    try:
        metadata = ingest_document(
            file_bytes=file_bytes,
            thread_id=thread_id,
            embeddings=graph.embeddings,
            filename=file.filename,
        )
        return metadata
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{thread_id}/documents")
def remove_document(thread_id: str):
    """Clear the in-memory document metadata for a thread."""
    clear_retriever(thread_id)
    return {"cleared": True}
