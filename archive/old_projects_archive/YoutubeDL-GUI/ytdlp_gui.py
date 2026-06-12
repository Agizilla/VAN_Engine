import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os

# --- Configuration ---
YTDLP_EXECUTABLE = 'yt-dlp'

class YoutubeDL_GUI:
    def __init__(self, master):
        self.master = master
        master.title("🎥 yt-dlp GUI with Filters (Resilient)")
        master.geometry("600x650") 
        master.resizable(False, False)

        # Variables for core settings
        self.download_dir = tk.StringVar(value=os.path.expanduser("~"))
        self.video_url = tk.StringVar()
        
        # QUALITY: Changed to a Radio button group, defaulting to 'best'
        self.quality_choice = tk.StringVar(value="best")

        # Variables for NEW Filtering Settings
        self.playlist_start_idx = tk.StringVar(value="1")
        self.playlist_end_idx = tk.StringVar()
        self.date_after = tk.StringVar()
        self.date_before = tk.StringVar()
        self.min_length = tk.StringVar()
        self.max_length = tk.StringVar()

        # Other useful settings
        self.embed_thumbnail = tk.BooleanVar(value=True)
        self.write_info_json = tk.BooleanVar(value=False)
        self.ignore_errors = tk.BooleanVar(value=True)
        
        # NEW: Option to ignore SSL errors
        self.no_check_certificates = tk.BooleanVar(value=False) 

        # Set up the UI
        self.create_widgets()

    def create_widgets(self):
        # --- Main Frame ---
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill='both', expand=True)

        # --- Core Settings (URL & Directory) ---
        
        # Download Directory Section
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill='x', pady=5)
        ttk.Label(dir_frame, text="**Download Folder:**", font='TkDefaultFont 9 bold').pack(side='left', padx=(0, 5))
        ttk.Entry(dir_frame, textvariable=self.download_dir, state='readonly', width=55).pack(side='left', fill='x', expand=True)
        ttk.Button(dir_frame, text="Browse", command=self.select_directory).pack(side='right')

        # URL Section
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill='x', pady=5)
        ttk.Label(url_frame, text="**Video/Channel URL:**", font='TkDefaultFont 9 bold').pack(side='left', padx=(0, 5))
        ttk.Entry(url_frame, textvariable=self.video_url, width=55).pack(side='left', fill='x', expand=True)

        # Quality/Format Section (NOW RADIO BUTTONS)
        ttk.Label(main_frame, text="**Download Quality (Resilient):**", font='TkDefaultFont 9 bold').pack(anchor='w', pady=(10, 0))
        
        quality_radio_frame = ttk.Frame(main_frame)
        quality_radio_frame.pack(anchor='w', pady=5)

        ttk.Radiobutton(quality_radio_frame, text="Best Available Quality (-f best)", variable=self.quality_choice, value="best").pack(side='left', padx=10)
        ttk.Radiobutton(quality_radio_frame, text="Lowest Quality (-f worst)", variable=self.quality_choice, value="worst").pack(side='left', padx=10)
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)

        # --- Filtering Settings ---
        filter_label = ttk.Label(main_frame, text="**Playlist & Content Filters:**", font='TkDefaultFont 10 bold', foreground="darkblue")
        filter_label.pack(anchor='w', pady=(5, 5))

        # 1. Playlist Index Range
        index_frame = ttk.Frame(main_frame)
        index_frame.pack(fill='x', pady=5)
        ttk.Label(index_frame, text="Playlist Index Range:").pack(side='left')
        ttk.Label(index_frame, text="Start:").pack(side='left', padx=(10, 5))
        ttk.Entry(index_frame, textvariable=self.playlist_start_idx, width=5).pack(side='left')
        ttk.Label(index_frame, text="End:").pack(side='left', padx=(10, 5))
        ttk.Entry(index_frame, textvariable=self.playlist_end_idx, width=5).pack(side='left')
        ttk.Label(index_frame, text="(e.g., 5 for 5th video, leave blank for all)").pack(side='left', padx=10)


        # 2. Date Filtering
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(fill='x', pady=5)
        ttk.Label(date_frame, text="Date Filter (YYYYMMDD):").pack(side='left')
        ttk.Label(date_frame, text="After:").pack(side='left', padx=(10, 5))
        ttk.Entry(date_frame, textvariable=self.date_after, width=10).pack(side='left')
        ttk.Label(date_frame, text="Before:").pack(side='left', padx=(10, 5))
        ttk.Entry(date_frame, textvariable=self.date_before, width=10).pack(side='left')
        ttk.Label(date_frame, text="(e.g., 20240101)").pack(side='left', padx=10)
        
        # 3. Length Filtering
        length_frame = ttk.Frame(main_frame)
        length_frame.pack(fill='x', pady=5)
        ttk.Label(length_frame, text="Length Filter (Minutes):").pack(side='left')
        ttk.Label(length_frame, text="Min:").pack(side='left', padx=(10, 5))
        ttk.Entry(length_frame, textvariable=self.min_length, width=5).pack(side='left')
        ttk.Label(length_frame, text="Max:").pack(side='left', padx=(10, 5))
        ttk.Entry(length_frame, textvariable=self.max_length, width=5).pack(side='left')
        ttk.Label(length_frame, text="(e.g., 5)").pack(side='left', padx=10)

        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=10)

        # --- Other Useful Settings Section ---
        settings_label = ttk.Label(main_frame, text="**Miscellaneous Options:**", font='TkDefaultFont 10 bold', foreground="darkblue")
        settings_label.pack(anchor='w', pady=(5, 0))

        settings_frame = ttk.Frame(main_frame)
        settings_frame.pack(fill='x', pady=5)
        
        # Checkboxes
        ttk.Checkbutton(settings_frame, text="Embed Metadata (Thumbnail, etc.)", variable=self.embed_thumbnail).pack(anchor='w')
        ttk.Checkbutton(settings_frame, text="Write Info JSON (Metadata file)", variable=self.write_info_json).pack(anchor='w')
        ttk.Checkbutton(settings_frame, text="Ignore Download Errors (continue playlist)", variable=self.ignore_errors).pack(anchor='w')
        # NEW: No Check Certificates
        ttk.Checkbutton(settings_frame, text="Ignore SSL Certificate Errors (--no-check-certificates)", variable=self.no_check_certificates).pack(anchor='w')

        # --- Download Button and Status ---
        self.download_button = ttk.Button(main_frame, text="🚀 Start Download", command=self.start_download_thread)
        self.download_button.pack(pady=20, fill='x')

        self.status_label = ttk.Label(main_frame, text="Status: Ready", foreground="green")
        self.status_label.pack(fill='x')


    def select_directory(self):
        """Opens a dialog to select the download folder."""
        new_dir = filedialog.askdirectory(title="Select Download Folder")
        if new_dir:
            self.download_dir.set(new_dir)

    def get_format_string(self):
        """Maps the quality choice (radio button value) to the yt-dlp format string."""
        choice = self.quality_choice.get()
        if choice == "best":
            return "-f 'best'"
        elif choice == "worst":
            return "-f 'worst'"
        return "-f 'best'" # Fallback just in case

    def build_command(self):
        """Constructs the full yt-dlp command based on GUI settings."""
        url = self.video_url.get().strip()
        download_path = self.download_dir.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a video or channel URL.")
            return None
        if not download_path or not os.path.isdir(download_path):
            messagebox.showerror("Error", "Please select a valid download folder.")
            return None

        # Base command structure
        command = [YTDLP_EXECUTABLE]
        
        # Add format/quality
        command.extend(self.get_format_string().split())
        
        # Output template
        command.append("-o")
        command.append(os.path.join(download_path, "%(title)s.%(ext)s"))

        # --- Add Filtering Options ---
        
        # 1. Playlist Index Range
        start_idx = self.playlist_start_idx.get().strip()
        end_idx = self.playlist_end_idx.get().strip()
        
        try:
            if start_idx and int(start_idx) > 1:
                command.extend(["--playlist-start", start_idx])
            if end_idx and int(end_idx) >= 1:
                command.extend(["--playlist-end", end_idx])
        except ValueError:
            messagebox.showwarning("Warning", "Playlist Start/End Index must be a valid number.")
            return None
            
        # 2. Date Filtering
        date_after = self.date_after.get().strip()
        date_before = self.date_before.get().strip()
        
        if date_after:
            command.extend(["--dateafter", date_after])
        if date_before:
            command.extend(["--datebefore", date_before])
            
        # 3. Length Filtering
        min_len = self.min_length.get().strip()
        max_len = self.max_length.get().strip()
        
        match_filter_list = []
        try:
            if min_len:
                min_sec = str(int(min_len) * 60)
                match_filter_list.append(f"$duration > {min_sec}")
            if max_len:
                max_sec = str(int(max_len) * 60)
                match_filter_list.append(f"$duration < {max_sec}")
        except ValueError:
            messagebox.showwarning("Warning", "Length Filters must be a valid number of minutes.")
            return None

        if match_filter_list:
             filter_string = " & ".join(match_filter_list)
             command.extend(["--match-filter", filter_string])


        # --- Add Miscellaneous Options ---
        if self.embed_thumbnail.get():
            command.append("--embed-metadata")
            command.append("--embed-thumbnail")
        if self.write_info_json.get():
            command.append("--write-info-json")
        if self.ignore_errors.get():
            command.append("--ignore-errors")
        
        # NEW: Add --no-check-certificates flag
        if self.no_check_certificates.get():
            command.append("--no-check-certificates")
            
        # Finally, add the URL
        command.append(url)
        
        return command

    def start_download_thread(self):
        """Starts the download process in a separate thread to prevent GUI freezing."""
        command = self.build_command()
        if command:
            self.status_label.config(text="Status: Starting download...", foreground="blue")
            self.download_button.config(state=tk.DISABLED, text="Downloading...")
            # Start the actual download in a new thread
            download_thread = threading.Thread(target=self.execute_download, args=(command,))
            download_thread.start()

    def execute_download(self, command):
        """Executes the yt-dlp command using subprocess."""
        try:
            result = subprocess.run(
                command, 
                check=True, 
                text=True,
                capture_output=True
            )
            # If the process finishes successfully
            self.master.after(0, lambda: self.update_status(f"Status: Download Complete! Files saved to: {self.download_dir.get()}", "green"))

        except subprocess.CalledProcessError as e:
            error_message = f"Error during download. Check terminal or logs for details. {e.stderr}"
            self.master.after(0, lambda: self.update_status(error_message, "red"))
            messagebox.showerror("Download Error", f"yt-dlp failed: {e.stderr[:200]}...")

        except FileNotFoundError:
            error_message = f"Status: Error - '{YTDLP_EXECUTABLE}' not found. Did you install it?"
            self.master.after(0, lambda: self.update_status(error_message, "red"))
            messagebox.showerror("Error", f"'{YTDLP_EXECUTABLE}' executable not found. Please ensure it is installed and in your system's PATH.")

        finally:
            self.master.after(0, lambda: self.download_button.config(state=tk.NORMAL, text="🚀 Start Download"))
            
    def update_status(self, text, color):
        """Updates the status label from the execution thread."""
        self.status_label.config(text=text, foreground=color)


if __name__ == "__main__":
    root = tk.Tk()
    app = YoutubeDL_GUI(root)
    root.mainloop()