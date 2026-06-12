import cv2
import dlib
import numpy as np
import os
import json
import tkinter as tk
from tkinter import filedialog

class UltimateFaceEngine:
    def __init__(self, predictor_path):
        if not os.path.exists(predictor_path):
            print(f"Error: {predictor_path} not found.")
            exit()
            
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        
        # UI & Transform State
        self.yaw, self.pitch = 0.0, 0.0
        self.zoom = 1.6
        self.is_dragging = False
        self.show_wireframe = False
        self.last_mouse = (0, 0)
        
        # Manual Selection Logic
        self.roi_start = None
        self.roi_end = None
        self.selecting = False
        
        # Persistent Data
        self.vertices = np.zeros((77, 3), dtype=np.float32)
        self.triangles = self._build_pro_mesh()
        self.texture_atlas = None
        self.base_lms = None
        self.learning_count = 0 
        self.master_brightness = None
        
        self.load_session()

    def _build_pro_mesh(self):
        face = [(0,1,36), (1,2,41), (15,14,46), (16,15,45), (30,31,48), (30,35,54),
                (36,37,41), (37,38,40), (42,43,47), (44,45,46), (48,49,60), (54,55,64),
                (17,18,36), (25,26,45), (8,7,58), (8,9,57), (27,28,30), (27,29,30)]
        torso = [(0,68,71), (16,69,71), (8,70,71), (68,72,70), (69,73,70), (71,70,8)]
        return face + torso

    def _normalize_lighting(self, img):
        if img is None or img.size == 0: return img
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        v = hsv[:, :, 2].astype(np.float32)
        avg = np.mean(v)
        if self.master_brightness is None:
            self.master_brightness = avg
            return img
        v = np.clip(v * (self.master_brightness / (avg + 1e-6)), 0, 255).astype(np.uint8)
        hsv[:, :, 2] = v
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def _update_geometry(self, lms):
        center = np.mean(lms, axis=0)
        nose_tip = lms[30]
        self.learning_count += 1
        alpha = 1.0 / (self.learning_count + 1)

        for i in range(68):
            z = -np.linalg.norm(lms[i] - nose_tip) * 0.82
            new_v = np.array([lms[i][0] - center[0], lms[i][1] - center[1], z])
            if self.learning_count == 1:
                self.vertices[i] = new_v
            else:
                self.vertices[i] = (1 - alpha) * self.vertices[i] + alpha * new_v

        w_f = np.linalg.norm(lms[0] - lms[16])
        c = self.vertices[8] 
        self.vertices[68:74] = [
            [c[0]-w_f*2, c[1]+w_f*1.2, -w_f], [c[0]+w_f*2, c[1]+w_f*1.2, -w_f],
            [0, c[1]+w_f*2.8, -w_f*0.2], [0, c[1]+w_f*1.1, -w_f*0.1],
            [c[0]-w_f*1.5, c[1]+w_f*2.2, -w_f*0.8], [c[0]+w_f*1.5, c[1]+w_f*2.2, -w_f*0.8]
        ]

    def upload_base_face(self):
        root = tk.Tk(); root.withdraw()
        path = filedialog.askopenfilename(title="Select Base Face Image", 
                                          filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if path:
            img = cv2.imread(path)
            if img is not None:
                h, w = img.shape[:2]
                print(f"Establishing Identity: {w}x{h}")
                # Reset for new identity if needed
                self.texture_atlas = None 
                self.master_brightness = None
                self._apply_crop_to_mesh(img, (0, 0, w, h))

    def _apply_crop_to_mesh(self, frame, rect):
        x, y, w, h = rect
        crop = frame[y:y+h, x:x+w]
        if crop.size == 0: return

        # Identity Detection
        normalized_crop = self._normalize_lighting(crop)
        rects = self.detector(cv2.cvtColor(normalized_crop, cv2.COLOR_BGR2GRAY), 0)
        if not rects:
            print("Detection failed.")
            return

        shape = self.predictor(normalized_crop, rects[0])
        lms = np.array([[p.x + x, p.y + y] for p in shape.parts()], dtype=np.float32)
        
        # Symmetry
        nx = lms[30][0]
        for i in range(17): lms[16-i][0] = nx + (nx - lms[i][0])

        normalized_frame = self._normalize_lighting(frame)

        # FIX: Ensure Blending Dimensions Match
        if self.texture_atlas is not None:
            target_h, target_w = self.texture_atlas['img_norm'].shape[:2]
            if normalized_frame.shape[0] != target_h or normalized_frame.shape[1] != target_w:
                # Calculate scale and rescale landmarks accordingly
                scale_x = target_w / normalized_frame.shape[1]
                scale_y = target_h / normalized_frame.shape[0]
                normalized_frame = cv2.resize(normalized_frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
                lms[:, 0] *= scale_x
                lms[:, 1] *= scale_y
            
            blended = cv2.addWeighted(self.texture_atlas['img_norm'], 0.85, normalized_frame, 0.15, 0)
        else:
            blended = normalized_frame

        self.texture_atlas = {'img_norm': blended}
        self.base_lms = lms
        self._update_geometry(lms)

    def render(self, w, h):
        canvas = np.zeros((h, w, 3), dtype=np.uint8)
        sy, cy = np.sin(self.yaw), np.cos(self.yaw)
        sp, cp = np.sin(self.pitch), np.cos(self.pitch)
        rmat = np.array([[cy, 0, sy], [sy*sp, cp, -cy*sp], [-sy*cp, sp, cy*cp]], dtype=np.float32)
        
        proj = (self.vertices @ rmat.T)
        pts_2d = (proj[:, :2] * self.zoom + [w//2, h//2]).astype(np.int32)

        for tri in self.triangles:
            try:
                t_idx = list(tri)
                if not self.show_wireframe and self.texture_atlas is not None and all(i < 68 for i in t_idx):
                    self._warp_triangle(self.texture_atlas['img_norm'], canvas, self.base_lms[t_idx], pts_2d[t_idx].astype(np.float32))
                elif self.show_wireframe or self.texture_atlas is None:
                    cv2.polylines(canvas, [pts_2d[t_idx]], True, (0, 255, 150), 1, cv2.LINE_AA)
            except: continue
        return canvas

    def _warp_triangle(self, src, dst, t_src, t_dst):
        r1, r2 = cv2.boundingRect(t_src), cv2.boundingRect(t_dst)
        # Boundary safety
        if r1[0] < 0 or r1[1] < 0 or r1[0]+r1[2] > src.shape[1] or r1[1]+r1[3] > src.shape[0]: return
        
        s_rect = src[r1[1]:r1[1]+r1[3], r1[0]:r1[0]+r1[2]]
        t1 = [(p[0]-r1[0], p[1]-r1[1]) for p in t_src]
        t2 = [(p[0]-r2[0], p[1]-r2[1]) for p in t_dst]
        
        M = cv2.getAffineTransform(np.float32(t1), np.float32(t2))
        patch = cv2.warpAffine(s_rect, M, (r2[2], r2[3]), None, cv2.INTER_LINEAR, cv2.BORDER_REFLECT_101)
        
        mask = np.zeros((r2[3], r2[2], 3), dtype=np.float32)
        cv2.fillConvexPoly(mask, np.int32(t2), (1, 1, 1), cv2.LINE_AA)
        
        y_end, x_end = r2[1]+r2[3], r2[0]+r2[2]
        if y_end <= dst.shape[0] and x_end <= dst.shape[1]:
            roi = dst[r2[1]:y_end, r2[0]:x_end]
            dst[r2[1]:y_end, r2[0]:x_end] = (roi*(1-mask) + patch*mask).astype(np.uint8)

    def save_session(self):
        if not os.path.exists("3D"): os.makedirs("3D")
        data = {"v": self.vertices.tolist(), "t": self.triangles, "l": self.base_lms.tolist() if self.base_lms is not None else [], "c": self.learning_count, "b": float(self.master_brightness) if self.master_brightness else None}
        with open("3D/pro_model.json", "w") as f: json.dump(data, f)
        if self.texture_atlas: cv2.imwrite("3D/pro_texture.png", self.texture_atlas['img_norm'])

    def load_session(self):
        if os.path.exists("3D/pro_model.json"):
            try:
                with open("3D/pro_model.json", "r") as f:
                    d = json.load(f)
                    self.vertices, self.triangles, self.learning_count = np.array(d["v"], dtype=np.float32), d["t"], d.get("c", 0)
                    self.master_brightness = d.get("b", None)
                    if os.path.exists("3D/pro_texture.png"):
                        self.texture_atlas = {'img_norm': cv2.imread("3D/pro_texture.png")}
                        self.base_lms = np.array(d["l"], dtype=np.float32)
            except: print("Error loading session. Starting fresh.")

# --- UI Loop remains the same ---
engine = UltimateFaceEngine("shape_predictor_68_face_landmarks.dat")
cv2.namedWindow("3D Innovator Studio")
cv2.setMouseCallback("3D Innovator Studio", on_mouse, "studio")

while True:
    view = engine.render(1200, 900)
    # HUD Rendering...
    status = [f"ENGINE: {'ACTIVE' if engine.texture_atlas else 'IDLE'}", 
              f"FIDELITY: {engine.learning_count}", "---", "[F] BASE FACE", "[V] VIDEO SAMPLE", "[S] SAVE", "[Q] EXIT"]
    for i, t in enumerate(status):
        cv2.putText(view, t, (20, 35 + i*28), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 150), 1, cv2.LINE_AA)
    
    cv2.imshow("3D Innovator Studio", view)
    k = cv2.waitKey(1) & 0xFF
    if k == ord('f'): engine.upload_base_face()
    elif k == ord('v'):
        root = tk.Tk(); root.withdraw()
        path = filedialog.askopenfilename()
        if path:
            cap = cv2.VideoCapture(path)
            cv2.namedWindow("Video Sampler")
            cv2.setMouseCallback("Video Sampler", on_mouse, "video")
            paused = False
            while cap.read()[0]:
                cap.set(cv2.CAP_PROP_POS_FRAMES, cap.get(cv2.CAP_PROP_POS_FRAMES)-1)
                ret, frame = cap.read()
                disp = frame.copy()
                if engine.roi_start and engine.roi_end:
                    cv2.rectangle(disp, engine.roi_start, engine.roi_end, (0, 255, 150), 2)
                cv2.imshow("Video Sampler", disp)
                vk = cv2.waitKey(30) & 0xFF
                if vk == ord(' '): paused = not paused
                if vk == 13: # Enter
                    if engine.roi_start and engine.roi_end:
                        x1, y1, x2, y2 = engine.roi_start[0], engine.roi_start[1], engine.roi_end[0], engine.roi_end[1]
                        engine._apply_crop_to_mesh(frame, (min(x1,x2), min(y1,y2), abs(x2-x1), abs(y2-y1)))
                if vk == ord('c'): break
                if not paused: continue
            cap.release(); cv2.destroyWindow("Video Sampler")
    elif k == ord('w'): engine.show_wireframe = not engine.show_wireframe
    elif k == ord('s'): engine.save_session()
    elif k == ord('q'): break