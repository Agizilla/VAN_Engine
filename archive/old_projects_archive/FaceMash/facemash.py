import cv2
import dlib
import numpy as np
import os
import time
import imageio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICTOR_PATH = os.path.join(SCRIPT_DIR, "shape_predictor_68_face_landmarks.dat")
WATCH_PATH = r"C:\Users\User\Pictures\!Faces"
GIF_PATH = os.path.join(SCRIPT_DIR, "evolution.gif")

class FaceAverageApp:
    def __init__(self):
        if not os.path.exists(PREDICTOR_PATH):
            print(f"ERROR: Model not found at {PREDICTOR_PATH}")
            exit()

        print("Initializing dlib...")
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(PREDICTOR_PATH)

        # Core Data
        self.sum_landmarks = np.zeros((68, 2), dtype=np.float32)
        self.seen_count = np.zeros(68, dtype=np.int32)
        self.history = []  # Memory-safe downscaled frames for slider/GIF
        self.data_history = [] # Raw (avg_pts, counts)
        
        self.canvas_size = (800, 800)
        self.window_name = "Evolving Heatmap Face"
        cv2.namedWindow(self.window_name)
        
        cv2.createTrackbar("Evolution", self.window_name, 0, 0, self.on_slider)
        self.draw_placeholder()

    def on_slider(self, val):
        if not self.history: return
        idx = min(val, len(self.history) - 1)
        # Upscale for viewing if needed, but display is usually fine at 400x400
        cv2.imshow(self.window_name, self.history[idx])

    def process_image(self, img_path):
        frame = cv2.imread(img_path)
        if frame is None: return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)

        if len(faces) == 0:
            print(f"Skipped: No face detected in {os.path.basename(img_path)}")
            return

        for face in faces:
            landmarks = self.predictor(gray, face)
            for i in range(68):
                pt = landmarks.part(i)
                if pt.x != 0 and pt.y != 0:
                    self.sum_landmarks[i] += [float(pt.x), float(pt.y)]
                    self.seen_count[i] += 1
            
            # 1. Feature-Specific Interpolation
            avg_pts = self.compute_interpolated_avg()
            
            # 2. Render and Downscale (save RAM: 800x800 -> 400x400)
            rendered = self.render(avg_pts, self.seen_count.copy(), len(self.history) + 1)
            small_frame = cv2.resize(rendered, (400, 400), interpolation=cv2.INTER_AREA)
            
            self.history.append(small_frame)
            self.data_history.append((avg_pts.copy(), self.seen_count.copy()))
            
            # 3. Update UI
            max_idx = len(self.history) - 1
            cv2.setTrackbarMax("Evolution", self.window_name, max_idx)
            cv2.setTrackbarPos("Evolution", self.window_name, max_idx)
            cv2.imshow(self.window_name, rendered)
            print(f"Processed #{len(self.history)}: {os.path.basename(img_path)}")
            break

    def compute_interpolated_avg(self):
        avg_pts = np.zeros((68, 2), dtype=np.float32)
        for i in range(68):
            if self.seen_count[i] > 0:
                avg_pts[i] = self.sum_landmarks[i] / self.seen_count[i]

        for i in range(68):
            if self.seen_count[i] == 0:
                # Anatomical logic
                if 36 <= i <= 41: p1, p2 = avg_pts[36], avg_pts[39]
                elif 42 <= i <= 47: p1, p2 = avg_pts[42], avg_pts[45]
                elif 48 <= i <= 59: p1, p2 = avg_pts[48], avg_pts[54]
                elif 60 <= i <= 67: p1, p2 = avg_pts[60], avg_pts[64]
                elif 31 <= i <= 35: p1, p2 = avg_pts[31], avg_pts[35]
                else: p1, p2 = avg_pts[(i-1)%68], avg_pts[(i+1)%68]
                
                # Robust check against zero-vectors
                if np.any(p1 != 0) or np.any(p2 != 0):
                    avg_pts[i] = (p1 + p2) / 2
                else:
                    avg_pts[i] = [400, 400]
        return avg_pts

    def render(self, avg_pts, counts, total_count):
        w, h = self.canvas_size
        canvas = np.ones((h, w, 3), dtype=np.uint8) * 255
        safe_total = max(total_count, 1)

        # Consistent scaling with epsilon to prevent div-by-zero
        x_min, x_max = avg_pts[:,0].min(), avg_pts[:,0].max()
        y_min, y_max = avg_pts[:,1].min(), avg_pts[:,1].max()
        scale = min((w*0.75)/(x_max-x_min+1e-6), (h*0.75)/(y_max-y_min+1e-6))
        
        mean_pt = np.mean(avg_pts, axis=0)
        pts = ((avg_pts - mean_pt) * scale + [w//2, h//2]).astype(np.int32)

        # Drawing
        cv2.polylines(canvas, [pts[0:17]], False, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.polylines(canvas, [pts[17:22]], False, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.polylines(canvas, [pts[22:27]], False, (0, 0, 0), 2, cv2.LINE_AA)

        anchor_indices = [36, 45, 30, 48, 54] 
        for idx in anchor_indices:
            ratio = counts[idx] / safe_total
            color = (0, int(255 * ratio), int(255 * (1 - ratio)))
            cv2.circle(canvas, tuple(pts[idx]), 12, color, -1 if idx == 30 else 2, cv2.LINE_AA)

        cv2.putText(canvas, f"Averaged: {total_count}", (30, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
        return canvas

    def draw_placeholder(self):
        canvas = np.ones((800, 800, 3), dtype=np.uint8) * 255
        cv2.putText(canvas, "Drop images into !Faces", (200, 400), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (180,180,180), 2)
        cv2.imshow(self.window_name, canvas)
        cv2.waitKey(1)

    def save_gif(self):
        if not self.history: return
        print("Finalizing evolution.gif (15 FPS)...")
        # Frames are already small (400x400) from the history buffer
        gif_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in self.history]
        imageio.mimsave(GIF_PATH, gif_frames, fps=15)
        print(f"Saved to: {GIF_PATH}")

class ImageHandler(FileSystemEventHandler):
    def __init__(self, app): self.app = app
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.jpg', '.png', '.webp')):
            time.sleep(0.5)
            self.app.process_image(event.src_path)

if __name__ == "__main__":
    if not os.path.exists(WATCH_PATH): os.makedirs(WATCH_PATH)
    app = FaceAverageApp()
    handler = ImageHandler(app)
    
    observer = Observer()
    observer.schedule(handler, WATCH_PATH, recursive=False)
    observer.start()

    print(f"Monitoring: {WATCH_PATH}. Press ESC to finish.")

    try:
        while True:
            if cv2.waitKey(1) == 27: break
            time.sleep(1)
            print("Tick")
    except KeyboardInterrupt: pass
    finally:
        app.save_gif()
        observer.stop()
        observer.join()
        cv2.destroyAllWindows()