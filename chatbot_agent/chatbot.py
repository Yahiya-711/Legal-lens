import os
from dotenv import load_dotenv
import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_chatbot_response(user_input, document_text=None, language="English"):
    """
    Get a response from the chatbot based on user input and optional document context.
    
    Args:
        user_input (str): The user's question or input
        document_text (str, optional): The text of the document being analyzed
        language (str): The language for the response (default: "English")
    
    Returns:
        str: The chatbot's response
    """
    try:
        # Prepare the system message with specific instructions
        system_message = """You are a knowledgeable legal assistant. You MUST:
1. ALWAYS provide a direct answer to legal questions
2. NEVER respond with "I cannot offer a response" or similar phrases
3. For questions about crimes and punishments:
   - ALWAYS state the standard punishment range (e.g., "Murder typically carries a sentence of 15-25 years to life imprisonment")
   - ALWAYS mention that exact penalties vary by jurisdiction
   - ALWAYS explain any relevant legal terms
4. Use simple, clear language
5. Be direct and concise
6. Respond in the specified language
7. If unsure about specific details, provide general information and note that it varies by jurisdiction"""

        # Prepare the prompt with document context if available
        if document_text:
            # Split document into chunks if it's too long
            max_context_length = 2000
            document_chunk = document_text[:max_context_length]
            
            prompt = f"""Context from legal document:
{document_chunk}

User question: {user_input}

Instructions:
1. First, determine if the answer can be found in the document
2. If yes, provide a clear answer with relevant quotes or references
3. If no, provide a direct legal answer based on your knowledge
4. Keep the response concise and focused
5. Respond in {language}"""

            logger.debug(f"Using document context for response. Context length: {len(document_chunk)}")
        else:
            prompt = f"""User question: {user_input}

Instructions:
1. You MUST provide a direct legal answer
2. For questions about crimes/punishments:
   - State the standard punishment range
   - Note that penalties vary by jurisdiction
   - Explain any relevant legal terms
3. Keep the response focused and relevant
4. Respond in {language}"""

            logger.debug("No document context available for response")

        # Get API key from environment variable
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            logger.error("API key not found in environment variables")
            return "Error: API key not found. Please check your environment variables."

        # Make API request to DeepSeek
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        logger.debug(f"Sending request to DeepSeek API with prompt: {prompt[:100]}...")

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            response_text = response.json()["choices"][0]["message"]["content"]
            logger.debug(f"Received response from API: {response_text[:100]}...")
            return response_text
        else:
            error_msg = f"Error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return error_msg

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return error_msg 