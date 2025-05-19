import streamlit as st
import logging
import os
import traceback
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from parser_agent.parser import extract_text_from_pdf, extract_text_from_image
from summarizer_agent.summarizer import summarize_text
from tts_agent.tts import text_to_speech
from chatbot_agent.chatbot import get_chatbot_response
from ui_frontend.languages import get_text, LANGUAGES
import requests
import re

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def clean_text(text):
    """Clean text by removing markdown characters and extra whitespace."""
    text = re.sub(r'[*#_~`]', '', text)  # Remove markdown characters
    text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
    return text.strip()

# Initialize session state variables at the module level
if 'interface_language' not in st.session_state:
    st.session_state.interface_language = "English"
if 'summary_language' not in st.session_state:
    st.session_state.summary_language = "English"

def extract_names_roles(text, language="English"):
    """Extract names and their roles from the document text."""
    try:
        cleaned_text = clean_text(text)
        prompt = f"""Extract names and their roles from the following legal document text. 
        Return the results as a list of tuples (name, role).
        Only include names that have clear roles or titles associated with them.
        Format: [("Name1", "Role1"), ("Name2", "Role2"), ...]

        Document text:
        {cleaned_text[:2000]}
        Return only the list of tuples, nothing else."""

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a legal document analyzer. Extract names and roles from legal documents. Be precise and only include information explicitly stated in the document."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("choices") and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                try:
                    names_roles = eval(content)
                    if isinstance(names_roles, list) and all(isinstance(item, tuple) and len(item) == 2 for item in names_roles):
                        if language != "English":
                            translated_roles = []
                            for name, role in names_roles:
                                translation_prompt = f"Translate this legal role to {language}. Return only the translation, no explanations or alternatives: {role}"
                                translation_data = {
                                    "model": "deepseek-chat",
                                    "messages": [
                                        {"role": "system", "content": f"You are a legal translator. Translate legal terms to {language}. Return only the translation."},
                                        {"role": "user", "content": translation_prompt}
                                    ],
                                    "temperature": 0.3
                                }
                                translation_response = requests.post(
                                    "https://api.deepseek.com/v1/chat/completions",
                                    headers=headers,
                                    json=translation_data
                                )
                                if translation_response.status_code == 200:
                                    translated_role = translation_response.json()["choices"][0]["message"]["content"].strip()
                                    translated_roles.append((name, translated_role))
                                else:
                                    translated_roles.append((name, role))
                            return translated_roles
                        return names_roles
                except Exception as e:
                    logging.error(f"Error parsing names and roles: {str(e)}")
                    return None
        return None
    except Exception as e:
        logging.error(f"Error extracting names and roles: {str(e)}")
        return None

def run_ui():
    try:
        st.set_page_config(
            page_title=get_text("title", st.session_state.interface_language),
            page_icon="⚖️",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize session state variables
        if 'summary' not in st.session_state:
            st.session_state.summary = None
        if 'extracted_text' not in st.session_state:
            st.session_state.extracted_text = None
        if 'audio_file' not in st.session_state:
            st.session_state.audio_file = None
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful legal assistant. "
                        "Answer questions about legal documents and law in simple, brief, and concise terms. "
                        "Keep your responses short and to the point, unless the user asks for more detail."
                    )
                },
                {
                    "role": "assistant",
                    "content": "👋 Hello! I'm your legal assistant. I can help you analyze legal documents and answer your legal questions. How can I assist you today?",
                    "timestamp": datetime.now().strftime("%H:%M")
                }
            ]
        if 'bot_typing' not in st.session_state:
            st.session_state.bot_typing = False
        if 'last_message' not in st.session_state:
            st.session_state.last_message = None

        with st.sidebar:
            prev_interface_language = st.session_state.interface_language

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

            if prev_interface_language != st.session_state.interface_language:
                st.rerun()

        title = get_text("title", st.session_state.interface_language)
        subtitle = get_text("subtitle", st.session_state.interface_language)
        st.markdown(f'<h1 class="title-text">{title}</h1>', unsafe_allow_html=True)
        st.markdown(f'<p class="subtitle-text">{subtitle}</p>', unsafe_allow_html=True)

        with st.container():
            upload_title = get_text("upload_title", st.session_state.interface_language)
            upload_help = get_text("upload_help", st.session_state.interface_language)

            uploaded_file = st.file_uploader(
                label=upload_title,
                type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
                help=upload_help,
                key=f"file_uploader_{st.session_state.interface_language}"
            )

            if uploaded_file:
                try:
                    with st.spinner(get_text("extracting_text", st.session_state.interface_language)):
                        if uploaded_file.type == "application/pdf":
                            st.session_state.extracted_text = extract_text_from_pdf(uploaded_file)
                        else:
                            st.session_state.extracted_text = extract_text_from_image(uploaded_file)

                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"### {get_text('document_preview', st.session_state.interface_language)}")
                        if st.session_state.extracted_text:
                            st.text_area("", st.session_state.extracted_text, height=400)

                    with col2:
                        st.markdown(f"### {get_text('key_people', st.session_state.interface_language)}")
                        if st.button(get_text('extract_roles', st.session_state.interface_language)):
                            with st.spinner(get_text('analyzing', st.session_state.interface_language)):
                                names_roles = extract_names_roles(st.session_state.extracted_text, st.session_state.summary_language)
                                if names_roles:
                                    for name, role in names_roles:
                                        st.markdown(f"**{name}** - {role}")
                                else:
                                    st.info(get_text('no_roles_found', st.session_state.interface_language))

                except Exception as e:
                    logger.error(f"Error processing file: {str(e)}")
                    logger.error(traceback.format_exc())
                    st.error(f"{get_text('error_processing', st.session_state.interface_language)} {str(e)}")

        if uploaded_file:
            if st.button(get_text("generate_summary", st.session_state.interface_language)):
                with st.spinner(get_text("analyzing", st.session_state.interface_language)):
                    cleaned_text = clean_text(st.session_state.extracted_text)
                    st.session_state.summary = summarize_text(cleaned_text, st.session_state.summary_language)

            if st.session_state.summary:
                st.subheader(get_text("ai_summary", st.session_state.interface_language))
                st.write(st.session_state.summary)

                if st.button(get_text("generate_audio", st.session_state.interface_language)):
                    with st.spinner(get_text("generating_audio", st.session_state.interface_language)):
                        try:
                            cleaned_summary = clean_text(st.session_state.summary)
                            audio_file = text_to_speech(cleaned_summary, st.session_state.summary_language)
                            st.session_state.audio_file = audio_file
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Audio generation failed: {str(e)}")
                            st.error(f"{get_text('error_audio', st.session_state.interface_language)} {str(e)}")
                            st.info(get_text("read_summary", st.session_state.interface_language))

                if st.session_state.audio_file:
                    st.subheader(get_text("audio_version", st.session_state.interface_language))
                    st.audio(st.session_state.audio_file)

        st.markdown(f'<div class="footer">{get_text("footer", st.session_state.interface_language)}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f'<div class="section-header">{get_text("chatbot_title", st.session_state.interface_language)}</div>', unsafe_allow_html=True)

        # Display chat history
        for msg in st.session_state.chat_history[1:]:  # Skip system message
            timestamp = msg.get("timestamp", datetime.now().strftime("%H:%M"))
            if msg["role"] == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.write(msg['content'])
                    st.caption(timestamp)
            elif msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(msg['content'])
                    st.caption(timestamp)

        # Typing animation
        if st.session_state.get("bot_typing", False):
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown("_Bot is typing..._")

        # Chat input
        if prompt := st.chat_input(get_text("chat_placeholder", st.session_state.interface_language)):
            # Check if this is a new message
            if prompt != st.session_state.last_message:
                st.session_state.last_message = prompt
                
                # Add user message to chat history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": prompt,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                # Set typing state
                st.session_state.bot_typing = True
                st.rerun()
            
        # Generate response if bot is typing
        if st.session_state.get("bot_typing", False):
            response = get_chatbot_response(prompt, st.session_state.extracted_text, st.session_state.interface_language)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            st.session_state.bot_typing = False
            st.rerun()

        st.markdown("""
            <style>
                .stChatMessage {
                    padding: 1rem;
                    border-radius: 10px;
                    margin: 0.5rem 0;
                }
                .stChatMessage[data-testid="stChatMessage"] {
                    background-color: #161b22;
                    border: 1px solid #30363d;
                }
                .stChatMessage[data-testid="stChatMessage"]:hover {
                    background-color: #1c2128;
                }
                .stChatMessageContent {
                    color: #e6edf3;
                }
                .stChatMessageAvatar {
                    background-color: #58a6ff;
                }
                .info-box {
                    background-color: #161b22;
                    border: 1px solid #30363d;
                    border-radius: 10px;
                    padding: 1rem;
                    margin: 0.5rem 0;
                    color: #e6edf3;
                }
                .info-box:hover {
                    background-color: #1c2128;
                }
            </style>
        """, unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"⚠️ Critical error: {str(e)}")
        st.error("Please check the logs for more details.")

if __name__ == "__main__":
    run_ui()