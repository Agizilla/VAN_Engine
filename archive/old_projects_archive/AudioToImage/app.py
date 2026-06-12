import os
import numpy as np
import soundfile as sf
from PIL import Image

class AudioVisualizer:
    def __init__(self):
        self.current_image = None
        self.last_wav = None

    def list_wavs(self):
        wavs = [f for f in os.listdir('.') if f.endswith('.wav')]
        if not wavs:
            print("\n❌ No .wav files found in root folder.")
            return None
        
        print("\n--- Available Audio Files ---")
        for i, f in enumerate(wavs, 1):
            print(f"{i}: {f}")
        return wavs

    def process_audio(self, filename, width=1024):
        print(f"Reading {filename}...")
        data, sr = sf.read(filename)
        
        # Convert to mono if necessary
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        # Normalize to 0-255 range
        data_min = data.min()
        data_max = data.max()
        if data_max == data_min:
            print("⚠️ Audio file appears to be silent.")
            return
            
        normalized = ((data - data_min) / (data_max - data_min) * 255).astype(np.uint8)

        # Calculate dimensions
        height = len(normalized) // width
        if height == 0:
            print("⚠️ Audio file too short for current width.")
            return

        # Reshape into image matrix
        pixel_matrix = normalized[:width * height].reshape((height, width))
        self.current_image = Image.fromarray(pixel_matrix)
        self.last_wav = filename
        print(f"✅ Processed {len(data)} samples into {width}x{height} matrix.")

    def run(self):
        while True:
            print("\n--- SYNCHESTHETIC AUDIO ENGINE ---")
            print("1: Upload/Select .wav file")
            print("2: Preview Image (Show Stats)")
            print("3: Save Image")
            print("4: Exit")
            
            choice = input("\nSelect an option: ").strip()

            if choice == "1":
                wavs = self.list_wavs()
                if wavs:
                    idx = input("Select file number: ")
                    try:
                        selected = wavs[int(idx) - 1]
                        self.process_audio(selected)
                    except (ValueError, IndexError):
                        print("Invalid selection.")

            elif choice == "2":
                if self.current_image:
                    print(f"\nImage Stats for: {self.last_wav}")
                    print(f"Dimensions: {self.current_image.size}")
                    print(f"Mode: {self.current_image.mode}")
                    # Attempt to show with system viewer
                    self.current_image.show()
                else:
                    print("No image processed yet. Select a file first.")

            elif choice == "3":
                if self.current_image:
                    out_name = f"viz_{self.last_wav}.png"
                    self.current_image.save(out_name)
                    print(f"✅ Saved as {out_name}")
                else:
                    print("Nothing to save.")

            elif choice == "4":
                print("Exiting...")
                break

if __name__ == "__main__":
    engine = AudioVisualizer()
    engine.run()