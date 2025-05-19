import streamlit as st
import logging
import os
import traceback
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    from parser_agent.parser import extract_text_from_pdf, extract_text
    from nlp.summarizer import summarize_text, deepseek_chat
    from tts_agent.tts import text_to_speech

    def run_ui():
        st.set_page_config(
            page_title="Legal Lens",
            page_icon="⚖️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Styling the UI 
        st.markdown("""
        <style>
        .main {
            background-color: #0d1117;
            color: #e6edf3;
            padding: 2rem;
        }

        .title-text {
            font-size: 2.5rem;
            font-weight: 700;
            color: #58a6ff;
            text-align: center;
        }

        .subtitle-text {
            font-size: 1.2rem;
            color: #c9d1d9;
            text-align: center;
            margin-bottom: 2rem;
        }

        .card {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
            margin: 1rem 0;
        }

        .card:hover {
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.4);
        }

        .section-header {
            color: #79c0ff;
            font-size: 1.4rem;
            font-weight: 600;
            border-bottom: 2px solid #30363d;
            padding-bottom: 0.3rem;
            margin-top: 1.5rem;
        }

        .preview-text, .summary-box {
            background-color: #0d1117;
            border: 1px solid #30363d;
            color: #e6edf3;
            padding: 1rem;
            border-radius: 10px;
            margin-top: 1rem;
            font-size: 1rem;
        }

        .stButton>button {
            background-color: #238636;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 2rem;
            font-size: 1rem;
            font-weight: 600;
            border: none;
        }

        .stButton>button:hover {
            background-color: #2ea043;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(255, 255, 255, 0.1);
        }

        .stFileUploader {
            background-color: #0d1117;
            border: 2px dashed #58a6ff;
            border-radius: 10px;
            padding: 1.5rem;
        }

        .stFileUploader:hover {
            background-color: #161b22;
        }

        .footer {
            text-align: center;
            color: #8b949e;
            font-size: 0.9rem;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #30363d;
        }

        .stMarkdown, .stMarkdown p {
            color: #e6edf3;
        }

        .stAudio {
            background-color: #161b22;
            padding: 1rem;
            border-radius: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Title
        st.markdown('<h1 class="title-text">⚖️ Legal Lens</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle-text">AI-Powered Legal Document Summarizer</p>', unsafe_allow_html=True)

        # Main Layout
        with st.container():
            # File uploader and language selection 
            uploaded_file = st.file_uploader(
                "📄 Upload Legal Document",
                type=["pdf", "png", "jpg", "jpeg", "tiff", "bmp"],
                help="Upload a PDF or image file (PNG, JPG, JPEG, TIFF, BMP). Maximum file size: 50MB"
            )
            target_language = st.selectbox(
                "🌐 Summary Language",
                [
                    "English", "Urdu", "Hindi", "Arabic", "French", "Spanish",
                    "Telugu", "Kannada", "Tamil", "Bengali", "Gujarati", "Marathi", "Malayalam", "Punjabi"
                ],
                index=0
            )

            if uploaded_file:
                try:
                    with st.spinner("📥 Extracting text from document..."):
                        text = extract_text(uploaded_file)
                        logger.info(f"Document processed: {uploaded_file.name}")

                        st.markdown('<div class="section-header">📄 Document Preview</div>', unsafe_allow_html=True)
                        preview_text = text[:500] + ("..." if len(text) > 500 else "")
                        st.markdown(f'<div class="preview-text">{preview_text}</div>', unsafe_allow_html=True)
                except Exception as e:
                    logger.error(f"Error processing file: {str(e)}")
                    logger.error(traceback.format_exc())
                    st.error(f"⚠️ Error processing file: {str(e)}")

        # Generating Summary and Audio
        if uploaded_file:
            if st.button("🔍 Generate Summary", type="primary"):
                with st.spinner("🤖 Analyzing document..."):
                    summary, clean_summary = summarize_text(text, target_language)
                    logger.info(f"Summary generated for {target_language}")
                    
                    # Store both formatted and clean summary in session state
                    st.session_state.summary = clean_summary
                    st.session_state.formatted_summary = summary
                    st.session_state.target_language = target_language

            # Displaying summary if it exists in session state
            if "formatted_summary" in st.session_state:
                st.markdown('<div class="section-header">📝 AI Summary</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="summary-box">{st.session_state.formatted_summary}</div>', unsafe_allow_html=True)

            # Audio generation button 
            if "summary" in st.session_state:
                if st.button("🔊 Generate Audio Version", type="secondary"):
                    with st.spinner("🔊 Generating audio version..."):
                        try:
                            audio_dir = "audio_output"
                            Path(audio_dir).mkdir(exist_ok=True)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            audio_path = os.path.join(audio_dir, f"summary_{timestamp}.mp3")

                            lang_code = {
                                "English": "en",
                                "Urdu": "ur",
                                "Hindi": "hi",
                                "Arabic": "ar",
                                "French": "fr",
                                "Spanish": "es",
                                "Telugu": "te",
                                "Kannada": "kn",
                                "Tamil": "ta",
                                "Bengali": "bn",
                                "Gujarati": "gu",
                                "Marathi": "mr",
                                "Malayalam": "ml",
                                "Punjabi": "pa"
                            }[st.session_state.target_language]
                            audio_path = text_to_speech(st.session_state.summary, lang=lang_code, output_path=audio_path)

                            st.markdown('<div class="section-header">🎧 Audio Version</div>', unsafe_allow_html=True)
                            st.audio(audio_path, format="audio/mp3")
                            
                            logger.info(f"Audio generated: {audio_path}")
                        except Exception as e:
                            logger.error(f"Audio generation failed: {str(e)}")
                            st.error(f"⚠️ Audio generation failed: {str(e)}")
                            st.info("You can still read the summary above.")

        # Footer
        st.markdown('<div class="footer">Made with ❤️ by Legal Lens AI Team</div>', unsafe_allow_html=True)

        # --- Chatbot Section ---
        st.markdown("---")
        st.markdown('<div class="section-header">💬 Legal Lens Chatbot</div>', unsafe_allow_html=True)

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful legal assistant. "
                        "Answer questions about legal documents and law in simple, brief, and concise terms. "
                        "Keep your responses short and to the point, unless the user asks for more detail."
                    )
                }
            ]
        if "bot_typing" not in st.session_state:
            st.session_state.bot_typing = False

        # Display chat history as chat bubbles with avatars and timestamps
        for msg in st.session_state.chat_history[1:]:
            timestamp = msg.get("timestamp", datetime.now().strftime("%H:%M"))
            if msg["role"] == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(f"{msg['content']}  \n<span style='font-size:0.8em;color:#888;'>{timestamp}</span>", unsafe_allow_html=True)
            elif msg["role"] == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(f"{msg['content']}  \n<span style='font-size:0.8em;color:#888;'>{timestamp}</span>", unsafe_allow_html=True)

        # Typing animation
        if st.session_state.get("bot_typing", False):
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown("_Bot is typing..._")

        # Chat input at the bottom
        user_input = st.chat_input("Ask the Legal Lens Chatbot anything about your document or legal terms:")

        if user_input:
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            st.session_state.bot_typing = True
            st.rerun()

        if st.session_state.get("bot_typing", False):
            time.sleep(1)  # Simulate typing delay
            bot_reply = deepseek_chat(st.session_state.chat_history)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": bot_reply,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            st.session_state.bot_typing = False
            st.rerun()

    if __name__ == "__main__":
        run_ui()

except Exception as e:
    logger.error(f"Critical error: {str(e)}")
    logger.error(traceback.format_exc())
    st.error(f"⚠️ Critical error: {str(e)}")
    st.error("Please check the logs for more details.")
