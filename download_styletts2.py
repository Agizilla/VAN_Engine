#!/usr/bin/env python3
"""
Download StyleTTS 2 model files from nonoJDWAOIDAWKDA/Amelia1_ft_StyleTTS2
Run: python download_styletts2.py
"""

import sys
import io
import os
import requests
from pathlib import Path
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def download_file(url: str, dest: Path, retries: int = 3):
    for attempt in range(retries):
        try:
            print(f"  Downloading {dest.name}...")
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            with open(dest, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            bar_len = 40
                            filled = int(bar_len * downloaded // total_size)
                            bar = '█' * filled + '░' * (bar_len - filled)
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_mb = total_size / (1024 * 1024)
                            sys.stdout.write(f'\r    [{bar}] {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)')
                            sys.stdout.flush()
            sys.stdout.write('\n')
            sys.stdout.flush()
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"  ✓ Downloaded {dest.name} ({size_mb:.1f} MB)")
            return True
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                wait_time = 2
                print(f"    Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    return False


def main():
    print("=" * 70)
    print("StyleTTS 2 Model Downloader (Amelia1_ft_StyleTTS2)")
    print("=" * 70)
    model_dir = Path("./models/Amelia1_ft_StyleTTS2")
    model_dir.mkdir(parents=True, exist_ok=True)
    base_url = "https://huggingface.co/nonoJDWAOIDAWKDA/Amelia1_ft_StyleTTS2/resolve/main/"
    files = {
        "config.yml": base_url + "config.yml",
        "models.py": base_url + "models.py",
        "utils.py": base_url + "utils.py",
        "text_utils.py": base_url + "text_utils.py",
        "bert.pth": base_url + "bert.pth",
        "bert_encoder.pth": base_url + "bert_encoder.pth",
        "decoder.pth": base_url + "decoder.pth",
        "diffusion.pth": base_url + "diffusion.pth",
        "predictor.pth": base_url + "predictor.pth",
        "predictor_encoder.pth": base_url + "predictor_encoder.pth",
        "style_encoder.pth": base_url + "style_encoder.pth",
        "text_encoder.pth": base_url + "text_encoder.pth",
        "mpd.pth": base_url + "mpd.pth",
        "msd.pth": base_url + "msd.pth",
        "pitch_extractor.pth": base_url + "pitch_extractor.pth",
        "text_aligner.pth": base_url + "text_aligner.pth",
        "wd.pth": base_url + "wd.pth",
        "checkpoint.pth": base_url + "checkpoint.pth",
        "config.json": base_url + "config.json",
        "training_metrics.png": base_url + "training_metrics.png",
        "README.md": base_url + "README.md",
        ".gitattributes": base_url + ".gitattributes",
    }
    print("\nFiles to download:")
    total_mb = 0
    for filename in files.keys():
        if filename in ["checkpoint.pth", "config.json", "training_metrics.png", "README.md", ".gitattributes"]:
            continue
        size_estimate = {
            "bert.pth": 25.2, "bert_encoder.pth": 1.58, "decoder.pth": 217,
            "diffusion.pth": 87.7, "predictor.pth": 64.8, "predictor_encoder.pth": 55.5,
            "style_encoder.pth": 55.5, "text_encoder.pth": 22.4, "mpd.pth": 164,
            "msd.pth": 1.14, "pitch_extractor.pth": 21, "text_aligner.pth": 31.5,
            "wd.pth": 4.7
        }.get(filename, 0)
        if size_estimate > 0:
            total_mb += size_estimate
            print(f"  {filename} ({size_estimate:.1f} MB)")
        else:
            print(f"  {filename}")
    print(f"\nTotal download size: ~{total_mb:.0f} MB (plus optional files)")
    print(f"Target directory: {model_dir.absolute()}")
    confirm = input("\nProceed with download? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Download cancelled.")
        return
    print("\n" + "=" * 70)
    print("Starting download...")
    print("=" * 70 + "\n")
    success_count = 0
    fail_count = 0
    skipped_count = 0
    for filename, url in files.items():
        dest = model_dir / filename
        if filename == "checkpoint.pth":
            print(f"Skipping {filename} (2.03 GB) - optional file")
            skipped_count += 1
            continue
        if dest.exists():
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"✓ {filename} already exists ({size_mb:.1f} MB)")
            success_count += 1
        else:
            if download_file(url, dest):
                success_count += 1
            else:
                fail_count += 1
    print("\n" + "=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"Successfully downloaded: {success_count} files")
    if fail_count > 0:
        print(f"Failed: {fail_count} files")
    if skipped_count > 0:
        print(f"Skipped: {skipped_count} files (optional)")
    print(f"\nModel directory: {model_dir.absolute()}")
    if success_count == len([f for f in files if f != "checkpoint.pth"]):
        print("\nAll required files downloaded successfully!")
        print("\nNext steps:")
        print("1. Run: python voice_cloning_ui.py")
        print("2. The UI will automatically detect the model")
    else:
        print("\nSome downloads failed. Run the script again to retry.")
    print("=" * 70)


if __name__ == "__main__":
    main()
