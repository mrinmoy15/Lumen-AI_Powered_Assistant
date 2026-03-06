"""
app.py — LUMEN entry point.
Run with: streamlit run app.py
"""
import streamlit as st

from config import THREAD_CLEANUP_DAYS
from db.database_utils import cleanup_old_threads, initialize_thread_tracker
from ui.utils import load_css, generate_thread_id, reset_chat
from ui.sidebar import render_sidebar, _retrieve_all_threads
from ui.dialogs import confirm_delete_dialog
from ui.chat import render_chat

# ── One-time DB init ─────────────────────────────────────────
initialize_thread_tracker()
cleanup_old_threads(days=THREAD_CLEANUP_DAYS)

# ── CSS ──────────────────────────────────────────────────────
load_css()

# ── Session state defaults ────────────────────────────────────
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = _retrieve_all_threads()

if "pending_delete_thread_id" not in st.session_state:
    st.session_state["pending_delete_thread_id"] = None

if "pdf_ingested_threads" not in st.session_state:
    st.session_state["pdf_ingested_threads"] = {}

# ── Delete confirmation dialog ────────────────────────────────
if st.session_state["pending_delete_thread_id"]:
    confirm_delete_dialog(st.session_state["pending_delete_thread_id"])
    st.session_state["pending_delete_thread_id"] = None

# ── Sidebar ───────────────────────────────────────────────────
render_sidebar()

# ── Chat config ───────────────────────────────────────────────
CONFIG = {
    "configurable": {"thread_id": st.session_state["thread_id"]},
    "metadata":     {"thread_id": st.session_state["thread_id"]},
    "run_name":     "chat_turn",
}

# ── Main chat area ────────────────────────────────────────────
render_chat(CONFIG)
