import cv2
import dlib
import numpy as np
import os
import time

class UnifiedFaceEngine:
    def __init__(self, predictor_path):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        
        # State
        self.points_3d = None
        self.base_lms = None
        self.texture_atlas = None
        self.yaw, self.pitch = 0.0, 0.0
        self.is_dragging = False
        self.last_mouse = (0, 0)
        
        # UI Params
        self.depth_mult = 0.8
        self.smile_factor = 0
        
        # Create standard triangulation for 68 points
        self.triangles = self._get_full_mesh()
        self.load_model()

    def _get_full_mesh(self):
        # A more robust triangle set to fill the face surface
        # Using a list of point indices (0-67)
        tri_list = [
            # Jaw and Cheeks
            (0,1,36), (1,2,36), (2,3,31), (3,4,31), (4,5,48), (5,6,48), (6,7,58), (7,8,58),
            (8,9,57), (9,10,56), (10,11,54), (11,12,54), (12,13,45), (13,14,45), (14,15,46), (15,16,46),
            # Nose
            (27,31,30), (27,35,30), (31,32,30), (32,33,30), (33,34,30), (34,35,30),
            # Eyes/Brows
            (17,18,36), (19,20,38), (21,27,39), (22,27,42), (24,25,45),
            # Mouth
            (48,49,60), (49,50,61), (50,51,62), (51,52,63), (52,53,64), (54,55,64), (55,56,65)
        ]
        return tri_list

    def load_model(self):
        if os.path.exists("3D/points.npy") and os.path.exists("3D/texture.png"):
            self.points_3d = np.load("3D/points.npy")
            self.texture_atlas = cv2.imread("3D/texture.png")
            self.base_lms = np.load("3D/base_lms.npy")
            print("Loaded persisted head.")

    def warp_triangle(self, src, dst, tri_src, tri_dst):
        # Professional Affine Warp with boundary handling
        r1 = cv2.boundingRect(np.float32([tri_src]))
        r2 = cv2.boundingRect(np.float32([tri_dst]))
        
        # Offset triangles to local bounding box coordinates
        t1_rect = [(p[0] - r1[0], p[1] - r1[1]) for p in tri_src]
        t2_rect = [(p[0] - r2[0], p[1] - r2[1]) for p in tri_dst]
        
        mask = np.zeros((r2[3], r2[2], 3), dtype=np.float32)
        cv2.fillConvexPoly(mask, np.int32(t2_rect), (1.0, 1.0, 1.0), 16, 0)
        
        src_rect = src[r1[1]:r1[1]+r1[3], r1[0]:r1[0]+r1[2]]
        warp_mat = cv2.getAffineTransform(np.float32(t1_rect), np.float32(t2_rect))
        dst_rect = cv2.warpAffine(src_rect, warp_mat, (r2[2], r2[3]), None, 
                                 flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        
        # Place warped triangle into destination image
        dst_rect = dst_rect * mask
        dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] * (1-mask) + dst_rect

    def render(self, w, h):
        if self.points_3d is None or self.texture_atlas is None:
            return np.zeros((h, w, 3), dtype=np.uint8)

        # 3D Matrix Calculation
        rad_y, rad_x = self.yaw, self.pitch
        rmat_y = np.array([[np.cos(rad_y), 0, np.sin(rad_y)], [0, 1, 0], [-np.sin(rad_y), 0, np.cos(rad_y)]])
        rmat_x = np.array([[1, 0, 0], [0, np.cos(rad_x), -np.sin(rad_x)], [0, np.sin(rad_x), np.cos(rad_x)]])
        rmat = (rmat_y @ rmat_x).astype(np.float32)

        # Apply user depth tuning
        points = self.points_3d.copy()
        points[:, 2] *= self.depth_mult 
        
        projected = points @ rmat.T
        scale = 1.8
        pts_2d_dest = (projected[:, :2] * scale + np.array([w//2, h//2])).astype(np.float32)
        
        output = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Render the 'Solid' Mesh
        for tri_idx in self.triangles:
            try:
                t_src = [self.base_lms[i] for i in tri_idx]
                t_dst = [pts_2d_dest[i] for i in tri_idx]
                self.warp_triangle(self.texture_atlas, output, t_src, t_dst)
            except: continue
        return output

# --- UI Setup ---
def on_change(x): pass

engine = UnifiedFaceEngine("shape_predictor_68_face_landmarks.dat")
cap = cv2.VideoCapture("face_video.mp4") # Or use 0 for Webcam
cv2.namedWindow("Innovator Dashboard")

# Reintroducing the Dashboard Controls
cv2.createTrackbar("3D Depth", "Innovator Dashboard", 80, 200, on_change)
cv2.createTrackbar("Smile Scale", "Innovator Dashboard", 0, 100, on_change)
cv2.createTrackbar("Reset", "Innovator Dashboard", 0, 1, on_change)

def mouse_handler(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN: engine.is_dragging = True; engine.last_mouse = (x, y)
    elif event == cv2.EVENT_LBUTTONUP: engine.is_dragging = False
    elif event == cv2.EVENT_MOUSEMOVE and engine.is_dragging:
        engine.yaw += (x - engine.last_mouse[0]) * 0.01
        engine.pitch += (y - engine.last_mouse[1]) * 0.01
        engine.last_mouse = (x, y)

cv2.setMouseCallback("Innovator Dashboard", mouse_handler)



while True:
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # UI updates
    engine.depth_mult = cv2.getTrackbarPos("3D Depth", "Innovator Dashboard") / 100.0
    if cv2.getTrackbarPos("Reset", "Innovator Dashboard") == 1:
        engine.yaw, engine.pitch = 0, 0
        cv2.setTrackbarPos("Reset", "Innovator Dashboard", 0)

    # Tracking
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = engine.detector(gray, 0)
    if rects:
        shape = engine.predictor(frame, rects[0])
        lms = np.array([[p.x, p.y] for p in shape.parts()], dtype=np.float32)
        
        # Only update the 'Base' if we don't have one yet, or if it's much better
        if engine.base_lms is None:
            engine.base_lms = lms
            engine.texture_atlas = frame.copy()
            
        # Update 3D coordinates from current frame
        center = np.mean(lms, axis=0)
        z = np.zeros((68, 1), dtype=np.float32)
        for i in range(68):
            z[i] = -np.linalg.norm(lms[i] - lms[30]) 
        engine.points_3d = np.hstack((lms - center, z))

    # Render
    head_render = engine.render(frame.shape[1], frame.shape[0])
    
    # Save folder "3D" logic
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        if not os.path.exists("3D"): os.makedirs("3D")
        np.save("3D/points.npy", engine.points_3d)
        np.save("3D/base_lms.npy", engine.base_lms)
        cv2.imwrite("3D/texture.png", engine.texture_atlas)
        print("Model Saved.")
    
    cv2.imshow("Innovator Dashboard", np.hstack((frame, head_render)))
    if key == ord('q'): break

cap.release()
cv2.destroyAllWindows()