import os
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

def summarize_text(text, language="English"):
    """
    Generate a concise summary of the input text in the specified language.
    
    Args:
        text (str): The text to summarize
        language (str): The language for the summary (default: "English")
    
    Returns:
        str: The generated summary
    """
    try:
        # Get API key from environment variable
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return "Error: API key not found. Please check your environment variables."

        # Prepare the prompt
        prompt = f"""Please provide a concise summary of the following legal text in {language}. 
Focus on key points, legal implications, and important details. 
Format the summary in bullet points for better readability.

Text to summarize:
{text}"""

        # Make API request to DeepSeek
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a legal document summarizer. Provide clear, concise summaries in the requested language."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Error: {str(e)}" 