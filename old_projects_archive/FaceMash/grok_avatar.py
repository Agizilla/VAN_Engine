import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
import json
import base64
import os

class AvatarBuilder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("3D Avatar Builder")
        
        # Basic female head and torso mesh
        self.vertices = self.create_basic_mesh()
        self.triangles = self.create_triangles()
        self.uv_map = self.create_uv_map()  # Proper UV
        self.texture = np.ones((1024, 1024, 3), dtype=np.uint8) * 255  # Larger white texture
        
        # Buttons
        tk.Button(self.root, text="Add Face Image", command=self.add_face_image).pack()
        tk.Button(self.root, text="Add Video", command=self.add_video).pack()
        tk.Button(self.root, text="Save", command=self.save_model).pack()
        tk.Button(self.root, text="Load", command=self.load_model).pack()
        
        self.canvas = tk.Canvas(self.root, width=400, height=400)
        self.canvas.pack()
        
        self.yaw, self.pitch = 0.0, 0.0
        self.is_dragging = False
        self.last_mouse = (0, 0)
        
        # Mouse bindings
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        self.render()
        
        self.root.mainloop()
    
    def create_basic_mesh(self):
        # Vertices (x, y, z)
        # Head: 0 nose, 1 right cheek, 2 left cheek, 3 top head
        # Torso: 4 neck, 5 right shoulder, 6 left shoulder
        head = np.array([[0, 0, 0], [50, 50, -20], [-50, 50, -20], [0, 100, 0]])
        torso = np.array([[0, -100, 0], [100, -200, 0], [-100, -200, 0]])
        return np.vstack((head, torso)).astype(np.float32)
    
    def create_triangles(self):
        return np.array([[0,1,2], [0,2,3], [0,3,4], [4,5,6], [0,4,5], [0,4,6]])
    
    def create_uv_map(self):
        # Proper UV for vertices (0-1 range, mapping to texture)
        # Assume front unwrap: head in center (0.4-0.6 x/y), torso below
        return np.array([
            [0.5, 0.5],   # 0 nose
            [0.6, 0.6],   # 1 right cheek
            [0.4, 0.6],   # 2 left cheek
            [0.5, 0.7],   # 3 top head
            [0.5, 0.4],   # 4 neck
            [0.7, 0.3],   # 5 right shoulder
            [0.3, 0.3]    # 6 left shoulder
        ], dtype=np.float32)
    
    def on_mouse_down(self, event):
        self.is_dragging = True
        self.last_mouse = (event.x, event.y)
    
    def on_mouse_drag(self, event):
        if self.is_dragging:
            dx = event.x - self.last_mouse[0]
            dy = event.y - self.last_mouse[1]
            self.yaw += dx * 0.5
            self.pitch += dy * 0.5
            self.last_mouse = (event.x, event.y)
            self.render()
    
    def on_mouse_up(self, event):
        self.is_dragging = False
    
    def add_face_image(self):
        path = filedialog.askopenfilename()
        if path:
            img = cv2.imread(path)
            fixed_size = 512
            img = cv2.resize(img, (fixed_size, fixed_size))
            start = (1024 - fixed_size) // 2
            self.texture[start:start+fixed_size, start:start+fixed_size] = img
            self.render()
    
    def add_video(self):
        path = filedialog.askopenfilename()
        if path:
            cap = cv2.VideoCapture(path)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            prev_size = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    face_img = frame[y:y+h, x:x+w]
                    if w * h > prev_size:
                        fixed_size = 512
                        face_img = cv2.resize(face_img, (fixed_size, fixed_size))
                        start = (1024 - fixed_size) // 2
                        self.texture[start:start+fixed_size, start:start+fixed_size] = face_img
                        prev_size = w * h
                self.render()
                cv2.waitKey(30)
            cap.release()
    
    def warp_triangle(self, src, dst, tri_src_uv, tri_dst_2d, normal):
        tex_coords = (tri_src_uv * np.array([src.shape[1] - 1, src.shape[0] - 1])).astype(np.float32)
        r1 = cv2.boundingRect(tex_coords)
        r2 = cv2.boundingRect(tri_dst_2d)
        if r1[2] <= 0 or r1[3] <= 0 or r2[2] <= 0 or r2[3] <= 0:
            return  # Skip degenerate triangles
        
        # Clip r2 to dst bounds
        r2_x = max(0, r2[0])
        r2_y = max(0, r2[1])
        r2_w = min(dst.shape[1] - r2_x, r2[2])
        r2_h = min(dst.shape[0] - r2_y, r2[3])
        if r2_w <= 0 or r2_h <= 0:
            return
        
        t1_rect = tex_coords - np.array([r1[0], r1[1]])
        t2_rect = tri_dst_2d - np.array([r2[0], r2[1]])
        mask = np.zeros((r2_h, r2_w, 3), dtype=np.float32)
        cv2.fillConvexPoly(mask, np.int32(t2_rect - np.array([r2_x - r2[0], r2_y - r2[1]])), (1.0, 1.0, 1.0))
        src_rect = src[r1[1]:r1[1]+r1[3], r1[0]:r1[0]+r1[2]]
        warp_mat = cv2.getAffineTransform(np.float32(t1_rect), np.float32(t2_rect))
        dst_rect = cv2.warpAffine(src_rect, warp_mat, (r2_w, r2_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        
        # Apply lighting
        light_dir = np.array([0, 0, -1])  # From front
        intensity = max(0.2, np.dot(normal, light_dir))
        dst_rect = (dst_rect.astype(np.float32) * intensity).astype(np.uint8)
        
        slice_dst = dst[r2_y:r2_y+r2_h, r2_x:r2_x+r2_w]
        temp = slice_dst.astype(np.float32) * (1 - mask) + dst_rect.astype(np.float32) * mask
        dst[r2_y:r2_y+r2_h, r2_x:r2_x+r2_w] = np.clip(temp, 0, 255).astype(np.uint8)
    
    def render(self):
        h, w = 400, 400
        img = np.zeros((h, w, 3), np.uint8)
        
        # Rotation matrix
        rad_y = np.deg2rad(self.yaw)
        rad_p = np.deg2rad(self.pitch)
        rmat_y = np.array([[np.cos(rad_y), -np.sin(rad_y), 0], [np.sin(rad_y), np.cos(rad_y), 0], [0, 0, 1]])
        rmat_p = np.array([[np.cos(rad_p), 0, np.sin(rad_p)], [0, 1, 0], [-np.sin(rad_p), 0, np.cos(rad_p)]])
        rmat = rmat_y @ rmat_p
        
        projected = (self.vertices @ rmat.T)[:, :2]
        scale = 1.5
        projected = (projected * scale + np.array([w//2, h//2])).astype(np.float32)
        
        for tri in self.triangles:
            tri_verts = self.vertices[tri]
            edge1 = tri_verts[1] - tri_verts[0]
            edge2 = tri_verts[2] - tri_verts[0]
            normal = np.cross(edge1, edge2)
            normal /= np.linalg.norm(normal) if np.linalg.norm(normal) != 0 else 1
            tri_dst_2d = projected[tri]
            tri_src_uv = self.uv_map[tri]
            self.warp_triangle(self.texture, img, tri_src_uv, tri_dst_2d, normal)
        
        _, encoded = cv2.imencode('.png', img)
        self.photo = tk.PhotoImage(data=encoded.tobytes())
        self.canvas.create_image(200, 200, image=self.photo)
    
    def save_model(self):
        data = {
            'vertices': self.vertices.tolist(),
            'triangles': self.triangles.tolist(),
            'uv_map': self.uv_map.tolist(),
            'texture': base64.b64encode(cv2.imencode('.png', self.texture)[1]).decode('utf-8')
        }
        with open('model.json', 'w') as f:
            json.dump(data, f)
    
    def load_model(self):
        if os.path.exists('model.json'):
            with open('model.json', 'r') as f:
                data = json.load(f)
            self.vertices = np.array(data['vertices'])
            self.triangles = np.array(data['triangles'])
            self.uv_map = np.array(data['uv_map'])
            texture_bytes = base64.b64decode(data['texture'])
            self.texture = cv2.imdecode(np.frombuffer(texture_bytes, np.uint8), cv2.IMREAD_COLOR)
            self.render()

if __name__ == "__main__":
    AvatarBuilder()