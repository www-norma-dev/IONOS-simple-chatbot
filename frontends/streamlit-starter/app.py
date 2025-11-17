"""
IONOS Chatbot Streamlit Application

This application provides a web interface for interacting with the IONOS chatbot backend.
Features include:
- ReAct agent with web search capabilities via Tavily API
- Model selection for different IONOS AI models
- Interactive chat interface with message history
- Real-time communication with FastAPI backend
"""

import streamlit as st
import requests
import time
import os
import json
from dotenv import load_dotenv
import re

load_dotenv()

# Helper to clean leading markdown headers
def clean_leading_headers(text):
    """Remove leading ## or ### from text start"""
    return re.sub(r'^#+\s*', '', text.strip())

# Backend API configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend-service:8000")

# Configure Streamlit page settings
st.set_page_config(page_title="IONOS Chatbot", page_icon="💬", layout="wide")

# Custom CSS for modern green-inspired design
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container - green gradient background */
    .main {
        background: linear-gradient(135deg, #e6fff9 0%, #e6f5ff 100%);
    }
    
    /* Sidebar styling - green colors */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #00D9A0 0%, #0099FF 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: white !important;
        font-weight: 600;
    }
    
    /* Radio buttons in sidebar */
    [data-testid="stSidebar"] .stRadio > label {
        color: white !important;
        font-weight: 500;
    }
    
    /* Select boxes in sidebar - improved styling */
    [data-testid="stSidebar"] .stSelectbox label {
        color: white !important;
        font-weight: 600;
        font-size: 1rem;
    }
    
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: white !important;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        position: relative;
    }
    
    /* Add dropdown arrow indicator */
    [data-testid="stSidebar"] .stSelectbox > div > div::after {
        content: "▼";
        position: absolute;
        right: 1rem;
        top: 50%;
        transform: translateY(-50%);
        color: #000000;
        font-size: 0.9rem;
        pointer-events: none;
        font-weight: 700;
    }
    
    /* FORCE BLACK TEXT IN DROPDOWN */
    [data-testid="stSidebar"] .stSelectbox input,
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] .stSelectbox span,
    [data-testid="stSidebar"] .stSelectbox p {
        color: #000000 !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Dropdown text - darker and readable with shadow */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] div[data-baseweb="select"] span {
        color: #000000 !important;
        background: white !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Title styling - green gradient text */
    h1 {
        background: linear-gradient(135deg, #00D9A0 0%, #0099FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 2.8rem;
    }
    
    /* Chat container */
    .chat-message {
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.75rem 0;
        animation: slideIn 0.3s ease-out;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Animated dots for thinking indicator */
    .thinking-dots::after {
        content: '';
        animation: dots 1.5s steps(4, end) infinite;
    }
    
    @keyframes dots {
        0%, 20% { content: ''; }
        40% { content: '.'; }
        60% { content: '..'; }
        80%, 100% { content: '...'; }
    }
    
    .user-message {
        background: linear-gradient(135deg, #00D9A0 0%, #0099FF 100%);
        color: white;
        margin-left: 20%;
        text-align: right;
    }
    
    .bot-message {
        background: white;
        color: #0c4a6e;
        margin-right: 20%;
        border-left: 4px solid #00D9A0;
    }
    
    .message-label {
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    
    .message-content {
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* Form styling */
    .stTextInput input {
        border-radius: 2rem;
        border: 2px solid #00D9A0;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        border-color: #0099FF;
        box-shadow: 0 0 0 3px rgba(0, 217, 160, 0.1);
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #00D9A0 0%, #0099FF 100%);
        color: white;
        border: none;
        border-radius: 2rem;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 217, 160, 0.3);
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #00c490 0%, #0088ee 100%);
        box-shadow: 0 6px 20px rgba(0, 217, 160, 0.4);
        transform: translateY(-2px);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #00D9A0 transparent transparent transparent;
    }
    
    /* Conversation header - Slick top accent */
    .conversation-header {
        background: white;
        padding: 1.25rem;
        border-radius: 1.25rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        text-align: center;
        border-top: 4px solid #00D9A0;
    }
    
    .conversation-header h4 {
        background: linear-gradient(135deg, #00D9A0 0%, #0099FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        margin: 0;
        font-size: 1.3rem;
    }
    
    /* Remove default margins */
    .block-container {
        padding-top: 3rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
st.sidebar.markdown("""
<div style='background: rgba(255,255,255,0.3); padding: 1rem; border-radius: 12px; margin-bottom: 1rem;'>
    <h1 style='color: #FFFFFF !important; font-weight: 800 !important; font-size: 1.5rem !important; margin: 0 !important; text-align: center;'>💬 Chat Controls</h1>
</div>
""", unsafe_allow_html=True)

# Model Selection Section
st.sidebar.subheader("🤖 Model Selection")

# Model type selector
model_type = st.sidebar.radio(
    "Model Type",
    options=["Inference", "Fine-tuned"],
    index=0,
    key="model_type"
)

# Inference Models (IONOS Hub)
@st.cache_data(ttl=300)
def fetch_inference_models():
    try:
        resp = requests.get(
            "https://openai.inference.de-txl.ionos.com/v1/models",
            headers={"Authorization": f"Bearer {os.getenv('IONOS_API_KEY')}"}
        )
        resp.raise_for_status()
        data = resp.json()
        return [m["id"] for m in data.get("data", [])]
    except Exception as e:
        st.sidebar.error(f"Error fetching inference models: {e}")
        return ["mistralai/Mistral-Small-24B-Instruct"]

# Fine-tuned Models (Studio) - fetch from backend
@st.cache_data(ttl=1)
def fetch_finetuned_models():
    """Fetch available fine-tuned models from backend."""
    try:
        resp = requests.get(f"{BACKEND_URL}/studio/models")
        resp.raise_for_status()
        return resp.json()  
    except Exception as e:
        st.sidebar.error(f"Error fetching fine-tuned models: {e}")
        return {}

if model_type == "Inference":
    inference_models = fetch_inference_models()
    # Preselect gpt-oss-120b if available
    default_index = 0
    try:
        default_index = inference_models.index("openai/gpt-oss-120b")
    except (ValueError, AttributeError):
        pass
    
    selected_model = st.sidebar.selectbox(
        "Select Model:",
        options=inference_models,
        key="inference_select",
        index=default_index
    )
    model = selected_model
else:  # Fine-tuned
    finetuned_models = fetch_finetuned_models()
    finetuned_names = list(finetuned_models.keys())
    if not finetuned_names:
        st.sidebar.warning("No fine-tuned models configured in backend")
        model = "mistralai/Mistral-Small-24B-Instruct"  # Fallback
    else:
        selected_name = st.sidebar.selectbox(
            "Select Model:",
            options=finetuned_names,
            key="finetuned_select",
            index=0
        )
        model = finetuned_models[selected_name]  # Studio model UUID

st.sidebar.markdown("---")

# Streaming toggle (only for inference models)
enable_streaming = model_type == "Inference" and st.sidebar.checkbox("⚡ Enable Streaming", value=True, help="Stream responses token-by-token (web search still works)")

st.sidebar.markdown("---")

# --- Main Chat Interface ---
st.title("IONOS Starter Pack")

# Initialize chat history in frontend only
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "processing" not in st.session_state:
    st.session_state["processing"] = False

# Chat messages area
st.markdown("<div class='conversation-header'><h4>💬 Conversation</h4></div>", unsafe_allow_html=True)

# Container for chat messages
messages_container = st.container()

with messages_container:
    for msg in st.session_state["chat_history"]:
        if msg["type"] == "human":
            st.markdown(
                f"""<div class='chat-message user-message'>
                    <div class='message-content'>{msg['content']}</div>
                </div>""", 
                unsafe_allow_html=True
            )
        elif msg["type"] == "ai":
            st.markdown(
                f"""<div class='chat-message bot-message'>
                    <div class='message-content'>{clean_leading_headers(msg['content'])}</div>
                </div>""", 
                unsafe_allow_html=True
            )

# Spacer
st.markdown("<br>", unsafe_allow_html=True)

# --- Chat Input ---
if st.session_state.get("waiting_for_response", False):
    st.markdown("""
    <style>
        div[data-testid="stForm"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    send_btn = False
    user_message = ""
else:
    input_container = st.container()
    with input_container:
        with st.form("chat_form", clear_on_submit=True):
            user_message = st.text_input("", key="user_message", placeholder="Ask anything...", label_visibility="collapsed")
            send_btn = st.form_submit_button("Send", use_container_width=True)

# Handle message submission
if send_btn and user_message.strip():
    # Add user message to chat history
    st.session_state["chat_history"].append({"type": "human", "content": user_message})
    st.session_state["waiting_for_response"] = True
    st.rerun()

# If waiting for response, make API call
if st.session_state.get("waiting_for_response", False):
    st.session_state["waiting_for_response"] = False
    messages_to_send = st.session_state["chat_history"]
    
    # Create placeholder inside messages container 
    with messages_container:
        response_placeholder = st.empty()
    
    if enable_streaming:
        # Streaming mode
        try:
            full_response = ""
            thinking = False
            
            resp = requests.post(f"{BACKEND_URL}/?stream=true", json={"messages": messages_to_send}, 
                                headers={"x-model-id": model}, stream=True)
            
            for line in resp.iter_lines():
                if line and line.startswith(b'data: '):
                    data_str = line[6:].decode('utf-8').strip()
                    if data_str == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if 'status' in data and data['status'] == 'thinking':
                            # Show thinking indicator
                            thinking = True
                            response_placeholder.markdown(f"""<div class='chat-message bot-message'>
                                <div class='message-content'><em><span class='thinking-dots'>🔍 Searching</span></em></div>
                            </div>""", unsafe_allow_html=True)
                        elif 'content' in data:
                            if thinking:
                                thinking = False
                                full_response = ""
                            full_response += data['content']
                            response_placeholder.markdown(f"""<div class='chat-message bot-message'>
                                <div class='message-content'>{clean_leading_headers(full_response)}</div>
                            </div>""", unsafe_allow_html=True)
                        elif 'error' in data:
                            st.error(f"Error: {data['error']}")
                            break
                    except json.JSONDecodeError:
                        pass
            
            st.session_state["chat_history"].append({"type": "ai", "content": full_response})
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        # Non-streaming mode (fine-tuned models)
        try:
            # Show thinking indicator
            response_placeholder.markdown(f"""<div class='chat-message bot-message'>
                <div class='message-content'><em><span class='thinking-dots'>💭 Thinking</span></em></div>
            </div>""", unsafe_allow_html=True)
            
            resp = requests.post(
                f"{BACKEND_URL}/",
                json={"messages": messages_to_send},
                headers={"x-model-id": model},
                timeout=180
            )
            if resp.ok:
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
                st.rerun() 
            else:
                st.error(f"Failed: {resp.text}")
        except Exception as e:
            st.error(f"Error: {e}")

