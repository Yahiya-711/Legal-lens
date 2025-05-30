import streamlit as st
import time
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from streamlit.components.v1 import html
from parser_agent.parser import extract_text_from_pdf, extract_text_from_image
from summarizer_agent.summarizer import summarize_text
from tts_agent.tts import text_to_speech
from chatbot_agent.chatbot import get_chatbot_response
from ui_frontend.languages import get_text, LANGUAGES
import requests
import re
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Chat UI Styles and Animations
CHAT_STYLES = """
<style>
/* Typing animation */
.typing-dots {
    display: inline-flex;
    align-items: center;
    height: 17px;
}
.typing-dots span {
    width: 7px;
    height: 7px;
    margin: 0 1px;
    background-color: #9e9e9e;
    border-radius: 50%;
    display: inline-block;
    opacity: 0.4;
}
.typing-dots span:nth-child(1) {
    animation: pulse 1s infinite;
}
.typing-dots span:nth-child(2) {
    animation: pulse 1s infinite;
    animation-delay: 0.2s;
}
.typing-dots span:nth-child(3) {
    animation: pulse 1s infinite;
    animation-delay: 0.4s;
}
@keyframes pulse {
    0% { opacity: 0.4; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.2); }
    100% { opacity: 0.4; transform: scale(1); }
}

/* Message animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.stChatMessage {
    animation: fadeIn 0.3s ease-out;
    transition: all 0.3s;
}

/* Message bubbles */
[data-testid="stChatMessage"] > div:first-child {
    border-radius: 18px !important;
    padding: 10px 16px !important;
    max-width: 80%;
}
[data-testid="stChatMessage"]:has(> div:first-child > div:first-child > div:first-child > .st-emotion-cache-4oy321) {
    justify-content: flex-end;
}
.user-message {
    background: #0d6efd;
    color: white;
    border-radius: 18px 18px 0 18px !important;
}
.bot-message {
    background: #f1f3f4;
    border-radius: 18px 18px 18px 0 !important;
}
.message-timestamp {
    font-size: 0.8rem;
    color: #666;
    margin-top: 4px;
    display: block;
}
</style>
"""

def clean_text(text: str) -> str:
    """Clean text by removing markdown characters and extra whitespace."""
    text = re.sub(r'[*#_~`]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def initialize_session_state():
    """Initialize all required session state variables."""
    defaults = {
        'interface_language': "English",
        'summary_language': "English",
        'summary': None,
        'extracted_text': None,
        'audio_file': None,
        'chat_history': [
            {
                "role": "system",
                "content": "You are a helpful legal assistant specialized in Indian law."
            },
            {
                "role": "assistant",
                "content": get_text("welcome_message", "English"),
                "timestamp": datetime.now().strftime("%H:%M")
            }
        ],
        'bot_typing': False,
        'last_message': None,
        'user_avatar': "🧑"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_typing_indicator():
    """Display animated typing dots."""
    with st.chat_message("assistant", avatar=get_text("bot_avatar")):
        st.markdown(
            '<div class="typing-dots"><span></span><span></span><span></span></div>',
            unsafe_allow_html=True
        )

def generate_bot_response():
    """Generate and display bot response with typing effect."""
    if st.session_state.get("bot_typing"):
        show_typing_indicator()
        
        placeholder = st.empty()
        full_response = get_chatbot_response(
            st.session_state.last_message,
            st.session_state.extracted_text,
            st.session_state.interface_language
        )
        
        # Progressive typing effect
        partial_response = ""
        for chunk in full_response.split():
            partial_response += chunk + " "
            time.sleep(0.05)
            placeholder.markdown(
                f'<div class="bot-message">{partial_response}</div>',
                unsafe_allow_html=True
            )
        
        # Finalize message
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": full_response,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        st.session_state.bot_typing = False
        st.rerun()

def display_chat_history():
    """Display chat messages with styling."""
    for msg in st.session_state.chat_history[1:]:  # Skip system message
        avatar = st.session_state.user_avatar if msg["role"] == "user" else get_text