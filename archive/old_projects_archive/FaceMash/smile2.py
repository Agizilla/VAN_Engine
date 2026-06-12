import cv2
import dlib
import numpy as np
import os
import time

class FaceArchitectPro:
    def __init__(self, predictor_path):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        
        # 3D State
        self.points_3d = None
        self.yaw, self.pitch = 0, 0
        self.is_dragging = False
        self.last_mouse = (0, 0)
        self.rotation_matrix = np.eye(3, dtype=np.float32)

    def get_data(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 0)
        if not rects: return None
        shape = self.predictor(gray, rects[0])
        return np.array([[p.x, p.y] for p in shape.parts()], dtype=np.float32)

    def update_3d_model(self, lms):
        # Center landmarks and estimate Z (Depth)
        center = np.mean(lms, axis=0)
        centered = lms - center
        
        # Depth heuristic: nose is prominent (Z=0), ears are recessed
        nose_tip = lms[30]
        z = np.zeros((68, 1), dtype=np.float32)
        for i in range(68):
            dist = np.linalg.norm(lms[i] - nose_tip)
            z[i] = -dist * 0.6  # Depth scaling factor
            
        self.points_3d = np.hstack((centered, z))

    def get_rotation_matrix(self):
        rx = np.array([[1, 0, 0],
                       [0, np.cos(self.pitch), -np.sin(self.pitch)],
                       [0, np.sin(self.pitch), np.cos(self.pitch)]], dtype=np.float32)
        ry = np.array([[np.cos(self.yaw), 0, np.sin(self.yaw)],
                       [0, 1, 0],
                       [-np.sin(self.yaw), 0, np.cos(self.yaw)]], dtype=np.float32)
        return ry @ rx

    def render(self, w, h):
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        if self.points_3d is None: return canvas
        
        # Project 3D -> 2D
        rmat = self.get_rotation_matrix()
        projected = (self.points_3d @ rmat.T)
        
        # Scale and Offset to center of canvas
        scale = 1.5
        pts_2d = (projected[:, :2] * scale + np.array([w//2, h//2])).astype(np.int32)
        
        # Draw Mesh Connections (Jaw, Brows, Nose, Eyes, Mouth)
        for start, end in [(0,16), (17,21), (22,26), (27,30), (30,35), (36,41), (42,47), (48,59)]:
            for i in range(start, end):
                cv2.line(canvas, tuple(pts_2d[i]), tuple(pts_2d[i+1]), (0, 255, 150), 1)
        return canvas

# --- Mouse Interaction ---
def mouse_ctrl(event, x, y, flags, param):
    obj = param
    if event == cv2.EVENT_LBUTTONDOWN:
        obj.is_dragging = True
        obj.last_mouse = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        obj.is_dragging = False
    elif event == cv2.EVENT_MOUSEMOVE and obj.is_dragging:
        obj.yaw += (x - obj.last_mouse[0]) * 0.01
        obj.pitch += (y - obj.last_mouse[1]) * 0.01
        obj.last_mouse = (x, y)

# --- Execution ---
video_file = "face_video.mp4" # Ensure this exists
if not os.path.exists(video_file):
    print(f"Error: {video_file} not found. Put a video in the root folder.")
    exit()

architect = FaceArchitectPro("shape_predictor_68_face_landmarks.dat")
cap = cv2.VideoCapture(video_file)
cv2.namedWindow("Reconstruction Dashboard")
cv2.setMouseCallback("Reconstruction Dashboard", mouse_ctrl, architect)

while True:
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
        continue

    lms = architect.get_data(frame)
    if lms is not None:
        architect.update_3d_model(lms)

    # Render side-by-side
    h, w = frame.shape[:2]
    render_view = architect.render(w, h)
    combined = np.hstack((frame, render_view))
    
    # Resize for display if too large
    display_w = 1200
    aspect = combined.shape[0] / combined.shape[1]
    cv2.imshow("Reconstruction Dashboard", cv2.resize(combined, (display_w, int(display_w * aspect))))
    
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()