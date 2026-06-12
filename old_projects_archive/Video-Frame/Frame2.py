import tkinter as tk
from tkinter import ttk, messagebox 
from PIL import ImageGrab, ImageTk, Image 
import cv2
import numpy as np
import time 
from scipy.spatial import distance as dist 
import dlib 

# --- Configuration Constants (Now dynamic) ---
DLIB_LANDMARK_PREDICTOR = 'shape_predictor_68_face_landmarks.dat'
FACE_CASCADE_PATH = 'haarcascade_frontalface_default.xml'

# Initialize Dlib and Haar
try:
    predictor = dlib.shape_predictor(DLIB_LANDMARK_PREDICTOR)
    face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
except:
    print("Error: Required dlib or haarcascade files not found.")
    exit()

if not face_cascade.empty() and predictor:
    (L_START, L_END) = (42, 48)
    (R_START, R_END) = (36, 42)
else:
    print("Error: Could not load cascade or Dlib predictor.")
    exit()


# --- Settings Window Class (Toplevel/Non-Modal) ---

class SettingsWindow(tk.Toplevel):
    def __init__(self, master, detector_app):
        super().__init__(master)
        self.detector_app = detector_app
        self.title("Detector Settings")
        self.geometry("300x250")
        self.attributes('-topmost', True)
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        
        self.transient(master) 
        
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        def create_setting(frame, label_text, initial_value, command=None):
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill='x', pady=5)
            
            ttk.Label(row_frame, text=label_text, width=15).pack(side='left')
            
            value_var = tk.StringVar(value=str(initial_value))
            
            entry = ttk.Entry(row_frame, textvariable=value_var, width=10)
            entry.pack(side='left', fill='x', expand=True)
            
            if command:
                ttk.Button(row_frame, text="Apply", command=lambda: command(value_var.get())).pack(side='right')
            
            return value_var
            
        self.refresh_rate_var = create_setting(main_frame, "Refresh Rate (ms):", 
                                                self.detector_app.REFRESH_RATE_MS, 
                                                self.apply_refresh_rate)
        
        self.ear_thresh_var = create_setting(main_frame, "EAR Threshold:", 
                                             self.detector_app.EYE_AR_THRESH, 
                                             self.apply_ear_thresh)
                                             
        self.consec_frames_var = create_setting(main_frame, "Consec. Frames:", 
                                                self.detector_app.EYE_AR_CONSEC_FRAMES, 
                                                self.apply_consec_frames)

    def apply_refresh_rate(self, value):
        try:
            new_rate = int(value)
            if 1 <= new_rate <= 1000:
                self.detector_app.REFRESH_RATE_MS = new_rate
                print(f"Settings: Refresh Rate set to {new_rate}ms.")
            else:
                raise ValueError("Rate must be between 1 and 1000.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid Refresh Rate: {e}")
            self.refresh_rate_var.set(str(self.detector_app.REFRESH_RATE_MS))

    def apply_ear_thresh(self, value):
        try:
            new_thresh = float(value)
            if 0.1 <= new_thresh <= 0.5:
                self.detector_app.EYE_AR_THRESH = new_thresh
                print(f"Settings: EAR Threshold set to {new_thresh}.")
            else:
                raise ValueError("Threshold must be between 0.1 and 0.5.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid EAR Threshold: {e}")
            self.ear_thresh_var.set(str(self.detector_app.EYE_AR_THRESH))
            
    def apply_consec_frames(self, value):
        try:
            new_frames = int(value)
            if 1 <= new_frames <= 10:
                self.detector_app.EYE_AR_CONSEC_FRAMES = new_frames
                print(f"Settings: Consecutive Frames set to {new_frames}.")
            else:
                raise ValueError("Frames must be between 1 and 10.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid Frames value: {e}")
            self.consec_frames_var.set(str(self.detector_app.EYE_AR_CONSEC_FRAMES))

    def close_window(self):
        self.detector_app.settings_window = None
        self.destroy()


# --- Main Application Class ---

class TransparentDetector(tk.Tk):
    # Make settings constants class attributes for dynamic access
    REFRESH_RATE_MS = 33
    EYE_AR_THRESH = 0.30 
    EYE_AR_CONSEC_FRAMES = 2
    
    # --- WINDOW CONTROL METHODS (Dragging) ---
    
    def _start_move(self, event):
        """Records the initial click position for dragging."""
        self._drag_x = event.x_root - self.winfo_rootx() 
        self._drag_y = event.y_root - self.winfo_rooty()

    def _on_move(self, event):
        """Calculates and applies the new window position."""
        new_x = event.x_root - self._drag_x
        new_y = event.y_root - self._drag_y
        self.geometry(f'+{new_x}+{new_y}')
        
    def open_settings(self):
        """Opens the non-modal settings window."""
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self, self)
        self.settings_window.lift() 
        
    def reset_counters(self, event):
        self.total_blinks = 0
        self.consec_frames_count = 0
        self.start_time = time.time()
        self.blink_label.config(text="Blinks: 0")
        self.timer_label.config(text="Time: 0s | BPM: N/A")

    # --- __init__ method ---
    def __init__(self):
        super().__init__()
        self.title("Transparent Detector")
        
        # --- State Variables ---
        self.is_paused = False    
        self.start_time = time.time()
        self.total_blinks = 0
        self.consec_frames_count = 0 
        self._drag_x = 0
        self._drag_y = 0
        self.settings_window = None 

        # --- Window Setup ---
        self.geometry("600x400+100+100") 
        self.attributes('-alpha', 0.5) 
        self.attributes('-topmost', True) 
        self.overrideredirect(True) 

        self.main_frame = tk.Frame(self, bg='gray')
        self.main_frame.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(self.main_frame, bg='gray', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, side=tk.TOP)
        
        # --- Settings Bar (Top) ---
        self.settings_bar = tk.Frame(self.main_frame, bg="black")
        self.settings_bar.pack(fill=tk.X, side=tk.TOP)
        
        self.settings_label = tk.Label(
            self.settings_bar, 
            text="Real-Time Detection Overlay",
            font=("Arial", 10), fg="yellow", bg="black", anchor="w", padx=5, pady=2
        )
        self.settings_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.settings_btn = tk.Button(self.settings_bar, text="⚙️", command=self.open_settings, 
                                     font=("Arial", 10), fg="white", bg="#333333", bd=0, padx=5)
        self.settings_btn.pack(side=tk.RIGHT, padx=5, pady=2)

        # Bottom frame for controls and metrics
        self.bottom_bar = tk.Frame(self.main_frame, bg="black")
        self.bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # UI Elements
        self.blink_label = tk.Label(self.bottom_bar, text="Blinks: 0", font=("Arial", 12, "bold"), fg="white", bg="black", anchor="w", padx=5, pady=5)
        self.blink_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        
        self.timer_label = tk.Label(self.bottom_bar, text="Time: 0s | BPM: N/A", font=("Arial", 12, "bold"), fg="white", bg="black", anchor="e", padx=5, pady=5)
        self.timer_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.timer_label.bind('<Button-1>', self.reset_counters)
        
        self.exit_button = tk.Button(self.bottom_bar, text="X", command=self.destroy, font=("Arial", 12, "bold"), fg="white", bg="#A00000", activebackground="#C00000", bd=0, width=3 )
        self.exit_button.pack(side=tk.RIGHT, padx=(0, 5), pady=5)

        # --- NEW: Binding Setup Method ---
        self._setup_bindings()
        
        self.run_detection() 

    def _setup_bindings(self):
        """Encapsulates all bindings, ensuring helper methods are defined first."""
        # Keyboard binding
        self.bind('<p>', self.toggle_pause)
        
        # Dragging bindings
        self.main_frame.bind('<ButtonPress-1>', self._start_move)
        self.main_frame.bind('<B1-Motion>', self._on_move)
        self.canvas.bind('<ButtonPress-1>', self._start_move)
        self.canvas.bind('<B1-Motion>', self._on_move)
        self.settings_bar.bind('<ButtonPress-1>', self._start_move)
        self.settings_bar.bind('<B1-Motion>', self._on_move)

    # --- CONTROL & UTILITY METHODS (Continued) ---
    
    def toggle_pause(self, event=None):
        self.is_paused = not self.is_paused
        status = "PAUSED" if self.is_paused else "RUNNING"
        self.update_settings_display(f"Status: {status}")

    def update_settings_display(self, status=""):
        p = "PAUSED" if self.is_paused else "RUNNING"
        s = f"EAR: {self.EYE_AR_THRESH} | Frames: {self.EYE_AR_CONSEC_FRAMES}"
        self.settings_label.config(text=f"[{p}] | {s} | Status: {status}")
        
    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def update_timer_and_bpm(self):
        elapsed_time = time.time() - self.start_time
        seconds = int(elapsed_time)
        
        time_base = max(30.0, elapsed_time)

        if self.total_blinks > 0 and time_base > 0:
            bpm = (self.total_blinks / time_base) * 60
            bpm_str = f"{bpm:.1f}"
        else:
            bpm_str = "N/A"
            
        self.timer_label.config(text=f"Time: {seconds}s | BPM: {bpm_str}")
        
    # --- DETECTION METHODS ---

    def capture_screen_area(self):
        x_start = self.winfo_x()
        y_start = self.winfo_y()
        width = self.winfo_width()
        height = self.winfo_height()
        
        bbox = (x_start, y_start, x_start + width, y_start + height)
        screenshot = ImageGrab.grab(bbox)
        
        img_np = np.array(screenshot)
        frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR) 
        
        return frame

    def draw_detections(self, frame_bgr, faces, avg_ear):
        
        self.canvas.delete("all") 
        
        frame_h, frame_w = frame_bgr.shape[:2]
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        scale_x = canvas_w / frame_w
        scale_y = canvas_h / frame_h

        # Convert and resize the frame
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(frame_rgb)
        img_pil = img_pil.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS) 
        
        # GHOSTING FIX: Ensure the photo reference is a class attribute
        self._photo = ImageTk.PhotoImage(image=img_pil) 
        
        self.canvas.create_image(0, 0, image=self._photo, anchor=tk.NW)

        # --- Draw Detection Boxes and Landmarks ---
        
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        for (x, y, w, h) in faces:
            # Scale face coordinates
            x1_scaled, y1_scaled = int(x * scale_x), int(y * scale_y)
            x2_scaled, y2_scaled = int((x + w) * scale_x), int((y + h) * scale_y)
            
            # Draw Face Box (Gold)
            self.canvas.create_rectangle(
                x1_scaled, y1_scaled, x2_scaled, y2_scaled, 
                outline="#FFD700", width=2 
            )
            
            # Re-run Dlib landmark calculation 
            rect = dlib.rectangle(x, y, x + w, y + h)
            shape = predictor(gray, rect)
            points = np.array([[p.x, p.y] for p in shape.parts()])
            
            left_eye = points[L_START:L_END]
            right_eye = points[R_START:R_END]

            for eye_points in [left_eye, right_eye]:
                # Scale landmark points
                scaled_points = []
                for (px, py) in eye_points:
                    scaled_points.append(int(px * scale_x))
                    scaled_points.append(int(py * scale_y))
                
                # Draw the polygon on the Tkinter canvas (Cyan)
                self.canvas.create_polygon(
                    *scaled_points, 
                    outline="#00FFFF", 
                    fill="", 
                    width=2
                )
        
        self.process_blinks(avg_ear)


    def process_blinks(self, avg_ear):
        
        if avg_ear < self.EYE_AR_THRESH: 
            self.consec_frames_count += 1
        else:
            if self.consec_frames_count >= self.EYE_AR_CONSEC_FRAMES: 
                self.total_blinks += 1
            
            self.consec_frames_count = 0
            
        self.blink_label.config(text=f"Blinks: {self.total_blinks}")
        self.update_timer_and_bpm()


    def run_detection(self):
        
        if self.is_paused:
            self.update_settings_display("Detection Paused")
            self.after(self.REFRESH_RATE_MS, self.run_detection) 
            return

        frame_bgr = self.capture_screen_area()
        
        # 1. Face Detection
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        avg_ear = 1.0
        if len(faces) > 0:
            (x, y, w, h) = faces[0] 
            rect = dlib.rectangle(x, y, x + w, y + h)
            
            shape = predictor(gray, rect)
            points = np.array([[p.x, p.y] for p in shape.parts()])
            
            left_eye = points[L_START:L_END]
            right_eye = points[R_START:R_END]
            avg_ear = (self.eye_aspect_ratio(left_eye) + self.eye_aspect_ratio(right_eye)) / 2.0


        # 2. Draw Results
        self.draw_detections(frame_bgr, faces, avg_ear)
        self.update_settings_display()
        
        self.after(self.REFRESH_RATE_MS, self.run_detection)

if __name__ == "__main__":
    app = TransparentDetector()
    app.mainloop()