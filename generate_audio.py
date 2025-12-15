import httpx
from pathlib import Path
import os
from dotenv import load_dotenv
from pydub import AudioSegment
import io # <-- NEW IMPORT: Import the io module

# --- Configuration (Load from Environment) ---
load_dotenv()

BASE_URL = os.getenv("SPEACHES_BASE_URL")
VOICE_ID = os.getenv("VOICE_ID")
MODEL_ID = os.getenv("SPEACHES_MODEL_ID")
API_KEY = "sk-speaches-local-key-0123456789"

# --- NEW CONFIGURATION ---
PRE_SILENCE_MS = 1000 # 1000 milliseconds (1 second) of silence to prepend
PRIME_AUDIO_FILE = "audio/beep-329314.mp3" # <-- PATH TO YOUR PRIMING MP3

def generate_speech(text_input: str, output_filename: str = "audio/output.mp3"):
    """
    Generates audio, prepends a click sound and silence, and saves the file.
    """
    
    # ... (API call setup is unchanged) ...
    url = f"{BASE_URL}/audio/speech"
    headers = {
        "Content-Type": "application/json",
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
        # 1. API Call and Response
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=json_data)
        response.raise_for_status()

        # 2. Load API-Generated Audio
        audio_file_object = io.BytesIO(response.content)
        audio_segment = AudioSegment.from_file(file=audio_file_object, format="mp3")

        # --- AUDIO MANIPULATION CHAIN ---

        # 3. Load the Priming Audio (The "Click")
        prime_path = Path(PRIME_AUDIO_FILE)
        if not prime_path.exists():
             # If the prime file doesn't exist, we fall back to just silence
             print(f"WARNING: Priming file {PRIME_AUDIO_FILE} not found. Using silence only.")
             prime_segment = AudioSegment.silent(duration=10) # 10ms of placeholder silence
        else:
            prime_segment = AudioSegment.from_file(prime_path)

        # 4. Create the main silence buffer
        # Ensure the silence matches the sample rate of the main audio
        silence_segment = AudioSegment.silent(duration=PRE_SILENCE_MS, frame_rate=audio_segment.frame_rate)
        
        # 5. Combine: Prime Click + Silence + Generated Voice
        final_audio = audio_segment
        
        # 6. Export the combined audio to the final file path
        output_path = Path(output_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True) 
        
        final_audio.export(output_path, format="mp3", bitrate="128k")
        
    # ... (error handling is unchanged) ...
    except Exception as e:
        error_message = f"Audio processing or I/O error: {e}"
        raise ValueError(f"Generate speech failed. {error_message}") from e

    print(f"Successfully created audio file (with prime/silence) at: {output_filename}")
    return output_filename
