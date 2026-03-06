"""ui/utils.py — Streamlit UI helper utilities."""
import uuid
import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_core.messages import BaseMessage

from config import CSS_PATH, HTML_PATH, THREAD_CLEANUP_DAYS
from db.database_utils import connection


# ── Thread ID ────────────────────────────────────────────────
def generate_thread_id() -> str:
    return str(uuid.uuid4())


# ── Session state helpers ─────────────────────────────────────
def reset_chat():
    st.session_state["thread_id"]      = generate_thread_id()
    st.session_state["message_history"] = []


def add_thread(thread_id: str, first_message: str):
    thread_id   = str(thread_id)
    thread_entry = {"thread_id": thread_id, "label": first_message}
    if not any(t["thread_id"] == thread_id for t in st.session_state["chat_threads"]):
        st.session_state["chat_threads"].append(thread_entry)
    cursor = connection.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO thread_tracker (thread_id) VALUES (?)", (thread_id,)
    )
    connection.commit()


# ── Message helpers ───────────────────────────────────────────
def load_conversation(thread_id: str) -> list[BaseMessage]:
    from core.graph import chatbot
    return chatbot.get_state(
        config={"configurable": {"thread_id": thread_id}}
    ).values["messages"]


def message_format_converter(messages: list[BaseMessage]) -> list[dict]:
    result = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        # Skip messages with non-string content (e.g. tool call dicts)
        if isinstance(msg.content, str) and msg.content.strip():
            result.append({"role": role, "content": msg.content})
    return result


# ── Asset loaders ─────────────────────────────────────────────
def load_css(path: str | None = None):
    file = path or CSS_PATH
    with open(file, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def load_html(path: str | None = None) -> str:
    file = path or HTML_PATH
    with open(file, "r", encoding="utf-8") as f:
        return f.read()
