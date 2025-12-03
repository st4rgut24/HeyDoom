# --- generate_audio.py ---

import httpx
from pathlib import Path
from openai import OpenAI
import os

# --- Configuration (Keep these at the top) ---
BASE_URL = "http://192.168.1.42:8000/v1" 
# ... (Other configuration like MODEL_ID, VOICE_ID) ...
client = OpenAI(
    base_url=BASE_URL,
    api_key="sk-speaches-api-key"
)

def generate_speech(text_input: str, output_filename: str = "output.mp3"):
    """Generates audio using the Speaches API and saves it to a file."""
    
    # 1. Generate the speech from the provided text
    print(f"Generating audio for: {text_input[:30]}...")
    try:
        response = client.audio.speech.create(
            model=MODEL_ID,
            voice=VOICE_ID,
            input=text_input,
        )
    except Exception as e:
        print(f"Error during API call: {e}")
        return None

    # 2. Save the response stream to the specified file
    response.stream_to_file(output_filename)
    print(f"Successfully created audio file at: {output_filename}")
    return output_filename # Returns the filename if successful

# This block ensures the script only runs the function if it's executed directly (not imported)
if __name__ == "__main__":
    # Example of running the function directly for testing
    generate_speech("Testing the function directly.", "test_direct.mp3")
