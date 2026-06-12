import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import time
import os
from gtts import gTTS # Used here for the *testing output* demonstration
from pydub import AudioSegment # For audio processing if needed

# --- Configuration ---
SAMPLE_RATE = 44100  # Standard audio sample rate
CHANNELS = 1         # Mono recording
RECORDING_FILENAME = "user_voice_sample.wav"
OUTPUT_TEST_FILENAME = "cloned_voice_test.mp3"

def record_user_voice(duration_seconds=5):
    """Records the user's voice for a specified duration."""
    print("🎙️ Starting recording in 3 seconds...")
    time.sleep(3)
    
    print(f"🎤 Recording for {duration_seconds} seconds...")
    recording = sd.rec(int(duration_seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16')
    sd.wait()  # Wait until recording is finished
    
    # Save the recording
    wav.write(RECORDING_FILENAME, SAMPLE_RATE, recording)
    print(f"✅ Recording finished and saved as **{RECORDING_FILENAME}**")

def test_text_input(text_to_speak):
    """
    Simulates the text-to-speech conversion.
    
    NOTE: For a *true* voice clone, this step would be replaced by calling 
    your trained deep learning model (e.g., Tacotron 2 + Hifi-GAN) 
    which has learned the voice characteristics from your recorded samples.
    
    Here, we use gTTS for a functional demonstration of text-to-audio.
    """
    print(f"\n🧠 Generating audio for text: '{text_to_speak}'...")
    
    try:
        # Create a gTTS object
        tts = gTTS(text=text_to_speak, lang='en')
        
        # Save the audio file
        tts.save(OUTPUT_TEST_FILENAME)
        
        print(f"✅ Test audio generated and saved as **{OUTPUT_TEST_FILENAME}**")
        print("▶️ You can now play the file to hear the output.")
        
    except Exception as e:
        print(f"❌ An error occurred during text-to-speech generation: {e}")


def main_menu():
    """Main menu loop for the voice cloning tool."""
    print("\n--- 🗣️ Realistic Voice Cloner Tool ---")
    
    # Check if a sample exists
    if os.path.exists(RECORDING_FILENAME):
        print(f"Current voice sample file: **{RECORDING_FILENAME}** (Ready for use in training)")
    else:
        print("No voice sample found. Please record one first.")
        
    print("\nSelect an option:")
    print("1. **Record** new voice sample (5 seconds)")
    print("2. **Test** voice cloning with text input (Simulated)")
    print("3. Exit")
    
    choice = input("Enter your choice (1/2/3): ")
    
    if choice == '1':
        record_user_voice()
        # After recording, you would proceed to the complex ML training step
        print("\n--- Next Step (Conceptual) ---")
        print("To create a clone, you now need a large dataset (hours of recordings) and an ML model.")
        print("The recorded sample is the *input data* for the training process.")
        main_menu()

    elif choice == '2':
        text_input = input("Enter the text you want the cloned voice to speak: ")
        if text_input.strip():
            test_text_input(text_input)
        else:
            print("Text input cannot be empty.")
        main_menu()
        
    elif choice == '3':
        print("Goodbye! Happy coding.")
        return
        
    else:
        print("Invalid choice. Please try again.")
        main_menu()

if __name__ == "__main__":
    # Ensure necessary ML-related packages are installed for a *real* project
    print("Ensure you have installed: sounddevice, numpy, scipy, gTTS, pydub")
    print("   (e.g., pip install sounddevice numpy scipy gTTS pydub)")
    main_menu()