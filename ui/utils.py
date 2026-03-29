"""ui/utils.py — Streamlit UI helper utilities."""
import uuid
import httpx
import streamlit as st

from config import CSS_PATH, HTML_PATH, BACKEND_URL


# ── Thread ID ────────────────────────────────────────────────
def generate_thread_id() -> str:
    return str(uuid.uuid4())


# ── Session state helpers ─────────────────────────────────────
def reset_chat():
    st.session_state["thread_id"]       = generate_thread_id()
    st.session_state["message_history"] = []


def add_thread(thread_id: str, first_message: str):
    thread_id    = str(thread_id)
    thread_entry = {"thread_id": thread_id, "label": first_message}
    if not any(t["thread_id"] == thread_id for t in st.session_state["chat_threads"]):
        st.session_state["chat_threads"].append(thread_entry)
    httpx.post(
        f"{BACKEND_URL}/threads",
        json={"thread_id": thread_id, "label": first_message},
        timeout=10,
    )


# ── Message helpers ───────────────────────────────────────────
def load_conversation(thread_id: str) -> list[dict]:
    """Fetch message history from the backend as a list of role/content dicts."""
    try:
        resp = httpx.get(f"{BACKEND_URL}/threads/{thread_id}/messages", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


# ── Asset loaders ─────────────────────────────────────────────
def load_css(path=None):
    file = path or CSS_PATH
    with open(file, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def load_html(path=None) -> str:
    file = path or HTML_PATH
    with open(file, "r", encoding="utf-8") as f:
        return f.read()
