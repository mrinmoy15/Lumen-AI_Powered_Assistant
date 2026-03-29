"""ui/chat.py — Main chat area: welcome screen, message history, input."""
import streamlit as st

from ui.utils import load_html, add_thread
from ui.sidebar import stream_response


def render_chat(thread_id: str):
    """Render the full chat area for the current thread."""
    _render_welcome_or_history()
    _handle_user_input(thread_id)


def _render_welcome_or_history():
    if len(st.session_state["message_history"]) == 0:
        st.markdown(load_html(), unsafe_allow_html=True)
        return

    for message in st.session_state["message_history"]:
        avatar = "🧑" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])


def _handle_user_input(thread_id: str):
    user_input = st.chat_input("Type your message here...")
    if not user_input:
        return

    # Register thread on first message
    if len(st.session_state["message_history"]) == 0:
        label = user_input[:40] + ("..." if len(user_input) > 40 else "")
        add_thread(thread_id, label)

    # Show user message
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.text(user_input)

    # Stream assistant response from backend
    with st.chat_message("assistant", avatar="🤖"):
        ai_message = st.write_stream(stream_response(user_input, thread_id))

    st.session_state["message_history"].append({"role": "assistant", "content": ai_message})
