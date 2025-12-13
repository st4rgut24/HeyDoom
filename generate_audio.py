import httpx
from pathlib import Path
import os
from dotenv import load_dotenv
from pydub import AudioSegment
import io # <-- NEW IMPORT: Import the io module

# --- Configuration (Load from Environment) ---
load_dotenv()

VOICE_ID = os.getenv("VOICE_ID")
MODEL_ID = os.getenv("SPEACHES_MODEL_ID")
BASE_URL = os.getenv("BASE_URL")
API_KEY = "sk-speaches-local-key-0123456789"

# --- NEW CONFIGURATION ---
PRE_SILENCE_MS = 1000 # 1000 milliseconds (1 second) of silence to prepend

def generate_speech(text_input: str, output_filename: str = "audio/output.mp3"):
    """
    Generates audio using the Speaches API via direct HTTP request, 
    then prepends silence to the audio file to prevent cutoff during playback.
    """
    
    # 1. Prepare Request Data
    url = f"{BASE_URL}/audio/speech"
    # ... (headers and json_data setup is unchanged) ...
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
        # 2. Make the POST Request using httpx and get the raw MP3 data
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=json_data)
        
        response.raise_for_status()

        # --- AUDIO MANIPULATION AND SAVE ---
        
        # 3. Create a file-like object from the raw binary content
        audio_file_object = io.BytesIO(response.content)

        # 4. Load the audio segment from the file-like object
        audio_segment = AudioSegment.from_file(
            file=audio_file_object, # <-- PASSING THE io.BytesIO OBJECT HERE
            format="mp3"
        )

        # 5. Create and prepend the silence segment
        silence = AudioSegment.silent(duration=PRE_SILENCE_MS, frame_rate=audio_segment.frame_rate)
        final_audio = silence + audio_segment
        
        # 6. Export the combined audio to the final file path
        output_path = Path(output_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True) 
        
        final_audio.export(output_path, format="mp3", bitrate="128k")
        
    except httpx.HTTPStatusError as e:
        error_message = f"HTTP Error {e.response.status_code}. Server Response: {e.response.text}"
        raise ValueError(f"Generate speech failed. {error_message}") from e
    except Exception as e:
        # Catch pydub/ffmpeg errors, connection errors, etc.
        error_message = f"Audio processing or I/O error: {e}"
        raise ValueError(f"Generate speech failed. {error_message}") from e

    print(f"Successfully created audio file (with silence) at: {output_filename}")
    return output_filename
