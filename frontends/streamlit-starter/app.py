"""
IONOS Chatbot Streamlit Application

This application provides a web interface for interacting with the IONOS chatbot backend.
Features include:
- RAG (Retrieval-Augmented Generation) initialization from web URLs
- Model selection for different LLaMA variants
- Interactive chat interface with message history
- Real-time communication with FastAPI backend
"""

import streamlit as st
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Backend API configuration
BACKEND_URL = "http://localhost:8000"

# Configure Streamlit page settings
st.set_page_config(page_title="IONOS Chatbot", page_icon="💬", layout="wide")

# --- Sidebar Configuration ---
st.sidebar.title("💬 Chat Controls")
st.sidebar.markdown("---")

# RAG Initialization UI and logic removed (step 2)

# Model Selection Section
st.sidebar.subheader("🤖 Model Selection")

@st.cache_data(ttl=300)
def fetch_model_ids():
    try:
        resp = requests.get(
            "https://openai.inference.de-txl.ionos.com/v1/models",
            headers={"Authorization": f"Bearer {os.getenv('IONOS_API_KEY')}"}
        )
        resp.raise_for_status()
        data = resp.json()
        return [m["id"] for m in data.get("data", [])]  # models under "data"
    except Exception as e:
        st.sidebar.error(f"Error fetching models: {e}")
        return []

MODEL_OPTIONS = fetch_model_ids() or ["meta‑llama/Meta‑Llama‑3.1‑8B‑Instruct"]
model = st.sidebar.selectbox("Model", MODEL_OPTIONS, key="model_select")

st.sidebar.markdown("---")

# --- Main Chat Interface ---
st.title("IONOS Chatbot 🗨️")

# Initialize chat history in frontend only
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Display chat messages in bubble format
st.markdown("#### Conversation")
chat_container = st.container()
with chat_container:
    for msg in st.session_state["chat_history"]:
        if msg["type"] == "human":
            # User messages - right-aligned blue bubbles
            st.markdown(
                f"<div style='text-align:right; background:#4F8EF7; color:white; padding:10px; "
                f"border-radius:10px; margin:5px 0 5px 30%;'>"
                f"<b>🧑‍💻 You:</b> {msg['content']}</div>", 
                unsafe_allow_html=True
            )
        elif msg["type"] == "ai":
            # AI responses - left-aligned yellow bubbles
            st.markdown(
                f"<div style='text-align:left; background:#FFD166; color:#222; padding:10px; "
                f"border-radius:10px; margin:5px 30% 5px 0;'>"
                f"<b>🤖 Bot:</b> {msg['content']}</div>", 
                unsafe_allow_html=True
            )

# --- Chat Input Form ---
with st.form("chat_form", clear_on_submit=True):
    user_message = st.text_input("Type your message...", key="user_message")
    send_btn = st.form_submit_button("Send", use_container_width=True)

# Handle message submission
if send_btn and user_message.strip():
    # Add user message to chat history immediately for better UX
    st.session_state["chat_history"].append({"type": "human", "content": user_message})
    # Ensure we never send an empty messages array
    messages_to_send = st.session_state["chat_history"] if st.session_state["chat_history"] else [{"type": "human", "content": user_message}]
    with st.spinner("Bot is thinking..."):
        try:
            resp = requests.post(
                f"{BACKEND_URL}/",
                json={"messages": messages_to_send},
                headers={"x-model-id": model},
            )
            if resp.ok:
                # Parse backend response (backend always returns a single message dict)
                data = resp.json() if resp.headers.get('content-type','').startswith('application/json') else {"type": "ai", "content": resp.text}
                if not isinstance(data, dict):
                    st.error("Unexpected response shape from backend (expected object)")
                else:
                    if data.get("type") == "tool":
                        st.session_state["chat_history"].append({
                            "type": "tool",
                            "name": data.get("name", "tool"),
                            "content": data.get("content", "")
                        })
                    else:
                        st.session_state["chat_history"].append({
                            "type": data.get("type", "ai"),
                            "content": data.get("content", "")
                        })
                st.rerun()  # Refresh UI to show new messages
            else:
                st.error(f"Failed: {resp.text}")
        except Exception as e:
            st.error(f"Error: {e}")

