"""ui/dialogs.py — Streamlit dialog definitions."""
import streamlit as st
from db.database_utils import delete_thread
from ui.utils import reset_chat


@st.dialog("Delete chat")
def confirm_delete_dialog(thread_id: str):
    from core.graph import chatbot  # lazy import to avoid circular deps

    st.write("Are you sure you want to delete this chat?")
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Cancel", use_container_width=True, key="cancel_delete"):
            st.rerun()

    with col2:
        if st.button("Delete", use_container_width=True, key="confirm_delete", type="primary"):
            delete_thread(thread_id)
            from core.graph import chatbot
            from ui.utils import generate_thread_id
            # Refresh thread list via retrieve_all_threads
            from core.graph import checkpointer
            from ui.sidebar import _retrieve_all_threads
            st.session_state["chat_threads"] = _retrieve_all_threads()
            if str(st.session_state["thread_id"]) == str(thread_id):
                reset_chat()
            st.rerun()
