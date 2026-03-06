"""ui/sidebar.py — Sidebar rendering: new chat, document upload, conversation list."""
import os
import asyncio
import streamlit as st
from langchain_core.messages import HumanMessage

from config import MAX_SIDEBAR_THREADS
from rag.ingest import ingest_document, SUPPORTED_EXTENSIONS
from ui.utils import reset_chat, load_conversation, message_format_converter


# ── Thread listing (async helper) ────────────────────────────
def _retrieve_all_threads() -> list[dict]:
    from core.graph import checkpointer, run_async

    async def _list():
        seen, threads = set(), []
        async for checkpoint in checkpointer.alist(None):
            tid = checkpoint.config["configurable"]["thread_id"]
            if tid in seen:
                continue
            seen.add(tid)
            messages = checkpoint.checkpoint.get("channel_values", {}).get("messages", [])
            first_human = next(
                (m.content[:40] + ("..." if len(m.content) > 40 else "")
                 for m in messages if isinstance(m, HumanMessage)),
                None,
            )
            if first_human:
                threads.append({"thread_id": tid, "label": first_human})
        return threads

    return run_async(_list())


# ── Streaming helper (used by chat.py) ───────────────────────
def stream_response(user_input: str, config: dict):
    from core.graph import chatbot, run_async
    from langchain_core.messages import HumanMessage as HM

    async def _astream():
        async for chunk, meta in chatbot.astream(
            {"messages": [HM(content=user_input)]},
            config=config,
            stream_mode="messages",
        ):
            if (
                chunk.content
                and not isinstance(chunk.content, list)
                and meta.get("langgraph_node") == "chat_node"
            ):
                yield chunk.content

    async def _collect():
        parts = []
        async for c in _astream():
            parts.append(c)
        return parts

    for part in run_async(_collect()):
        yield part


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
            from rag.store import clear_retriever
            del st.session_state["pdf_ingested_threads"][current_tid]
            clear_retriever(current_tid)
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
            from core.graph import embeddings
            result = ingest_document(
                file_bytes=uploaded.getvalue(),
                thread_id=current_tid,
                embeddings=embeddings,
                filename=uploaded.name,
            )
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
                st.session_state["thread_id"] = tid
                messages = load_conversation(tid)
                st.session_state["message_history"] = message_format_converter(messages)

        with col2:
            with st.popover("···", use_container_width=True):
                if st.button("🗑️ Delete", key=f"delete_{tid}", use_container_width=True):
                    st.session_state["pending_delete_thread_id"] = tid
                    st.rerun()
