import sys
import time
from pvrecorder import PvRecorder
from pvporcupine import Porcupine

# --- CONFIGURATION ---
# !!! IMPORTANT: Replace 'YOUR_ACCESS_KEY_HERE' with your actual Picovoice AccessKey
ACCESS_KEY = 'lKeGfU6LBZ6308zlEtnVtqHFz5DWOiHeoPc5oiiG6YzWJ2yVUUXxKQ=='

# Choose your desired keyword. 'ALEXA' is an example.
# Use BuiltInKeyword.<KEYWORD_NAME> for built-in words.
# For custom words, provide the path to the .ppn file (e.g., keyword_file_paths=['/path/to/my_keyword.ppn'])
# KEYWORD_TO_DETECT = BuiltInKeyword.ALEXA 
# ---------------------

def run_detector():
    """
    Initializes Porcupine and PvRecorder, and runs the continuous detection loop.
    """
    porcupine = None
    recorder = None
    
    try:
        # 1. Initialize Porcupine Engine
        print("Initializing Porcupine engine...")
        porcupine = Porcupine(
            access_key=ACCESS_KEY,
            keyword_paths=["/home/yomama/code/Converse/Hey-Doom_en_raspberry-pi_v3_0_0.ppn"],
	    library_path="/home/yomama/code/venv/lib/python3.12/site-packages/pvporcupine/lib/raspberry-pi/cortex-a76-aarch64/libpv_porcupine.so",
	    model_path="/home/yomama/code/venv/lib/python3.12/site-packages/pvporcupine/lib/common/porcupine_params.pv",
	    sensitivities=[0.5]
        )

        # 2. Initialize Audio Recorder (PvRecorder)
        # Porcupine requires a specific frame length and sample rate.
        print(f"Initializing PvRecorder with frame length: {porcupine.frame_length} and sample rate: {porcupine.sample_rate}")
        
        # NOTE: To list available input devices, you can use:
        # for i, device in enumerate(PvRecorder.get_available_devices()):
        #     print(f"Device {i}: {device}")
        
        # We use device_index=-1 to let PvRecorder automatically select the default input device.
        recorder = PvRecorder(
             frame_length=porcupine.frame_length,
             device_index=-1
        )
        
        recorder.start()
        print(f"\nListening for 'Hey DOOM!'...")
        
        # 3. Main Detection Loop
        while True:
            # Read a frame of audio from the microphone
            pcm = recorder.read()
            
            # Pass the audio frame to the Porcupine engine
            keyword_index = porcupine.process(pcm)
            
            # Check if a keyword was detected (index >= 0)
            if keyword_index >= 0:
                print("-" * 30)
                print(f"Keyword Detected! Time: {time.strftime('%H:%M:%S')}")
                print("-" * 30)
                
                # --- YOUR ACTION GOES HERE ---
                # This is where you would call your subsequent service, 
                # play a beep, or start a full transcription service.
                # Example:
                # play_confirmation_sound()
                # start_full_voice_assistant()
                pass
                
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        # If the script fails, systemd will attempt to restart it.
        
    finally:
        # 4. Clean up resources
        if recorder is not None:
            recorder.stop()
            recorder.delete()
        if porcupine is not None:
            porcupine.delete()
        
        print("Resources cleaned up. Detector stopped.")

if __name__ == '__main__':
    run_detector()
