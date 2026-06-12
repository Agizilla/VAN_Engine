import cv2
import dlib
import numpy as np
import os
import time
from scipy.spatial import Delaunay

class UnifiedFaceEngine:
    def __init__(self, predictor_path):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        
        # State for incremental updates
        self.points_3d = None
        self.base_lms = None
        self.texture_atlas = None
        self.uv_map = None
        self.yaw, self.pitch, self.roll = 0.0, 0.0, 0.0
        self.is_dragging = False
        self.last_mouse = (0, 0)
        
        # UI Params
        self.depth_mult = 0.8
        self.smile_factor = 0
        
        # Triangles computed dynamically
        self.triangles = None
        
        # 3D model points for PnP
        self.model_points = np.array([
            (0.0, 0.0, 0.0),  # Nose tip
            (0.0, -330.0, -65.0),  # Chin
            (-225.0, 170.0, -135.0),  # Left eye left corner
            (225.0, 170.0, -135.0),  # Right eye right corner
            (-150.0, -150.0, -125.0),  # Left Mouth corner
            (150.0, -150.0, -125.0)   # Right mouth corner
        ], dtype=np.float64)
        
        self.load_model()
    
    def load_model(self):
        if os.path.exists("3D/points.npy") and os.path.exists("3D/texture.png"):
            self.points_3d = np.load("3D/points.npy")
            self.texture_atlas = cv2.imread("3D/texture.png")
            self.base_lms = np.load("3D/base_lms.npy")
            if os.path.exists("3D/uv_map.npy"):
                self.uv_map = np.load("3D/uv_map.npy")
            if self.base_lms is not None:
                self.triangles = Delaunay(self.base_lms).simplices
            print("Loaded persisted head.")
        else:
            # Initialize UV map (simple placeholder)
            self.uv_map = np.random.rand(68, 2)  # Replace with standard UV if needed
    
    def estimate_head_pose(self, lms):
        image_points = np.array([
            lms[30], lms[8], lms[36], lms[45], lms[48], lms[54]
        ], dtype=np.float64)
        
        camera_matrix = np.array([[500, 0, 320], [0, 500, 240], [0, 0, 1]], dtype=np.float64)
        dist_coeffs = np.zeros((4,1))
        
        _, rotation_vec, _ = cv2.solvePnP(self.model_points, image_points, camera_matrix, dist_coeffs)
        rotation_mat, _ = cv2.Rodrigues(rotation_vec)
        euler_angles = cv2.RQDecomp3x3(rotation_mat)[0]
        return euler_angles  # yaw, pitch, roll
    
    def update_model(self, frame, lms, pose):
        if self.points_3d is None:
            center = np.mean(lms, axis=0)
            z = np.zeros((68, 1), dtype=np.float32)
            for i in range(68):
                z[i] = -np.linalg.norm(lms[i] - lms[30]) * self.depth_mult
            self.points_3d = np.hstack((lms - center, z))
            self.base_lms = lms
            self.texture_atlas = frame.copy()
            self.triangles = Delaunay(self.base_lms).simplices
            return
        
        # Blend texture for visible parts
        alpha = 0.5
        visible_mask = self.get_visible_points(pose)
        for i in np.where(visible_mask)[0]:
            # Simplified blending (expand for proper UV)
            self.texture_atlas = cv2.addWeighted(self.texture_atlas, alpha, frame, 1 - alpha, 0)
    
    def get_visible_points(self, pose):
        # Placeholder: improve with normals
        return np.ones(68, dtype=bool)
    
    def warp_triangle(self, src, dst, tri_src, tri_dst):
        r1 = cv2.boundingRect(np.float32([tri_src]))
        r2 = cv2.boundingRect(np.float32([tri_dst]))
        t1_rect = [(p[0] - r1[0], p[1] - r1[1]) for p in tri_src]
        t2_rect = [(p[0] - r2[0], p[1] - r2[1]) for p in tri_dst]
        mask = np.zeros((r2[3], r2[2], 3), dtype=np.float32)
        cv2.fillConvexPoly(mask, np.int32(t2_rect), (1.0, 1.0, 1.0))
        src_rect = src[r1[1]:r1[1]+r1[3], r1[0]:r1[0]+r1[2]]
        warp_mat = cv2.getAffineTransform(np.float32(t1_rect), np.float32(t2_rect))
        dst_rect = cv2.warpAffine(src_rect, warp_mat, (r2[2], r2[3]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT_101)
        
        # Blended assignment in float space
        slice_dst = dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]]
        temp = slice_dst.astype(np.float32) * (1 - mask) + dst_rect.astype(np.float32) * mask
        dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = np.clip(temp, 0, 255).astype(np.uint8)
    
    def render(self, w, h):
        if self.points_3d is None or self.texture_atlas is None or self.triangles is None:
            return np.zeros((h, w, 3), dtype=np.uint8)
        
        # Rotation matrix
        rad_y, rad_p, rad_r = np.deg2rad(self.yaw), np.deg2rad(self.pitch), np.deg2rad(self.roll)
        rmat_y = np.array([[np.cos(rad_y), -np.sin(rad_y), 0], [np.sin(rad_y), np.cos(rad_y), 0], [0, 0, 1]])
        rmat_p = np.array([[np.cos(rad_p), 0, np.sin(rad_p)], [0, 1, 0], [-np.sin(rad_p), 0, np.cos(rad_p)]])
        rmat_r = np.array([[1, 0, 0], [0, np.cos(rad_r), -np.sin(rad_r)], [0, np.sin(rad_r), np.cos(rad_r)]])
        rmat = rmat_y @ rmat_p @ rmat_r
        
        points = self.points_3d.copy()
        projected = points @ rmat.T
        pts_2d_dest = (projected[:, :2] * 1.8 + np.array([w//2, h//2])).astype(np.float32)
        
        output = np.zeros((h, w, 3), dtype=np.uint8)
        for tri_idx in self.triangles:
            t_src = [self.base_lms[i] for i in tri_idx]
            t_dst = [pts_2d_dest[i] for i in tri_idx]
            self.warp_triangle(self.texture_atlas, output, t_src, t_dst)
        return output

# UI Setup remains the same
def on_change(x): pass
engine = UnifiedFaceEngine("shape_predictor_68_face_landmarks.dat")
cap = cv2.VideoCapture("face_video.mp4")
cv2.namedWindow("Innovator Dashboard")
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

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue
    
    engine.depth_mult = cv2.getTrackbarPos("3D Depth", "Innovator Dashboard") / 100.0
    if cv2.getTrackbarPos("Reset", "Innovator Dashboard") == 1:
        engine.yaw, engine.pitch, engine.roll = 0, 0, 0
        cv2.setTrackbarPos("Reset", "Innovator Dashboard", 0)
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = engine.detector(gray, 0)
    if rects:
        shape = engine.predictor(frame, rects[0])
        lms = np.array([[p.x, p.y] for p in shape.parts()], dtype=np.float32)
        
        pose = engine.estimate_head_pose(lms)
        if abs(pose[0] - engine.yaw) > 5 or abs(pose[1] - engine.pitch) > 5:
            engine.update_model(frame, lms, pose)
            engine.yaw, engine.pitch, engine.roll = pose
    
    head_render = engine.render(frame.shape[1], frame.shape[0])
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s') or frame_count % 100 == 0:
        if not os.path.exists("3D"): os.makedirs("3D")
        np.save("3D/points.npy", engine.points_3d)
        np.save("3D/base_lms.npy", engine.base_lms)
        cv2.imwrite("3D/texture.png", engine.texture_atlas)
        np.save("3D/uv_map.npy", engine.uv_map)
        print("Model Saved.")
    
    cv2.imshow("Innovator Dashboard", np.hstack((frame, head_render)))
    if key == ord('q'): break
    frame_count += 1

cap.release()
cv2.destroyAllWindows()