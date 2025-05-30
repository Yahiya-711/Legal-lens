from gtts import gTTS
import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Language name to ISO code mapping
LANGUAGE_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Marathi": "mr",
    "Bengali": "bn",
    "Tamil": "ta",
    "Spanish": "es"
}

def text_to_speech(text, lang="English", output_path="summary.mp3"):
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Converting text to speech (language: {lang})")
        logger.debug(f"Output path: {output_path}")
        
        # Ensure text is not empty
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Convert language name to language code
        lang_code = LANGUAGE_CODES.get(lang, "en")  # Default to English if language not found
        logger.debug(f"Using language code: {lang_code}")
            
        # Create TTS object
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        # Save the audio file
        logger.debug("Saving audio file...")
        tts.save(output_path)
            
        # Verify the file was created
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Audio file was not created at {output_path}")
            
        logger.info(f"Audio file successfully created at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"TTS conversion failed: {str(e)}")
        logger.error(f"Error details: {type(e).__name__}")
        raise Exception(f"Audio generation failed: {str(e)}")
