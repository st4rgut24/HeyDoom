import httpx
from pathlib import Path
import os
from dotenv import load_dotenv
# No longer strictly need 'from openai import OpenAI' if we use httpx

# --- Configuration (Load from Environment) ---
# Assuming these are correctly loaded via os.getenv()
load_dotenv()

VOICE_ID = os.getenv("VOICE_ID")
MODEL_ID = os.getenv("SPEACHES_MODEL_ID")
BASE_URL = os.getenv("BASE_URL") # e.g., http://192.168.1.42:8000/v1
API_KEY = "sk-speaches-local-key-0123456789"

# client = OpenAI is REMOVED/ignored

def generate_speech(text_input: str, output_filename: str = "output.mp3"):
    """Generates audio using the Speaches API via direct HTTP request."""
    
    # 1. Prepare Request Data
    url = f"{BASE_URL}/audio/speech"
    headers = {
        "Content-Type": "application/json",
        # Use the exact Authorization header that worked with curl
        "Authorization": f"Bearer {API_KEY}"
    }
    json_data = {
        "model": MODEL_ID,
        "voice": VOICE_ID,
        "input": text_input,
        "response_format": "mp3"
    }

    print(f"Generating audio for: {text_input[:30]}...")
    
    try:
        # 2. Make the POST Request using httpx
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=json_data)
        
        # 3. Check for HTTP errors (like 401, 404, 500)
        response.raise_for_status() 

        # 4. Save the response content (the audio file)
        output_path = Path(output_filename)
        output_path.write_bytes(response.content)

    except httpx.HTTPStatusError as e:
        # Catch specific HTTP errors
        error_message = f"HTTP Error {e.response.status_code}. Server Response: {e.response.text}"
        raise ValueError(f"Generate speech failed. {error_message}") from e
    except Exception as e:
        # Catch all other errors (connection, timeout, etc.)
        error_message = f"Connection or I/O error: {e}"
        raise ValueError(f"Generate speech failed. {error_message}") from e

    print(f"Successfully created audio file at: {output_filename}")
    return output_filename
