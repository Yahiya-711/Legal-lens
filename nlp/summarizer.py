import os
import requests
from dotenv import load_dotenv
import logging
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
logger.debug("Current working directory: %s", os.getcwd())
logger.debug("Loading .env file...")
load_dotenv()
logger.debug("Environment variables loaded")

def clean_markdown(text):
    """Remove markdown formatting from text."""
    # Remove bold/italic markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove **
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Remove *
    text = re.sub(r'_(.*?)_', r'\1', text)        # Remove _
    
    # Remove headings
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)  # Remove # at start of lines
    
    # Remove other markdown elements
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Convert [text](url) to text
    text = re.sub(r'`(.*?)`', r'\1', text)           # Remove `code` markers
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Remove code blocks
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Remove multiple blank lines
    text = text.strip()
    
    return text

def summarize_text(text, target_language="English"):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    logger.debug("API Key found: %s", "Yes" if api_key else "No")
    
    if not api_key:
        logger.error("DEEPSEEK_API_KEY not found in environment variables")
        raise ValueError("DeepSeek API key not found in .env file")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an expert legal document summarizer. Create a concise, point-form summary with the most important legal points. Use bullet points (•) for each key point. Keep each point brief and clear. Focus on the main legal implications, rights, obligations, and key terms. Avoid lengthy explanations."},
            {"role": "user", "content": f"Summarize this legal document in {target_language} for a non-lawyer:\n{text[:15000]}"}
        ],
        "temperature": 0.5,
        "max_tokens": 1024,
        "top_p": 0.9
    }

    try:
        logger.debug("Making API request to DeepSeek...")
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        summary = response.json()["choices"][0]["message"]["content"]
        
        # Clean the summary for TTS
        clean_summary = clean_markdown(summary)
        logger.debug("Summary cleaned for TTS")
        
        return summary, clean_summary
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API request failed: {str(e)}")
        raise Exception(f"AI service error: {str(e)}")

def deepseek_chat(messages):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DeepSeek API key not found in .env file")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 1024,
        "top_p": 0.9
    }

    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=90
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
