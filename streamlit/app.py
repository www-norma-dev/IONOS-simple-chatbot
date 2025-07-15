import streamlit as st
import requests
import time

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="IONOS Chatbot Tester", page_icon="💬", layout="wide")

# --- Sidebar ---
st.sidebar.title("💬 Chat Controls")
st.sidebar.markdown("---")

# RAG Initialization
st.sidebar.subheader("🔗 RAG Initialization")
rag_url = st.sidebar.text_input("Page URL", value="https://example.com", key="rag_url")
if st.sidebar.button("Initialize RAG", key="init_rag_btn"):
    try:
        resp = requests.post(f"{BACKEND_URL}/init", json={"page_url": rag_url})
        if resp.ok:
            # Fetch initial chat history from backend after RAG init
            hist_resp = requests.get(f"{BACKEND_URL}/", headers={"x-model-id": st.session_state.get('model_select', '')})
            if hist_resp.ok:
                st.session_state["chat_history"] = hist_resp.json()
            st.sidebar.success(f"RAG initialized! {resp.json()}")
            st.rerun()  # Force UI refresh
        else:
            st.sidebar.error(f"Failed: {resp.text}")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

st.sidebar.markdown("---")

# Model Selection
st.sidebar.subheader("🤖 Model Selection")
MODEL_OPTIONS = [
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/Meta-Llama-3.1-405B-Instruct-FP8",
]
model = st.sidebar.selectbox("Model", MODEL_OPTIONS, key="model_select")

st.sidebar.markdown("---")

# --- Main Chat Area ---
st.title("IONOS Chatbot 🗨️")

if "chat_history" not in st.session_state:
    # On first load, fetch from backend
    try:
        resp = requests.get(f"{BACKEND_URL}/", headers={"x-model-id": model})
        if resp.ok:
            st.session_state["chat_history"] = resp.json()
        else:
            st.session_state["chat_history"] = []
    except Exception:
        st.session_state["chat_history"] = []

# Show chat bubbles
st.markdown("#### Conversation")
chat_container = st.container()
with chat_container:
    for msg in st.session_state["chat_history"]:
        if msg["type"] == "human":
            st.markdown(f"<div style='text-align:right; background:#4F8EF7; color:white; padding:10px; border-radius:10px; margin:5px 0 5px 30%;'><b>🧑‍💻 You:</b> {msg['content']}</div>", unsafe_allow_html=True)
        elif msg["type"] == "ai":
            st.markdown(f"<div style='text-align:left; background:#FFD166; color:#222; padding:10px; border-radius:10px; margin:5px 30% 5px 0;'><b>🤖 Bot:</b> {msg['content']}</div>", unsafe_allow_html=True)

# --- Chat Input ---
with st.form("chat_form", clear_on_submit=True):
    user_message = st.text_input("Type your message...", key="user_message")
    send_btn = st.form_submit_button("Send", use_container_width=True)

if send_btn and user_message.strip():
    # Append user message to session state immediately
    st.session_state["chat_history"].append({"type": "human", "content": user_message})
    
    # Create a placeholder for the bot response
    with st.spinner("Bot is thinking..."):
        try:
            resp = requests.post(
                f"{BACKEND_URL}/",
                json={"prompt": user_message},
                headers={"x-model-id": model},
            )
            if resp.ok:
                # Append bot response to session state immediately
                st.session_state["chat_history"].append({"type": "ai", "content": resp.text})
                
                # Optional: Sync with backend to ensure consistency
                try:
                    hist_resp = requests.get(f"{BACKEND_URL}/", headers={"x-model-id": model})
                    if hist_resp.ok:
                        backend_history = hist_resp.json()
                        # Only update if backend has more recent data
                        if len(backend_history) > len(st.session_state["chat_history"]):
                            st.session_state["chat_history"] = backend_history
                except Exception:
                    pass  # If sync fails, continue with local state
                
                # Force UI refresh to show the new messages
                st.rerun()
            else:
                st.error(f"Failed: {resp.text}")
        except Exception as e:
            st.error(f"Error: {e}")