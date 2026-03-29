"""ui/sidebar.py — Sidebar rendering: new chat, document upload, conversation list."""
import json
import os

import httpx
import streamlit as st

from config import MAX_SIDEBAR_THREADS, BACKEND_URL
from rag.ingest import SUPPORTED_EXTENSIONS
from ui.utils import reset_chat, load_conversation


# ── Thread listing ────────────────────────────────────────────
def _retrieve_all_threads() -> list[dict]:
    try:
        resp = httpx.get(f"{BACKEND_URL}/threads", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


# ── Streaming helper (consumed by chat.py via st.write_stream) ─
def stream_response(user_input: str, thread_id: str):
    """POST to /threads/{thread_id}/chat and yield SSE chunks one by one."""
    with httpx.Client(timeout=None) as client:
        with client.stream(
            "POST",
            f"{BACKEND_URL}/threads/{thread_id}/chat",
            json={"message": user_input},
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data != "[DONE]":
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            pass


# ── Sidebar render ────────────────────────────────────────────
def render_sidebar():
    st.sidebar.title("Chatbot Powered by LangGraph")

    if st.sidebar.button("New Chat"):
        reset_chat()

    _render_document_upload()

    st.sidebar.divider()
    _render_conversation_list()


def _render_document_upload():
    st.sidebar.divider()
    st.sidebar.header("Document Upload")

    current_tid    = str(st.session_state["thread_id"])
    already_loaded = st.session_state["pdf_ingested_threads"].get(current_tid)

    if already_loaded:
        st.sidebar.success(f"📄 **{already_loaded}**")
        if st.sidebar.button("🗑️ Remove document", use_container_width=True, key="remove_doc"):
            httpx.delete(f"{BACKEND_URL}/threads/{current_tid}/documents", timeout=10)
            del st.session_state["pdf_ingested_threads"][current_tid]
            st.rerun()
        return

    supported_label = ", ".join(SUPPORTED_EXTENSIONS.keys())
    uploaded = st.sidebar.file_uploader(
        f"Supported: {supported_label}",
        type=None,
        label_visibility="visible",
        key=f"doc_uploader_{current_tid}",
    )

    if uploaded is None:
        return

    ext = os.path.splitext(uploaded.name)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        st.sidebar.error(
            f"❌ **Unsupported file type:** `{uploaded.name}`\n\n"
            f"Supported types: {supported_label}"
        )
        st.stop()

    with st.sidebar.status("📥 Processing document...", expanded=False) as status:
        try:
            resp = httpx.post(
                f"{BACKEND_URL}/threads/{current_tid}/documents",
                files={"file": (uploaded.name, uploaded.getvalue())},
                timeout=120,
            )
            resp.raise_for_status()
            result = resp.json()
            st.session_state["pdf_ingested_threads"][current_tid] = uploaded.name
            status.update(
                label=f"✅ Ready — {result['chunks']} chunks indexed",
                state="complete",
            )
        except Exception as e:
            status.update(label="❌ Ingestion failed", state="error")
            st.sidebar.error(f"Failed to process document: {e}")
            st.stop()

    st.rerun()


def _render_conversation_list():
    st.sidebar.header("My Conversations")

    for thread in st.session_state["chat_threads"][-MAX_SIDEBAR_THREADS:]:
        tid   = thread["thread_id"]
        label = str(thread["label"])
        col1, col2 = st.sidebar.columns([6, 1])

        with col1:
            if st.button(label, key=f"thread_{tid}", use_container_width=True):
                st.session_state["thread_id"]       = tid
                st.session_state["message_history"] = load_conversation(tid)

        with col2:
            with st.popover("···", use_container_width=True):
                if st.button("🗑️ Delete", key=f"delete_{tid}", use_container_width=True):
                    st.session_state["pending_delete_thread_id"] = tid
                    st.rerun()
