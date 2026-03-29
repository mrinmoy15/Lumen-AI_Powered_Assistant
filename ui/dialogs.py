"""ui/dialogs.py — Streamlit dialog definitions."""
import httpx
import streamlit as st

from config import BACKEND_URL
from ui.utils import reset_chat


@st.dialog("Delete chat")
def confirm_delete_dialog(thread_id: str):
    st.write("Are you sure you want to delete this chat?")
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Cancel", use_container_width=True, key="cancel_delete"):
            st.rerun()

    with col2:
        if st.button("Delete", use_container_width=True, key="confirm_delete", type="primary"):
            httpx.delete(f"{BACKEND_URL}/threads/{thread_id}", timeout=10)

            from ui.sidebar import _retrieve_all_threads
            st.session_state["chat_threads"] = _retrieve_all_threads()

            if str(st.session_state["thread_id"]) == str(thread_id):
                reset_chat()

            st.rerun()
