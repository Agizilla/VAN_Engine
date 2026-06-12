import tkinter as tk
from PIL import ImageGrab 
import cv2
import numpy as np
import time 
from scipy.spatial import distance as dist 
import dlib 
from collections import deque # For storing color history

# --- Configuration ---
DLIB_LANDMARK_PREDICTOR = 'shape_predictor_68_face_landmarks.dat'
FACE_CASCADE_PATH = 'haarcascade_frontalface_default.xml'
REFRESH_RATE_MS = 33 

# Blink Detection Constants
EYE_AR_THRESH = 0.30 
EYE_AR_CONSEC_FRAMES = 2 

# Color Keying Constants
COLOR_KEY_TOLERANCE = 15 # The range (in BGR space) around the picked color to key out
COLOR_KEY_OUT_COLOR = [0, 0, 0, 0] # Fully transparent (B, G, R, Alpha)

# Initialize Dlib and Haar
predictor = dlib.shape_predictor(DLIB_LANDMARK_PREDICTOR)
face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)

if face_cascade.empty() or not predictor:
    print("Error: Could not load cascade or Dlib predictor.")
    exit()

(L_START, L_END) = (42, 48)
(R_START, R_END) = (36, 42)

class TransparentDetector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Transparent Detector")
        
        # --- NEW: Color Keying Variables ---
        self.key_color = None     # BGR tuple of the color to be keyed out
        self.replacement_color = None # BGR tuple of the color to replace with
        self.is_paused = False    # To pause and pick colors
        
        # Application State Variables (Unchanged)
        self.start_time = time.time()
        self.total_blinks = 0
        self.consec_frames = 0
        self._drag_x = 0
        self._drag_y = 0

        # --- Window Setup ---
        self.geometry("600x400+100+100") # Increased size for settings
        self.attributes('-alpha', 0.5) 
        self.attributes('-topmost', True) 
        self.overrideredirect(True) 

        self.main_frame = tk.Frame(self, bg='gray')
        self.main_frame.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(self.main_frame, bg='gray', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, side=tk.TOP)
        
        # --- NEW: Settings Bar (Top) ---
        self.settings_bar = tk.Frame(self.main_frame, bg="black")
        self.settings_bar.pack(fill=tk.X, side=tk.TOP)
        
        self.settings_label = tk.Label(
            self.settings_bar, 
            text="Settings: Press [C] to pick Key Color, [R] for Replacement. [P] to Pause.",
            font=("Arial", 10), fg="yellow", bg="black", anchor="w", padx=5, pady=2
        )
        self.settings_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Bottom frame for controls and metrics
        self.bottom_bar = tk.Frame(self.main_frame, bg="black")
        self.bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # UI Elements (Unchanged positioning)
        self.blink_label = tk.Label(self.bottom_bar, text="Blinks: 0", font=("Arial", 12, "bold"), fg="white", bg="black", anchor="w", padx=5, pady=5)
        self.blink_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        
        self.timer_label = tk.Label(self.bottom_bar, text="Time: 0s | BPM: N/A", font=("Arial", 12, "bold"), fg="white", bg="black", anchor="e", padx=5, pady=5)
        self.timer_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.timer_label.bind('<Button-1>', self.reset_counters)
        
        self.exit_button = tk.Button(self.bottom_bar, text="X", command=self.destroy, font=("Arial", 12, "bold"), fg="white", bg="#A00000", activebackground="#C00000", bd=0, width=3 )
        self.exit_button.pack(side=tk.RIGHT, padx=(0, 5), pady=5)

        # --- Bindings ---
        # Bind keyboard shortcuts for color picking and pause
        self.bind('<c>', self.pick_key_color)
        self.bind('<r>', self.pick_replacement_color)
        self.bind('<p>', self.toggle_pause)
        
        # Dragging bindings (updated to include settings_bar)
        self.main_frame.bind('<ButtonPress-1>', self._start_move)
        self.main_frame.bind('<B1-Motion>', self._on_move)
        self.canvas.bind('<ButtonPress-1>', self._start_move)
        self.canvas.bind('<B1-Motion>', self._on_move)
        self.settings_bar.bind('<ButtonPress-1>', self._start_move)
        self.settings_bar.bind('<B1-Motion>', self._on_move)
        
        self.after(REFRESH_RATE_MS, self.run_detection)
        
    # --- NEW: Color Keying Methods ---
    
    def toggle_pause(self, event=None):
        """Pauses the detection and screen capture loop."""
        self.is_paused = not self.is_paused
        status = "PAUSED" if self.is_paused else "RUNNING"
        self.update_settings_display(f"Status: {status}")

    def get_center_color(self):
        """Captures the single pixel color at the center of the frame."""
        width = self.winfo_width()
        height = self.winfo_height()
        x_center = self.winfo_x() + width // 2
        y_center = self.winfo_y() + height // 2
        
        # Grab only the center pixel
        bbox = (x_center, y_center, x_center + 1, y_center + 1)
        screenshot = ImageGrab.grab(bbox)
        
        # Get the color of the single pixel (RGB from PIL)
        color_rgb = screenshot.getpixel((0, 0))
        # Convert to BGR tuple for OpenCV compatibility
        return (color_rgb[2], color_rgb[1], color_rgb[0]) 

    def pick_key_color(self, event=None):
        """Sets the color to be keyed out using the center pixel."""
        self.key_color = self.get_center_color()
        self.update_settings_display(f"Key Color Picked: BGR{self.key_color}")

    def pick_replacement_color(self, event=None):
        """Sets the replacement color using the center pixel."""
        self.replacement_color = self.get_center_color()
        self.update_settings_display(f"Replacement Color Picked: BGR{self.replacement_color}")

    def update_settings_display(self, status=""):
        """Updates the status and color display."""
        k = f"Key: {self.key_color}" if self.key_color else "Key: None"
        r = f"Repl: {self.replacement_color}" if self.replacement_color else "Repl: Transparent"
        p = "PAUSED" if self.is_paused else "RUNNING"
        
        self.settings_label.config(text=f"[{p}] {k} | {r} | Status: {status}")
        
    # --- WINDOW CONTROL METHODS (Unchanged/Refined) ---

    def _start_move(self, event):
        self._drag_x = event.x_root - self.winfo_rootx() 
        self._drag_y = event.y_root - self.winfo_rooty()

    def _on_move(self, event):
        new_x = event.x_root - self._drag_x
        new_y = event.y_root - self._drag_y
        self.geometry(f'+{new_x}+{new_y}')
        
    def reset_counters(self, event):
        self.total_blinks = 0
        self.consec_frames = 0
        self.start_time = time.time()
        self.blink_label.config(text="Blinks: 0")
        self.timer_label.config(text="Time: 0s | BPM: N/A")

    # --- METRIC CALCULATION METHODS (Unchanged) ---
    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def update_timer_and_bpm(self):
        elapsed_time = time.time() - self.start_time
        seconds = int(elapsed_time)
        
        if elapsed_time < 60:
            time_base = 30.0
        else:
            time_base = elapsed_time

        if self.total_blinks > 0 and time_base > 0:
            bpm = (self.total_blinks / time_base) * 60
            bpm_str = f"{bpm:.1f}"
        else:
            bpm_str = "N/A"
            
        self.timer_label.config(text=f"Time: {seconds}s | BPM: {bpm_str}")
        
    # --- DETECTION METHODS ---

    def apply_color_key(self, frame_bgr):
        """Applies chroma keying to the captured frame."""
        if self.key_color is None:
            return frame_bgr # No key color defined, return original

        # Create numpy arrays for the lower and upper BGR bounds
        key_color_np = np.array(self.key_color)
        lower = np.maximum(0, key_color_np - COLOR_KEY_TOLERANCE)
        upper = np.minimum(255, key_color_np + COLOR_KEY_TOLERANCE)

        # Create a mask where the colors fall within the bounds
        mask = cv2.inRange(frame_bgr, lower, upper)
        
        # Invert the mask to get everything *except* the key color
        mask_inv = cv2.bitwise_not(mask)
        
        # Isolate the parts of the image that are *not* the key color
        foreground = cv2.bitwise_and(frame_bgr, frame_bgr, mask=mask_inv)

        # 1. Prepare the background (the keyed out area)
        if self.replacement_color is None:
            # If no replacement color, we key out to TRANSPARENT
            # This requires converting to BGRA and setting alpha to 0 for the keyed area.
            
            # Convert foreground to BGRA (adds an alpha channel)
            frame_bgra = cv2.cvtColor(foreground, cv2.COLOR_BGR2BGRA)
            
            # The mask now defines where the alpha should be 0 (fully transparent)
            frame_bgra[mask > 0, 3] = 0 # Set alpha channel to 0 where mask is present
            
            return frame_bgra
        else:
            # 2. If a replacement color is defined, replace the keyed color with it
            
            # Create a solid color image of the replacement color
            replacement_img = np.full_like(frame_bgr, self.replacement_color, dtype=np.uint8)
            
            # Isolate the areas that *are* the key color
            background = cv2.bitwise_and(replacement_img, replacement_img, mask=mask)
            
            # Combine the foreground (non-keyed parts) and the background (replacement color)
            final_frame = cv2.add(foreground, background)
            
            # Convert final frame to BGRA with full opacity (255) for rendering
            final_frame_bgra = cv2.cvtColor(final_frame, cv2.COLOR_BGR2BGRA)
            final_frame_bgra[:, :, 3] = 255 
            
            return final_frame_bgra

    def capture_screen_area(self):
        """Grabs a screenshot of the pixel area directly under the window."""
        # (Same logic as before, returns BGR frame)
        x_start = self.winfo_x()
        y_start = self.winfo_y()
        width = self.winfo_width()
        height = self.winfo_height()
        
        bbox = (x_start, y_start, x_start + width, y_start + height)
        screenshot = ImageGrab.grab(bbox)
        
        img_np = np.array(screenshot)
        frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR) 
        
        return frame

    def draw_detections(self, frame_bgra, faces, avg_ear):
        """Draws the final processed image on the canvas along with detection boxes."""
        
        # Convert the BGRA numpy array back to a PIL Image (needed for Tkinter PhotoImage)
        # Note: Tkinter can't handle transparency directly on the canvas background, 
        # but we can use the transparency in the image we draw.
        
        # Remove the transparent background property from the Tkinter canvas itself
        self.canvas.config(bg='gray') 
        self.canvas.delete("all") 
        
        # Convert BGRA to RGB for PIL/Tkinter
        frame_rgb = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2RGB)
        
        # Convert numpy array to PIL Image
        img_pil = Image.fromarray(frame_rgb)
        
        # Resize to fit canvas exactly (may not be necessary but good practice)
        img_pil = img_pil.resize((self.canvas.winfo_width(), self.canvas.winfo_height()))
        
        # Convert PIL Image to Tkinter PhotoImage
        self._photo = ImageTk.PhotoImage(image=img_pil)
        
        # Draw the processed image on the canvas
        self.canvas.create_image(0, 0, image=self._photo, anchor=tk.NW)

        # --- Draw Detection Boxes and Landmarks OVER the processed image ---
        
        # We need to re-run Dlib detection on the BGR version of the frame for landmarks
        frame_bgr = frame_bgra[:, :, :3]
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        for (x, y, w, h) in faces:
            # Draw Face Box (Gold)
            self.canvas.create_rectangle(
                x, y, x + w, y + h, 
                outline="#FFD700", width=4 
            )
            
            # Redo Dlib landmark calculation for drawing accurate eye outlines
            rect = dlib.rectangle(x, y, x + w, y + h)
            shape = predictor(gray, rect)
            points = np.array([[p.x, p.y] for p in shape.parts()])
            
            left_eye = points[L_START:L_END]
            right_eye = points[R_START:R_END]

            for hull in [cv2.convexHull(left_eye), cv2.convexHull(right_eye)]:
                poly_points = hull.flatten().tolist()
                
                # Draw the polygon on the Tkinter canvas (Cyan)
                self.canvas.create_polygon(
                    *poly_points, 
                    outline="#00FFFF", 
                    fill="", 
                    width=2
                )
        
        self.process_blinks(avg_ear)


    def process_blinks(self, avg_ear):
        """Checks for eye closure using the accurate EAR value and updates metrics."""
        
        if avg_ear < EYE_AR_THRESH:
            self.consec_frames += 1
        else:
            if self.consec_frames >= EYE_AR_CONSEC_FRAMES:
                self.total_blinks += 1
            
            self.consec_frames = 0
            
        self.blink_label.config(text=f"Blinks: {self.total_blinks}")
        self.update_timer_and_bpm()


    def run_detection(self):
        """The main loop: Capture -> Detect -> Keying -> Draw -> Repeat."""
        
        if self.is_paused:
            # If paused, only update the timer/settings and schedule the next check
            self.update_settings_display("Detection Paused")
            self.after(REFRESH_RATE_MS, self.run_detection)
            return

        frame_bgr = self.capture_screen_area()
        
        # 1. Apply Color Keying/Replacement
        frame_processed = self.apply_color_key(frame_bgr)
        
        # 2. Face Detection
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        avg_ear = 1.0
        if len(faces) > 0:
            # Perform Dlib landmark detection for EAR calculation only on the first face
            (x, y, w, h) = faces[0] 
            rect = dlib.rectangle(x, y, x + w, y + h)
            
            # Predictor needs the original grayscale image
            shape = predictor(gray, rect)
            points = np.array([[p.x, p.y] for p in shape.parts()])
            
            left_eye = points[L_START:L_END]
            right_eye = points[R_START:R_END]
            avg_ear = (self.eye_aspect_ratio(left_eye) + self.eye_aspect_ratio(right_eye)) / 2.0


        # 3. Draw Results
        self.draw_detections(frame_processed, faces, avg_ear)
        self.update_settings_display()
        
        # Schedule the next run
        self.after(REFRESH_RATE_MS, self.run_detection)

if __name__ == "__main__":
    # You must also install PhotoImage support for Pillow:
    # pip install Pillow
    from PIL import ImageTk, Image # Need ImageTk for Tkinter photo compatibility

    app = TransparentDetector()
    app.mainloop()