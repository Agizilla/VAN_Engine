import tkinter as tk
from tkinter import ttk
import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist
from imutils import face_utils
import os
import threading
import time

# --- Configuration Constants ---
EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 3

# --- Blink Detection Utility Functions ---

def eye_aspect_ratio(eye):
    """Calculates the Eye Aspect Ratio (EAR) for blink detection."""
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# --- Main Application Class ---

class RealTimeBlinkCounterApp:
    def __init__(self, master):
        self.master = master
        master.title("Expert Real-Time Blink Counter")
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Dlib Initialization with Robust Pathing ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        predictor_path = os.path.join(script_dir, "shape_predictor_68_face_landmarks.dat")

        self.detector = dlib.get_frontal_face_detector()
        
        try:
            self.predictor = dlib.shape_predictor(predictor_path)
            print(f"INFO: Loaded predictor from: {predictor_path}")
        except RuntimeError as e:
            print(f"ERROR: Predictor file not found at: {predictor_path}")
            master.destroy()
            return

        (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

        self.face_trackers = {}
        self.running = False
        self.cap = None
        self.thread = None

        # --- Tkinter GUI Setup (Simplified for controls) ---
        self.main_frame = ttk.Frame(master, padding="10")
        self.main_frame.pack(fill='both', expand=True)

        self.status_label = ttk.Label(self.main_frame, text="Status: Ready | Blinks: 0", font=('Arial', 12, 'bold'))
        self.status_label.pack(pady=10)

        self.start_btn = ttk.Button(self.main_frame, text="Start Camera & Analysis", command=self.start_processing)
        self.start_btn.pack(pady=5, fill='x')
        
        self.stop_btn = ttk.Button(self.main_frame, text="Stop Camera", command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(pady=5, fill='x')
        
        # Display window name for OpenCV (needed for closing)
        self.cv_window_name = "Real-Time Face Analysis (OpenCV)"

    def get_total_blinks(self):
        """Calculates the total blink count across all tracked faces."""
        return sum(tracker['BLINKS'] for tracker in self.face_trackers.values())

    def start_processing(self):
        """Initializes video capture and starts the processing loop in a separate thread."""
        if self.running:
            return

        self.cap = cv2.VideoCapture(0) # 0 is typically the default webcam
        if not self.cap.isOpened():
            self.status_label.config(text="Status: ERROR - Could not open camera.")
            return

        self.running = True
        self.face_trackers = {} # Reset state
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Start the analysis loop in a separate thread to prevent GUI freezing
        self.thread = threading.Thread(target=self.process_loop)
        self.thread.daemon = True
        self.thread.start()
        
        self.status_label.config(text="Status: Running | Blinks: 0")

    def stop_processing(self):
        """Stops the processing loop, releases the camera, and closes the CV window."""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        
        cv2.destroyAllWindows()
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.status_label.config(text=f"Status: Stopped. Final Blinks: {self.get_total_blinks()}")

    def on_closing(self):
        """Handles graceful shutdown when the Tkinter window is closed."""
        self.stop_processing()
        self.master.destroy()

    def process_loop(self):
        """The main real-time processing loop for camera frames."""
        
        # Set the target window resolution (optional, adjust for speed/quality)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01) # Wait briefly if frame is not ready
                continue

            # Flip the frame horizontally for a more natural mirror view
            frame = cv2.flip(frame, 1)

            # Use a copy of the color frame for drawing and final display
            display_frame = frame.copy() 

            # Grayscale Conversion: ONLY for dlib detection
            gray = cv2.cvtColor(display_frame, cv2.COLOR_BGR2GRAY)

            # Detect faces in the grayscale frame
            rects = self.detector(gray, 0)
            
            new_face_trackers = {}

            for (i, rect) in enumerate(rects):
                (x, y, w, h) = face_utils.rect_to_bb(rect)
                face_key = rect # Use dlib rect as key

                # Get or initialize the tracker state
                if face_key in self.face_trackers:
                    tracker_state = self.face_trackers[face_key]
                else:
                    tracker_state = {'CONSEC_FRAMES': 0, 'BLINKS': 0}
                
                new_face_trackers[face_key] = tracker_state

                # Facial landmarks using the grayscale image
                shape = self.predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)

                leftEye = shape[self.lStart:self.lEnd]
                rightEye = shape[self.rStart:self.rEnd]

                leftEAR = eye_aspect_ratio(leftEye)
                rightEAR = eye_aspect_ratio(rightEye)
                ear = (leftEAR + rightEAR) / 2.0

                # Draw the face bounding box on the COLOR frame
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Blink Logic
                if ear < EYE_AR_THRESH:
                    tracker_state['CONSEC_FRAMES'] += 1
                else:
                    if tracker_state['CONSEC_FRAMES'] >= EYE_AR_CONSEC_FRAMES:
                        tracker_state['BLINKS'] += 1
                    tracker_state['CONSEC_FRAMES'] = 0

                # Display the blink count and EAR
                blink_text = f"Blinks: {tracker_state['BLINKS']}"
                cv2.putText(display_frame, blink_text, (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                ear_text = f"EAR: {ear:.2f}"
                cv2.putText(display_frame, ear_text, (x, y + h + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            self.face_trackers = new_face_trackers
            
            # Update the Tkinter status label (needs to be done safely, though simple update is usually fine)
            self.master.after(0, lambda: self.status_label.config(
                text=f"Status: Running | Total Blinks: {self.get_total_blinks()} | Faces: {len(self.face_trackers)}"))

            # Display the frame in the OpenCV window
            cv2.imshow(self.cv_window_name, display_frame)
            
            # Check for window close event or key press (must be done in a loop using cv2.waitKey)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.master.after(0, self.stop_processing) # Trigger stop on main thread
                break
        
        # Ensure cleanup if loop exits
        self.stop_processing()


# --- Run the Application ---
if __name__ == "__main__":
    root = tk.Tk()
    # To achieve a "transparent" look, you can make the Tkinter window itself very small
    # and use the simple OpenCV window as the main visual feedback.
    # To hide the TK window: root.wm_attributes('-alpha', 0.0)
    app = RealTimeBlinkCounterApp(root)
    root.mainloop()