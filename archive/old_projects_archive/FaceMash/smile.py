import cv2
import dlib
import numpy as np
import os
import time

class FaceInnovatorPro:
    def __init__(self, image_path):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
        self.original_img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        
        if self.original_img is None:
            raise ValueError(f"Could not load {image_path}")

        self.h, self.w = self.original_img.shape[:2]
        self.landmarks = self._get_landmarks(self.original_img)
        self.face_center = np.mean(self.landmarks, axis=0)
        self.face_width = np.linalg.norm(self.landmarks[0] - self.landmarks[16])

    def _get_landmarks(self, img):
        # Handle 4-channel PNG for dlib
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY) if img.shape[2] == 4 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 1)
        if not rects: raise Exception("No face detected.")
        shape = self.predictor(gray, rects[0])
        return np.array([[p.x, p.y] for p in shape.parts()])

    def apply_complex_deformation(self, smile, eye_size, rot, blink, wink, talk_offset):
        rows, cols = np.indices((self.h, self.w), dtype=np.float32)
        map_x, map_y = cols.copy(), rows.copy()
        
        # 1. NECK ROTATION (Coordinate Transformation)
        # We rotate the sampling grid in the opposite direction
        angle = (rot - 50) * 0.2  # Degree range
        pivot = self.landmarks[8] # Chin as pivot point
        
        # Create a weight mask so only the head rotates, not the background
        dist_from_pivot = np.sqrt((cols - pivot[0])**2 + (rows - pivot[1])**2)
        rot_weight = np.clip(1.0 - (dist_from_pivot / (self.face_width * 1.5)), 0, 1)
        
        rad = np.radians(angle)
        cos_a, sin_a = np.cos(rad), np.sin(rad)
        
        # Adjust mapping for rotation
        tx = cols - pivot[0]
        ty = rows - pivot[1]
        map_x = pivot[0] + (tx * cos_a - ty * sin_a) * rot_weight + tx * (1 - rot_weight)
        map_y = pivot[1] + (tx * sin_a + ty * cos_a) * rot_weight + ty * (1 - rot_weight)

        # 2. LOCAL LANDMARK MANIPULATION (Smile, Eyes, Talk)
        indices, vectors = [], []
        
        # Smile
        s_s = smile / 100.0
        indices.extend([48, 54])
        vectors.extend([[-15 * s_s, -15 * s_s], [15 * s_s, -15 * s_s]])

        # Blink & Wink Logic
        # Left Eye: 37, 38 (Top) | Right Eye: 43, 44 (Top)
        l_blink = max(blink, wink if wink > 0 else 0) / 100.0
        r_blink = blink / 100.0
        
        indices.extend([37, 38, 43, 44])
        vectors.extend([[0, 12 * l_blink], [0, 12 * l_blink], [0, 12 * r_blink], [0, 12 * r_blink]])

        # Eye Size (Scale)
        e_s = (eye_size - 50) / 50.0
        for i in [37, 38, 40, 41, 43, 44, 46, 47]:
            direction = -1 if i in [37, 38, 43, 44] else 1
            indices.append(i)
            vectors.append([0, direction * 8 * e_s])

        # Talk
        if talk_offset > 0:
            for i in [57, 62, 66, 8]:
                indices.append(i)
                vectors.append([0, talk_offset])

        # Apply displacement to the already rotated map
        radius = self.face_width / 8
        for idx, vec in zip(indices, vectors):
            dx, dy = map_x - self.landmarks[idx][0], map_y - self.landmarks[idx][1]
            weight = np.exp(-(dx**2 + dy**2) / (2 * radius**2))
            map_x -= weight * vec[0]
            map_y -= weight * vec[1]

        return cv2.remap(self.original_img, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# --- UI Setup ---
img_file = next((f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))), None)
engine = FaceInnovatorPro(img_file)
cv2.namedWindow("Control Dashboard")

def n(x): pass
cv2.createTrackbar("Smile", "Control Dashboard", 0, 100, n)
cv2.createTrackbar("Eye Size", "Control Dashboard", 50, 100, n)
cv2.createTrackbar("Rotation", "Control Dashboard", 50, 100, n)
cv2.createTrackbar("Blink", "Control Dashboard", 0, 100, n)
cv2.createTrackbar("Wink (L)", "Control Dashboard", 0, 100, n)
cv2.createTrackbar("Talk", "Control Dashboard", 0, 1, n)



while True:
    s = cv2.getTrackbarPos("Smile", "Control Dashboard")
    e = cv2.getTrackbarPos("Eye Size", "Control Dashboard")
    r = cv2.getTrackbarPos("Rotation", "Control Dashboard")
    b = cv2.getTrackbarPos("Blink", "Control Dashboard")
    w = cv2.getTrackbarPos("Wink (L)", "Control Dashboard")
    talking = cv2.getTrackbarPos("Talk", "Control Dashboard") == 1
    
    t_off = int(np.sin(time.time() * 18) * 15 + 15) if talking else 0

    frame = engine.apply_complex_deformation(s, e, r, b, w, t_off)
    cv2.imshow("Control Dashboard", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cv2.destroyAllWindows()