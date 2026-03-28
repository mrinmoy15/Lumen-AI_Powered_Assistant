"""
app.py — LUMEN Streamlit frontend entry point.

The frontend contains no business logic — it talks exclusively to the
FastAPI backend via HTTP.  Start the backend first:

    uvicorn backend.main:app --port 8000 --reload

Then run the frontend:

    streamlit run app.py
"""
import streamlit as st

from ui.utils import load_css, generate_thread_id
from ui.sidebar import render_sidebar, _retrieve_all_threads
from ui.dialogs import confirm_delete_dialog
from ui.chat import render_chat

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

# ── Main chat area ────────────────────────────────────────────
render_chat(st.session_state["thread_id"])
