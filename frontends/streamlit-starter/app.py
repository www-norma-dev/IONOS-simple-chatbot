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
import uuid

load_dotenv()

# Backend API configuration
BACKEND_URL = "http://localhost:8000"

# UUID for session tracking
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())

# Configure Streamlit page settings
st.set_page_config(page_title="IONOS Chatbot", page_icon="💬", layout="wide")

# --- Sidebar Configuration ---
st.sidebar.title("💬 Chat Controls")
st.sidebar.markdown("---")

# RAG Initialization Section
st.sidebar.subheader("🔗 RAG Initialization")
rag_url = st.sidebar.text_input("Page URL", value="https://example.com", key="rag_url")

# Handle RAG initialization button click
if st.sidebar.button("Initialize RAG", key="init_rag_btn"):
    try:
        # Send POST request to initialize RAG with the provided URL
        resp = requests.post(f"{BACKEND_URL}/init", json={"page_url": rag_url})
        if resp.ok:
            # Fetch updated chat history after successful RAG initialization
            hist_resp = requests.get(f"{BACKEND_URL}/", headers={"x-model-id": st.session_state.get('model_select', '')})
            if hist_resp.ok:
                st.session_state["chat_history"] = hist_resp.json()
            st.sidebar.success(f"RAG initialized! {resp.json()}")
            st.rerun()  # Force UI refresh to show updated state
        else:
            st.sidebar.error(f"Failed: {resp.text}")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

st.sidebar.markdown("---")

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
st.sidebar.selectbox("Model", MODEL_OPTIONS, key="model_select")

st.sidebar.markdown("---")

# --- Main Chat Interface ---
st.title("IONOS Chatbot 🗨️")

# Initialize chat history from backend or create empty list
if "chat_history" not in st.session_state:
    try:
        # Fetch existing chat history from backend
        resp = requests.get(
            f"{BACKEND_URL}/",
            headers={
                "x-model-id": st.session_state.get("model_select", MODEL_OPTIONS[0] if MODEL_OPTIONS else ""),
                "x-user-id": st.session_state["user_id"]
            }
        )
        if resp.ok:
            st.session_state["chat_history"] = resp.json()
        else:
            st.session_state["chat_history"] = []
    except Exception:
        # Fallback to empty history if backend is unavailable
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
    
    # Send message to backend and get AI response
    with st.spinner("Bot is thinking..."):
        try:
            # Post user message to backend with selected model
            resp = requests.post(
                f"{BACKEND_URL}/",
                json={"prompt": user_message},
                headers={
                    "x-model-id": st.session_state.get("model_select", MODEL_OPTIONS[0] if MODEL_OPTIONS else ""),
                    "x-user-id": st.session_state["user_id"]
                },
            )
            if resp.ok:
                # Add AI response to chat history
                st.session_state["chat_history"].append({"type": "ai", "content": resp.text})
                
                # Attempt to sync with backend chat history
                try:
                    hist_resp = requests.get(
                        f"{BACKEND_URL}/",
                        headers={
                            "x-model-id": st.session_state.get("model_select", MODEL_OPTIONS[0] if MODEL_OPTIONS else ""),
                            "x-user-id": st.session_state["user_id"]
                        }
                    )
                    if hist_resp.ok:
                        backend_history = hist_resp.json()
                        # Update local history if backend has more recent messages
                        if len(backend_history) > len(st.session_state["chat_history"]):
                            st.session_state["chat_history"] = backend_history
                except Exception:
                    # Continue with local history if backend sync fails
                    pass  
                
                st.rerun()  # Refresh UI to show new messages
            else:
                st.error(f"Failed: {resp.text}")
        except Exception as e:
            st.error(f"Error: {e}")

