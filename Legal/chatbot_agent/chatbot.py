import os
from dotenv import load_dotenv
import requests
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_chatbot_response(
    user_input: str,
    document_text: Optional[str] = None,
    language: str = "English"
) -> str:
    """
    Get a response from the chatbot with improved error handling and reliability.
    
    Args:
        user_input: The user's question or input
        document_text: Optional document context (first 2000 chars will be used)
        language: The language for the response
        
    Returns:
        The chatbot's response or an error message in the specified language
    """
    try:
        # Validate API key
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            logger.error("API key not configured")
            return "Service configuration error. Please contact support."
        
        # Prepare messages with language consideration
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a legal assistant. Provide concise answers in {language}. "
                    "For legal questions, always:\n"
                    "1. State applicable laws\n"
                    "2. Mention jurisdiction variations\n"
                    "3. Keep responses under 300 words\n"
                    "4. Never say you can't answer legal questions"
                )
            }
        ]
        
        # Add document context if available
        if document_text:
            messages.append({
                "role": "system", 
                "content": f"Document context:\n{document_text[:2000]}"
            })
            
        messages.append({"role": "user", "content": user_input})

        # Make API request with timeout
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30  # 30-second timeout
        )

        # Validate response
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return "The AI service is currently unavailable. Please try again later."
            
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Malformed API response: {str(e)}")
            return "The AI response couldn't be processed. Please rephrase your question."

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {str(e)}")
        return "Network connection issue. Please check your internet."
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return "An unexpected error occurred. We're working on it!"