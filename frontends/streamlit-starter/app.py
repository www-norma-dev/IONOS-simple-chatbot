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
from dotenv import load_dotenv

load_dotenv()

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
@st.cache_data(ttl=1)  # Refresh each second
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
    selected_model = st.sidebar.selectbox(
        "Select Model:",
        options=inference_models,
        key="inference_select",
        index=0
    )
    model = selected_model  # we use teh AI model hub from ionos
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
        model_id = finetuned_models[selected_name]
        model = f"studio:{model_id}"  # Prefix for backend routing

st.sidebar.markdown("---")

# --- Main Chat Interface ---
st.title("IONOS Starter Pack")

# Initialize chat history in frontend only
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Display chat messages with modern styling
st.markdown("<div class='conversation-header'><h4>💬 Conversation</h4></div>", unsafe_allow_html=True)

chat_container = st.container()
with chat_container:
    for msg in st.session_state["chat_history"]:
        if msg["type"] == "human":
            st.markdown(
                f"""<div class='chat-message user-message'>
                    <div class='message-label'>🧑‍💻 You</div>
                    <div class='message-content'>{msg['content']}</div>
                </div>""", 
                unsafe_allow_html=True
            )
        elif msg["type"] == "ai":
            st.markdown(
                f"""<div class='chat-message bot-message'>
                    <div class='message-label'>🤖 AI Assistant</div>
                    <div class='message-content'>{msg['content']}</div>
                </div>""", 
                unsafe_allow_html=True
            )

# --- Chat Input Form ---
with st.form("chat_form", clear_on_submit=True):
    user_message = st.text_input("Type your message...", key="user_message", placeholder="Ask me anything...")
    send_btn = st.form_submit_button("Send Message", use_container_width=True)

# Handel message submission
if send_btn and user_message.strip():
    # Add user message to chat history immediately 
    st.session_state["chat_history"].append({"type": "human", "content": user_message})
    # avoiding to send an empty messages array
    messages_to_send = st.session_state["chat_history"] if st.session_state["chat_history"] else [{"type": "human", "content": user_message}]
    with st.spinner("AI is thinking..."):
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
                st.rerun() 
            else:
                st.error(f"Failed: {resp.text}")
        except Exception as e:
            st.error(f"Error: {e}")
