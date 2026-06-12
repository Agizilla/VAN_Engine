import os
import yt_dlp
import whisper
from whisper.utils import get_writer

# --- Configuration ---
CHANNEL_URL = "https://www.youtube.com/@functionalmelancholic/videos"
OUTPUT_DIR = "transcriptions"
ARCHIVE_FILE = "downloaded_history.txt" # Keeps track of IDs to skip downloads
MODEL_SIZE = "turbo" 

def download_and_process(url):
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{OUTPUT_DIR}/%(title)s.%(ext)s',
        # --- RESUME & SKIP LOGIC ---
        'download_archive': ARCHIVE_FILE, # CRITICAL: Skips already downloaded videos
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'extractor_args': {'youtube': {'player_client': ['web', 'tv']}},
        'cookies_from_browser': 'chrome', 
        'ignoreerrors': True,
        'quiet': False,
    }

    # Load the "Soul" (Whisper Model) once to save memory
    print(f"--- Loading Whisper Model: {MODEL_SIZE} ---")
    model = whisper.load_model(MODEL_SIZE)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # We extract info and download one by one to handle transcription immediately
        try:
            playlist_info = ydl.extract_info(url, download=False)
            if 'entries' not in playlist_info:
                entries = [playlist_info]
            else:
                entries = playlist_info['entries']

            for entry in entries:
                if not entry: continue
                
                video_title = entry.get('title', 'Unknown_Video')
                video_id = entry.get('id')
                
                # Double check if transcript already exists to skip the whole process
                base_path = os.path.join(OUTPUT_DIR, video_title)
                if os.path.exists(f"{base_path}.txt") or os.path.exists(f"{base_path}.srt"):
                    print(f"--- Skipping {video_title} (Transcript Exists) ---")
                    continue

                print(f"\n--- Processing: {video_title} ---")
                
                # Download the specific video
                result = ydl.download([f"https://www.youtube.com/watch?v= {video_id}"])
                
                # Locate the resulting MP3
                mp3_path = f"{base_path}.mp3"
                
                if os.path.exists(mp3_path):
                    print(f"--- Transcribing with Timestamps: {video_title} ---")
                    transcribe_with_timestamps(model, mp3_path, OUTPUT_DIR)
                else:
                    print(f"--- Download failed or skipped for {video_title} ---")

        except Exception as e:
            print(f"Workflow Error: {e}")

def transcribe_with_timestamps(model, audio_path, output_dir):
    try:
        # Perform transcription
        result = model.transcribe(audio_path, verbose=False)
        
        # Use Whisper's internal writers for timestamps (SRT, VTT, TXT)
        # This creates [filename].srt and [filename].txt in the directory
        writer_args = {"highlight_words": False, "max_line_count": None, "max_line_width": None}
        
        for format in ["txt", "srt"]:
            writer = get_writer(format, output_dir)
            writer(result, audio_path, writer_args)
            
        print(f"✓ Success: Transcripts generated for {os.path.basename(audio_path)}")
    except Exception as e:
        print(f"Transcription Error: {e}")

if __name__ == "__main__":
    print("--- Starting Production Sync ---")
    download_and_process(CHANNEL_URL)
    print("\n--- All Pending Tasks Complete ---")