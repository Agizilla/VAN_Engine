import cv2
import dlib
import numpy as np
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICTOR_PATH = os.path.join(SCRIPT_DIR, "shape_predictor_68_face_landmarks.dat")
WATCH_PATH = r"C:\Users\User\Pictures\!Faces"

class GhostMachine:
    def __init__(self):
        if not os.path.exists(PREDICTOR_PATH):
            print("ERROR: Model missing."); exit()

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(PREDICTOR_PATH)

        # Texture and Geometry Buffers
        self.crops = []  # Stores raw face crops
        self.sum_landmarks = np.zeros((68, 2), dtype=np.float32)
        self.seen_count = np.zeros(68, dtype=np.int32)
        
        self.canvas_size = (800, 800)
        self.tex_size = (400, 400) # Slightly larger crop for better detail
        self.window_name = "The Averaged Soul"

    def process_image(self, img_path):
        frame = cv2.imread(img_path)
        if frame is None: return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)

        for face in faces:
            # 1. Grab raw landmarks
            landmarks = self.predictor(gray, face)
            for i in range(68):
                pt = landmarks.part(i)
                self.sum_landmarks[i] += [float(pt.x), float(pt.y)]
                self.seen_count[i] += 1

            # 2. Grab the "Flesh": Crop the face bounding box
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            # Safety padding to avoid going out of frame
            y1, y2 = max(0, y), min(frame.shape[0], y+h)
            x1, x2 = max(0, x), min(frame.shape[1], x+w)
            
            crop = frame[y1:y2, x1:x2]
            if crop.size > 0:
                # Resize all crops to a standard size for averaging
                crop_res = cv2.resize(crop, self.tex_size)
                self.crops.append(crop_res.astype(np.float32))

            self.render_all()
            print(f"Fused: {os.path.basename(img_path)} (Total: {len(self.crops)})")
            break

    def render_all(self):
        if not self.crops: return

        # 1. Generate Mean Skin Texture
        skin_texture = np.mean(self.crops, axis=0).astype(np.uint8)
        # Stretch texture to fill canvas
        skin_full = cv2.resize(skin_texture, self.canvas_size, interpolation=cv2.INTER_LINEAR)

        # 2. Generate Wireframe Bone
        line_canvas = np.zeros((self.canvas_size[1], self.canvas_size[0], 3), dtype=np.uint8)
        avg_pts_raw = self.sum_landmarks / self.seen_count.reshape(-1, 1)
        
        # Proportional scaling for wireframe
        x_min, x_max = avg_pts_raw[:,0].min(), avg_pts_raw[:,1].max()
        y_min, y_max = avg_pts_raw[:,1].min(), avg_pts_raw[:,1].max()
        scale = min((self.canvas_size[0]*0.75)/(x_max-x_min+1e-6), (self.canvas_size[1]*0.75)/(y_max-y_min+1e-6))
        mean_pt = np.mean(avg_pts_raw, axis=0)
        pts = ((avg_pts_raw - mean_pt) * scale + [400, 400]).astype(np.int32)

        # Draw lines on black canvas
        cv2.polylines(line_canvas, [pts[0:17]], False, (255, 255, 255), 2, cv2.LINE_AA) # Jaw
        cv2.polylines(line_canvas, [pts[17:22]], False, (255, 255, 255), 2, cv2.LINE_AA) # Brows
        cv2.polylines(line_canvas, [pts[22:27]], False, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.circle(line_canvas, tuple(pts[36]), 10, (255, 255, 255), 2) # Eyes
        cv2.circle(line_canvas, tuple(pts[45]), 10, (255, 255, 255), 2)
        cv2.circle(line_canvas, tuple(pts[30]), 5, (255, 255, 255), -1) # Nose

        # 3. BLEND: 0.7 Texture + 0.3 Wireframe
        # Note: Line canvas is black (0,0,0) where there are no lines, so it won't darken skin
        final_view = cv2.addWeighted(skin_full, 0.7, line_canvas, 0.3, 0)

        cv2.imshow(self.window_name, final_view)
        cv2.waitKey(1)

class ImageHandler(FileSystemEventHandler):
    def __init__(self, app): self.app = app
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.jpg', '.png', '.webp')):
            time.sleep(0.5)
            self.app.process_image(event.src_path)

if __name__ == "__main__":
    if not os.path.exists(WATCH_PATH): os.makedirs(WATCH_PATH)
    app = GhostMachine()
    observer = Observer()
    observer.schedule(ImageHandler(app), WATCH_PATH, recursive=False)
    observer.start()

    print(f"Averaging love at: {WATCH_PATH}")
    try:
        while cv2.waitKey(1) != 27:
            time.sleep(0.1)
    except KeyboardInterrupt: pass
    finally:
        observer.stop(); observer.join(); cv2.destroyAllWindows()