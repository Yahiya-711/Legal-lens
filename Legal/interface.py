import streamlit as st
import logging
import os
import traceback
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Optional, Tuple
import requests
import re
from parser_agent.parser import extract_text_from_pdf, extract_text_from_image
from summarizer_agent.summarizer import summarize_text
from tts_agent.tts import text_to_speech
from chatbot_agent.chatbot import get_chatbot_response
from ui_frontend.languages import get_text, LANGUAGES

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
                "content": "You are a helpful legal assistant. Answer questions about legal documents clearly and concisely."
            },
            {
                "role": "assistant",
                "content": get_text("welcome_message", "English"),
                "timestamp": datetime.now().strftime("%H:%M")
            }
        ],
        'bot_typing': False,
        'last_message': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def clean_text(text: str) -> str:
    """Clean text by removing special characters and normalizing whitespace."""
    text = re.sub(r'[*#_~`]', '', text)  # Remove markdown characters
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    return text

def extract_names_roles(text: str, language: str = "English") -> Optional[List[Tuple[str, str]]]:
    """
    Extract names and their roles from document text using AI.
    
    Args:
        text: The document text to analyze
        language: Target language for role translations
        
    Returns:
        List of (name, role) tuples or None if extraction fails
    """
    try:
        cleaned_text = clean_text(text)[:2000]  # Limit input size
        
        prompt = f"""Extract names and roles from this legal document text.
        Return ONLY as a list of tuples in format: [("Name1", "Role1"), ("Name2", "Role2")]
        Include only names with clearly stated roles.
        Document excerpt:
        {cleaned_text}"""

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            logger.error("API key not configured")
            return None

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You extract precise (name, role) pairs from legal documents."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            },
            timeout=30  # Add timeout
        )

        if response.status_code == 200:
            try:
                content = response.json()["choices"][0]["message"]["content"]
                names_roles = eval(content)
                
                if (isinstance(names_roles, list) and 
                    all(isinstance(item, tuple) and len(item) == 2 
                        for item in names_roles)):
                    
                    if language != "English":
                        return translate_roles(names_roles, language)
                    return names_roles
            except Exception as e:
                logger.error(f"Failed to parse response: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        return None

def translate_roles(names_roles: List[Tuple[str, str]], target_lang: str) -> List[Tuple[str, str]]:
    """Translate role descriptions to target language."""
    translated = []
    for name, role in names_roles:
        try:
            prompt = f"Translate this legal role to {target_lang}: {role}"
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You translate legal terms to {target_lang} accurately."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                },
                timeout=30
            )
            if response.status_code == 200:
                translated_role = response.json()["choices"][0]["message"]["content"].strip()
                translated.append((name, translated_role))
            else:
                translated.append((name, role))
        except Exception:
            translated.append((name, role))
    return translated

def handle_file_upload():
    """Process uploaded file and extract text."""
    uploaded_file = st.file_uploader(
        get_text("upload_title", st.session_state.interface_language),
        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
        help=get_text("upload_help", st.session_state.interface_language)
    )
    
    if uploaded_file:
        try:
            with st.spinner(get_text("extracting_text", st.session_state.interface_language)):
                if uploaded_file.type == "application/pdf":
                    st.session_state.extracted_text = extract_text_from_pdf(uploaded_file)
                else:
                    st.session_state.extracted_text = extract_text_from_image(uploaded_file)
                    
            display_document_preview()
            
        except Exception as e:
            logger.error(f"File processing failed: {str(e)}\n{traceback.format_exc()}")
            st.error(f"{get_text('error_processing', st.session_state.interface_language)}: {str(e)}")

def display_document_preview():
    """Display document preview and extracted names/roles."""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(get_text("document_preview", st.session_state.interface_language))
        if st.session_state.extracted_text:
            st.text_area(
                label="Document Content",
                value=st.session_state.extracted_text,
                height=400,
                label_visibility="collapsed"
            )
    
    with col2:
        st.subheader(get_text("key_people", st.session_state.interface_language))
        if st.button(get_text("extract_roles", st.session_state.interface_language)):
            with st.spinner(get_text("analyzing", st.session_state.interface_language)):
                names_roles = extract_names_roles(
                    st.session_state.extracted_text,
                    st.session_state.summary_language
                )
                if names_roles:
                    for name, role in names_roles:
                        st.markdown(f"**{name}** - {role}")
                else:
                    st.info(get_text("no_roles_found", st.session_state.interface_language))

def handle_summary_generation():
    """Generate and display document summary."""
    if st.session_state.extracted_text:
        if st.button(get_text("generate_summary", st.session_state.interface_language)):
            with st.spinner(get_text("analyzing", st.session_state.interface_language)):
                st.session_state.summary = summarize_text(
                    clean_text(st.session_state.extracted_text),
                    st.session_state.summary_language
                )
        
        if st.session_state.summary:
            st.subheader(get_text("ai_summary", st.session_state.interface_language))
            st.write(st.session_state.summary)
            
            if st.button(get_text("generate_audio", st.session_state.interface_language)):
                with st.spinner(get_text("generating_audio", st.session_state.interface_language)):
                    try:
                        st.session_state.audio_file = text_to_speech(
                            clean_text(st.session_state.summary),
                            st.session_state.summary_language
                        )
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Audio generation failed: {str(e)}")
                        st.error(f"{get_text('error_audio', st.session_state.interface_language)}: {str(e)}")
            
            if st.session_state.audio_file:
                st.subheader(get_text("audio_version", st.session_state.interface_language))
                st.audio(st.session_state.audio_file)

def handle_chat_interaction():
    """Manage chat interface and bot responses."""
    st.markdown("---")
    st.subheader(get_text("chatbot_title", st.session_state.interface_language))
    
    # Display chat history
    for msg in st.session_state.chat_history[1:]:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
            st.write(msg['content'])
            if msg.get("timestamp"):
                st.caption(msg["timestamp"])
    
    # Handle user input
    if prompt := st.chat_input(get_text("chat_placeholder", st.session_state.interface_language)):
        process_user_message(prompt)
    
    # Generate bot response
    if st.session_state.bot_typing:
        generate_bot_response()

def process_user_message(prompt: str):
    """Process user message and trigger bot response."""
    if not st.session_state.last_message or prompt != st.session_state.last_message:
        st.session_state.last_message = prompt
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        st.session_state.bot_typing = True
        st.rerun()

def generate_bot_response():
    """Generate and display bot response."""
    try:
        response = get_chatbot_response(
            st.session_state.last_message,
            st.session_state.extracted_text,
            st.session_state.interface_language
        )
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M")
        })
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": get_text("general_error", st.session_state.interface_language),
            "timestamp": datetime.now().strftime("%H:%M")
        })
    finally:
        st.session_state.bot_typing = False
        st.session_state.last_message = None
        st.rerun()

def run_ui():
    """Main application interface."""
    try:
        initialize_session_state()
        
        st.set_page_config(
            page_title=get_text("title", st.session_state.interface_language),
            page_icon="⚖️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Language selection sidebar
        with st.sidebar:
            prev_lang = st.session_state.interface_language
            st.session_state.interface_language = st.selectbox(
                get_text("language_selector", st.session_state.interface_language),
                options=list(LANGUAGES.keys()),
                index=list(LANGUAGES.keys()).index(st.session_state.interface_language)
            )
            st.session_state.summary_language = st.selectbox(
                get_text("summary_language", st.session_state.interface_language),
                options=list(LANGUAGES.keys()),
                index=list(LANGUAGES.keys()).index(st.session_state.summary_language)
            )
            if prev_lang != st.session_state.interface_language:
                st.rerun()
        
        # Main application
        st.title(get_text("title", st.session_state.interface_language))
        st.markdown(f"*{get_text('subtitle', st.session_state.interface_language)}*")
        
        handle_file_upload()
        handle_summary_generation()
        handle_chat_interaction()
        
        st.markdown(
            f'<div style="text-align: center; margin-top: 2rem;">'
            f'{get_text("footer", st.session_state.interface_language)}'
            f'</div>',
            unsafe_allow_html=True
        )
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}\n{traceback.format_exc()}")
        st.error(get_text("general_error", st.session_state.interface_language))

if __name__ == "__main__":
    run_ui()