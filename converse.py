import pyaudio
import pvporcupine
import struct
import numpy as np
import collections
from webrtcvad import Vad
import time
import sys
from faster_whisper import WhisperModel # <-- NEW IMPORT

# --- CONFIGURATION ---
# !!! IMPORTANT: Replace 'YOUR_ACCESS_KEY_HERE' with your actual Picovoice AccessKey
ACCESS_KEY = 'lKeGfU6LBZ6308zlEtnVtqHFz5DWOiHeoPc5oiiG6YzWJ2yVUUXxKQ=='
WAKE_WORD_PATH = "/home/yomama/code/Converse/Hey-Doom_en_raspberry-pi_v3_0_0.ppn"

# --- Whisper Configuration ---
# 'tiny.en' is recommended for the best balance of speed and accuracy on the Pi 5.
WHISPER_MODEL_SIZE = "tiny.en" 
# Use 'cpu' device for Raspberry Pi 5
DEVICE = "cpu"
COMPUTE_TYPE = "int8" # Use INT8 quantization for maximum speed on CPU
# ---------------------

# --- Audio and VAD Configuration (from previous script) ---
SAMPLE_RATE = 16000         
CHANNELS = 1
FORMAT = pyaudio.paInt16

VAD_AGGRESSIVENESS = 3       
VAD_FRAME_DURATION_MS = 30   
VAD_FRAME_SIZE = int(SAMPLE_RATE * VAD_FRAME_DURATION_MS / 1000)

SILENCE_TIMEOUT_FRAMES = 50 
SPEECH_START_FRAMES = 10    
# ---------------------

# Initialize the Whisper model globally for efficiency
# This loading process is slow, so we only do it once at startup.
try:
    print(f"Loading Whisper model '{WHISPER_MODEL_SIZE}' for CPU...")
    # Setting local_files_only=False ensures it downloads the model if not present.
    WHISPER_AHOY = WhisperModel(WHISPER_MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    print("Whisper model loaded successfully.")
except Exception as e:
    print(f"ERROR: Failed to load faster-whisper model. Check your installation/network. Details: {e}", file=sys.stderr)
    WHISPER_AHOY = None


# --- Functions ---

def transcribe_command(audio_data):
    """
    Transcribes the recorded audio data using the faster-whisper model.
    """
    if WHISPER_AHOY is None:
        return "ERROR: Transcription engine not initialized."
    
    print("\n[STT] 🎙️ Processing recorded audio with Whisper...")
    
    # 1. Convert raw audio bytes (int16) to NumPy float array (required by Whisper)
    # The audio data is a flat sequence of int16 PCM samples at 16000Hz.
    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

    # 2. Transcribe the audio
    try:
        segments, info = WHISPER_AHOY.transcribe(
            audio_np, 
            beam_size=5, 
            language="en" # Force English for tiny.en model
        )
        
        full_text = []
        for segment in segments:
            full_text.append(segment.text)
            
        transcription = " ".join(full_text).strip()
        
        if not transcription:
             return "[ASSISTANT] Could not recognize speech."

        return transcription
    
    except Exception as e:
        print(f"[STT ERROR] Transcription failed: {e}", file=sys.stderr)
        return "Transcription failed due to an engine error."


# --- Helper Functions (Record VAD and Main Detector remain the same) ---

def record_audio_vad(pa_instance, vad_instance, sample_rate, frame_size):
    """
    Records audio using VAD to automatically stop when speech ends.
    """
    # Open a new stream optimized for VAD frame size
    vad_stream = pa_instance.open(
        rate=sample_rate,
        channels=CHANNELS,
        format=FORMAT,
        input=True,
        frames_per_buffer=frame_size,
    )
    
    print("[VAD] Listening for command... (Speak now)")
    
    ring_buffer = collections.deque(maxlen=SILENCE_TIMEOUT_FRAMES)
    command_frames = []
    is_speaking = False
    
    while True:
        try:
            pcm_data = vad_stream.read(frame_size, exception_on_overflow=False)
        except IOError as e:
            print(f"[ERROR] PyAudio read error: {e}", file=sys.stderr)
            continue

        is_active = vad_instance.is_speech(pcm_data, sample_rate)

        if not is_speaking:
            ring_buffer.append(is_active)
            if sum(ring_buffer) >= SPEECH_START_FRAMES:
                is_speaking = True
                print("[VAD] 🗣️ Speech detected. Recording...")
                ring_buffer.clear()
                command_frames.append(pcm_data)
        
        else:
            command_frames.append(pcm_data)
            ring_buffer.append(is_active)
                
            if len(ring_buffer) == SILENCE_TIMEOUT_FRAMES and sum(ring_buffer) == 0:
                print("[VAD] 🤫 Silence detected. Stopping recording.")
                break 

    vad_stream.stop_stream()
    vad_stream.close()
    
    return b''.join(command_frames)


def run_detector():
    """
    Main function for the Porcupine Wake Word detection loop.
    """
    # ... [Porcupine, PyAudio, VAD Initialization code is the same] ...
    porcupine = None
    pa = None
    mic_stream = None
    vad = None
    
    try:
        # 1. Initialize Porcupine Engine
        print("Initializing Porcupine engine...")
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keyword_paths=[WAKE_WORD_PATH],
            sensitivities=[0.5] 
        )
        
        # 2. Initialize VAD
        vad = Vad(VAD_AGGRESSIVENESS)

        # 3. Initialize PyAudio
        pa = pyaudio.PyAudio()

        porcupine_frame_size = porcupine.frame_length
        mic_stream = pa.open(
            rate=SAMPLE_RATE,
            channels=CHANNELS,
            format=FORMAT,
            input=True,
            frames_per_buffer=porcupine_frame_size,
        )
        
        print(f"\n🤖 Listening for 'Hey DOOM!'...")
        
        # 4. Main Detection Loop
        while True:
            pcm_bytes = mic_stream.read(porcupine_frame_size, exception_on_overflow=False)
            pcm_shorts = struct.unpack_from("h" * porcupine_frame_size, pcm_bytes)
            keyword_index = porcupine.process(pcm_shorts)
            
            if keyword_index >= 0:
                print("\n" + "=" * 30)
                print(f"🎉 WAKE WORD DETECTED! Time: {time.strftime('%H:%M:%S')}")
                print("=" * 30)
                
                # Close the Porcupine-optimized stream before starting VAD
                mic_stream.close()
                mic_stream.terminate()
                
                # --- ACTION: Record Command with VAD ---
                # Re-initialize PyAudio instance before opening VAD stream
                pa = pyaudio.PyAudio() 
                recorded_command_bytes = record_audio_vad(pa, vad, SAMPLE_RATE, VAD_FRAME_SIZE)
                
                # --- ACTION: Transcribe and Process ---
                if recorded_command_bytes:
                    transcribed_text = transcribe_command(recorded_command_bytes)
                    print(f"[ASSISTANT] ✅ Transcribed: \"{transcribed_text}\"")
                    # *** ADD YOUR COMMAND FULFILLMENT LOGIC HERE ***
                else:
                    print("[ASSISTANT] ❌ Command not detected.")
                
                # Re-initialize PyAudio and stream for the main loop
                pa = pyaudio.PyAudio()
                mic_stream = pa.open(
                    rate=SAMPLE_RATE,
                    channels=CHANNELS,
                    format=FORMAT,
                    input=True,
                    frames_per_buffer=porcupine_frame_size,
                )
                
                print(f"\n🤖 Listening for 'Hey DOOM!'...")
                
    except pvporcupine.PorcupineInvalidArgumentError as e:
        print(f"ERROR: Invalid argument to Porcupine. Check Access Key and keyword path. Details: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        
    finally:
        # 4. Clean up resources
        if mic_stream is not None and mic_stream.is_active():
            mic_stream.stop_stream()
            mic_stream.close()
        if pa is not None:
            pa.terminate()
        if porcupine is not None:
            porcupine.delete()
        print("Resources cleaned up. Detector stopped.")


if __name__ == '__main__':
    run_detector()
