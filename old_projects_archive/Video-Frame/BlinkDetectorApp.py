import tkinter as tk
from tkinter import messagebox
import cv2
import dlib
import numpy as np
from PIL import ImageGrab
from scipy.spatial import distance as dist
import time
import os
import sys

# -----------------------------------------------------------------------------
# Global Helpers & Constants
# -----------------------------------------------------------------------------

def eye_aspect_ratio(eye_points):
    """
    Compute the Eye Aspect Ratio (EAR).
    eye_points is a list of (x, y) coordinates.
    """
    # Vertical distances
    A = dist.euclidean(eye_points[1], eye_points[5])
    B = dist.euclidean(eye_points[2], eye_points[4])
    # Horizontal distance
    C = dist.euclidean(eye_points[0], eye_points[3])

    ear = (A + B) / (2.0 * C)
    return ear

def shape_to_np(shape, dtype="int"):
    """Convert dlib shape object to numpy array (68, 2)"""
    coords = np.zeros((68, 2), dtype=dtype)
    for i in range(0, 68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords

# -----------------------------------------------------------------------------
# Settings Window
# -----------------------------------------------------------------------------

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        self.geometry("300x450")
        self.attributes('-topmost', True)

        # Helper to create input rows
        def create_entry(label_text, current_val, key, is_color=False):
            frame = tk.Frame(self)
            frame.pack(fill='x', padx=10, pady=5)
            lbl = tk.Label(frame, text=label_text, width=20, anchor='w')
            lbl.pack(side='left')
            entry = tk.Entry(frame)
            entry.insert(0, str(current_val))
            entry.pack(side='right', expand=True, fill='x')
            return key, entry

        self.entries = {}
        
        # Logic Settings
        tk.Label(self, text="Detection Logic", font=("Arial", 10, "bold")).pack(pady=5)
        self.entries['REFRESH'] = create_entry("Refresh Rate (ms):", parent.REFRESH_RATE_MS, 'REFRESH')[1]
        self.entries['THRESH'] = create_entry("EAR Threshold:", parent.EYE_AR_THRESH, 'THRESH')[1]
        self.entries['FRAMES'] = create_entry("Consecutive Frames:", parent.EYE_AR_CONSEC_FRAMES, 'FRAMES')[1]

        # Color Settings
        tk.Label(self, text="Visuals (Hex/Name)", font=("Arial", 10, "bold")).pack(pady=5)
        self.entries['C_FACE'] = create_entry("Face Rect Color:", parent.COLOR_FACE_RECT, 'C_FACE')[1]
        self.entries['C_EYES'] = create_entry("Eye Poly Color:", parent.COLOR_EYE_POLY, 'C_EYES')[1]
        self.entries['C_DOTS'] = create_entry("Landmark Color:", parent.COLOR_LANDMARKS, 'C_DOTS')[1]

        # Apply Button
        btn_apply = tk.Button(self, text="Apply Settings", command=self.apply_settings, bg="#dddddd")
        btn_apply.pack(pady=20, fill='x', padx=10)

    def apply_settings(self):
        try:
            # Logic
            new_refresh = int(self.entries['REFRESH'].get())
            new_thresh = float(self.entries['THRESH'].get())
            new_frames = int(self.entries['FRAMES'].get())

            if not (1 <= new_refresh <= 2000): raise ValueError("Refresh rate must be 1-2000")
            if not (0.1 <= new_thresh <= 0.5): raise ValueError("EAR Threshold must be 0.1-0.5")
            if not (1 <= new_frames <= 20): raise ValueError("Frames must be 1-20")

            self.parent.REFRESH_RATE_MS = new_refresh
            self.parent.EYE_AR_THRESH = new_thresh
            self.parent.EYE_AR_CONSEC_FRAMES = new_frames

            # Colors
            self.parent.COLOR_FACE_RECT = self.entries['C_FACE'].get()
            self.parent.COLOR_EYE_POLY = self.entries['C_EYES'].get()
            self.parent.COLOR_LANDMARKS = self.entries['C_DOTS'].get()

            # Update Main UI Labels
            self.parent.lbl_info.config(text=f"EAR: {new_thresh} | Frames: {new_frames}")
            messagebox.showinfo("Success", "Settings updated!")
            self.destroy()

        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))

# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------

class TransparentDetector(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- 1. Check Dependencies ---
        self.PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"
        self.CASCADE_PATH = "haarcascade_frontalface_default.xml"
        self._check_files()

        # --- 2. Dynamic Settings ---
        self.REFRESH_RATE_MS = 33      # ~30 FPS
        self.EYE_AR_THRESH = 0.30      # Below this is a blink
        self.EYE_AR_CONSEC_FRAMES = 2  # Frames to hold for blink

        # Visual Settings
        self.COLOR_FACE_RECT = "green"
        self.COLOR_EYE_POLY = "cyan"
        self.COLOR_LANDMARKS = "yellow"

        # State Variables
        self.counter = 0
        self.total_blinks = 0
        self.is_running = True
        self.start_time = time.time()
        self.last_ear = 0.0

        # --- 3. Load Models ---
        print("[INFO] Loading detector and predictor...")
        self.face_cascade = cv2.CascadeClassifier(self.CASCADE_PATH)
        self.predictor = dlib.shape_predictor(self.PREDICTOR_PATH)
        
        # Dlib indices for eyes
        self.L_START, self.L_END = 42, 48 # Left eye (actual indices in array)
        self.R_START, self.R_END = 36, 42 # Right eye

        # --- 4. Window Setup ---
        self.title("Blink Detector Overlay")
        self.geometry("600x450+100+100")
        self.overrideredirect(True)      # Borderless
        self.attributes('-alpha', 0.5)   # Semi-transparent
        self.attributes('-topmost', True)
        self.config(bg='black')

        # --- 5. UI Construction ---
        
        # Style
        self.ui_font = ("Consolas", 10)
        self.ui_bg = "#222222"
        self.ui_fg = "#00FF00"

        # Top Bar (Settings & Status)
        self.top_bar = tk.Frame(self, bg=self.ui_bg, height=30)
        self.top_bar.pack(side="top", fill="x")

        self.lbl_status = tk.Label(self.top_bar, text="RUNNING", bg=self.ui_bg, fg="white", font=self.ui_font)
        self.lbl_status.pack(side="left", padx=5)

        self.lbl_info = tk.Label(self.top_bar, text=f"EAR: {self.EYE_AR_THRESH} | Frames: {self.EYE_AR_CONSEC_FRAMES}", 
                                 bg=self.ui_bg, fg="gray", font=("Arial", 8))
        self.lbl_info.pack(side="left", padx=10)

        self.btn_settings = tk.Button(self.top_bar, text="⚙️", command=self.open_settings, 
                                      bg="#444", fg="white", relief="flat", font=("Arial", 8))
        self.btn_settings.pack(side="right", padx=2, pady=2)

        # Canvas (The "Window" into the analysis)
        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Bottom Bar (Stats & Controls)
        self.bottom_bar = tk.Frame(self, bg=self.ui_bg, height=40)
        self.bottom_bar.pack(side="bottom", fill="x")

        self.lbl_blinks = tk.Label(self.bottom_bar, text="Blinks: 0", bg=self.ui_bg, fg=self.ui_fg, font=("Arial", 12, "bold"))
        self.lbl_blinks.pack(side="left", padx=10)

        self.lbl_timer = tk.Label(self.bottom_bar, text="Time: 0s | BPM: 0.0", bg=self.ui_bg, fg="white", font=self.ui_font)
        self.lbl_timer.pack(side="left", padx=10, expand=True)
        # Bind reset click
        self.lbl_timer.bind("<Button-1>", lambda e: self.reset_counters())
        self.lbl_timer.bind("<Enter>", lambda e: self.lbl_timer.config(cursor="hand2"))

        self.btn_exit = tk.Button(self.bottom_bar, text=" X ", command=self.quit_app, 
                                  bg="#880000", fg="white", font=("Arial", 10, "bold"))
        self.btn_exit.pack(side="right", padx=5, pady=5)

        # --- 6. Draggable Logic ---
        self._drag_data = {"x": 0, "y": 0}
        # Bind drag to top bar, bottom bar, and canvas
        for widget in [self.top_bar, self.bottom_bar, self.canvas, self.lbl_status, self.lbl_blinks, self.lbl_timer]:
            widget.bind("<ButtonPress-1>", self._start_move)
            widget.bind("<B1-Motion>", self._on_move)

        # --- 7. Start Loop ---
        self.after(self.REFRESH_RATE_MS, self.run_detection)

    def _check_files(self):
        missing = []
        if not os.path.exists(self.PREDICTOR_PATH):
            missing.append(self.PREDICTOR_PATH)
        if not os.path.exists(self.CASCADE_PATH):
            missing.append(self.CASCADE_PATH)
        
        if missing:
            messagebox.showerror("Missing Files", 
                f"The following required files are missing from the script directory:\n\n{chr(10).join(missing)}\n\nPlease download them (see instructions).")
            sys.exit()

    def _start_move(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_move(self, event):
        deltax = event.x - self._drag_data["x"]
        deltay = event.y - self._drag_data["y"]
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def open_settings(self):
        SettingsWindow(self)

    def reset_counters(self):
        self.start_time = time.time()
        self.total_blinks = 0
        self.counter = 0
        self.lbl_blinks.config(text="Blinks: 0")
        self.lbl_timer.config(text="Time: 0s | BPM: 0.0")

    def quit_app(self):
        self.is_running = False
        self.destroy()

    def capture_screen_area(self):
        """Captures the screen area directly beneath the window"""
        # Get window geometry
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        w = self.winfo_width()
        h = self.winfo_height()

        # Capture using Pillow
        bbox = (x, y, x + w, y + h)
        try:
            img = ImageGrab.grab(bbox=bbox, all_screens=True)
            # Convert to OpenCV format
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"Capture error: {e}")
            return None

    def process_blinks(self, ear):
        # Check if EAR is below the blink threshold
        if ear < self.EYE_AR_THRESH:
            self.counter += 1
        else:
            # If the eyes were closed for a sufficient number of frames, count the blink
            if self.counter >= self.EYE_AR_CONSEC_FRAMES:
                self.total_blinks += 1
                self.lbl_blinks.config(text=f"Blinks: {self.total_blinks}")
            self.counter = 0

    def draw_detections(self, faces, gray_frame, color_frame):
        """Draws overlays on the Tkinter canvas based on CV data"""
        self.canvas.delete("all") # Clear previous drawing
        
        # Note: We do NOT draw the camera image to avoid ghosting.
        # We only draw the analysis data.

        # Process detected faces
        for i, (x, y, w, h) in enumerate(faces):
            # Draw Face Rectangle (Green)
            self.canvas.create_rectangle(x, y, x+w, y+h, outline=self.COLOR_FACE_RECT, width=2)
            
            # For the first face, perform expensive landmark detection
            if i == 0:
                # Dlib requires a rectangle object
                dlib_rect = dlib.rectangle(int(x), int(y), int(x + w), int(y + h))
                
                # Get landmarks
                shape = self.predictor(gray_frame, dlib_rect)
                shape = shape_to_np(shape)

                # Extract eye coordinates
                leftEye = shape[self.L_START:self.L_END]
                rightEye = shape[self.R_START:self.R_END]

                # Calculate EAR
                leftEAR = eye_aspect_ratio(leftEye)
                rightEAR = eye_aspect_ratio(rightEye)
                avgEAR = (leftEAR + rightEAR) / 2.0
                self.last_ear = avgEAR

                # Process Blink Logic
                self.process_blinks(avgEAR)

                # Draw Eyes (Polygon) - Flatten points for Tkinter
                def flatten(pts): return [coord for point in pts for coord in point]
                
                self.canvas.create_polygon(flatten(leftEye), outline=self.COLOR_EYE_POLY, fill='', width=2)
                self.canvas.create_polygon(flatten(rightEye), outline=self.COLOR_EYE_POLY, fill='', width=2)

                # Draw all 68 landmarks (Yellow dots)
                for (lx, ly) in shape:
                    self.canvas.create_oval(lx-1, ly-1, lx+1, ly+1, fill=self.COLOR_LANDMARKS, outline="")
                
                # Display current EAR near the face
                self.canvas.create_text(x, y-10, text=f"EAR: {avgEAR:.2f}", fill=self.COLOR_EYE_POLY, anchor="sw")

    def run_detection(self):
        if not self.is_running:
            return

        # 1. Capture Screen
        frame = self.capture_screen_area()
        if frame is None:
             self.after(self.REFRESH_RATE_MS, self.run_detection)
             return

        # 2. Preprocess
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 3. Detect Faces (Haar)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # 4. Draw & Logic
        self.draw_detections(faces, gray, frame)

        # 5. Update Timer Stats
        elapsed = time.time() - self.start_time
        mins = elapsed / 60.0
        bpm = self.total_blinks / mins if mins > 0 else 0
        
        # Format time MM:SS
        m, s = divmod(int(elapsed), 60)
        time_str = f"{m:02d}:{s:02d}"
        
        self.lbl_timer.config(text=f"Time: {time_str} | BPM: {bpm:.1f}")

        # 6. Schedule Next Loop
        self.after(self.REFRESH_RATE_MS, self.run_detection)

if __name__ == "__main__":
    app = TransparentDetector()
    app.mainloop()