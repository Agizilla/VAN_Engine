"""
3D Face Avatar Generator
Creates a 3D face model from photos/video with texture mapping and face tracking
"""

import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import pygame
from pygame.locals import *
import math
import mediapipe as mp
import os

class FaceAvatar3D:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 3D model data
        self.vertices = []
        self.texture_coords = []
        self.faces_indices = []
        self.texture_id = None
        self.texture_image = None
        
        # Face grid for texture atlas
        self.face_crops = []  # Store 200x200 face crops
        self.face_qualities = []  # Quality scores for each crop
        self.grid_size = 10  # 10x10 grid = 100 faces max
        self.crop_size = 200
        
        # Camera/view controls
        self.rotation_x = 0
        self.rotation_y = 0
        self.zoom = -5.0
        self.mouse_down = False
        self.last_mouse_pos = (0, 0)
        
        # Video processing
        self.video_cap = None
        self.video_playing = False
        self.video_thread = None
        
    def calculate_face_quality(self, face_img):
        """Calculate quality score based on sharpness and brightness"""
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        # Laplacian variance for sharpness
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Brightness
        brightness = np.mean(gray)
        # Combined score
        quality = laplacian_var * 0.7 + brightness * 0.3
        return quality
    
    def extract_face_from_image(self, image):
        """Extract face region and landmarks from image"""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        
        if not results.multi_face_landmarks:
            return None, None
        
        landmarks = results.multi_face_landmarks[0]
        h, w = image.shape[:2]
        
        # Get face bounding box
        x_coords = [lm.x * w for lm in landmarks.landmark]
        y_coords = [lm.y * h for lm in landmarks.landmark]
        
        x_min, x_max = int(min(x_coords)), int(max(x_coords))
        y_min, y_max = int(min(y_coords)), int(max(y_coords))
        
        # Add padding
        padding = 30
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = min(w, x_max + padding)
        y_max = min(h, y_max + padding)
        
        face_crop = image[y_min:y_max, x_min:x_max]
        
        # Resize to 200x200
        if face_crop.size > 0:
            face_crop = cv2.resize(face_crop, (self.crop_size, self.crop_size))
            return face_crop, landmarks
        
        return None, None
    
    def add_face_to_grid(self, face_crop):
        """Add face crop to grid, replacing lower quality ones if needed"""
        quality = self.calculate_face_quality(face_crop)
        
        if len(self.face_crops) < self.grid_size * self.grid_size:
            self.face_crops.append(face_crop)
            self.face_qualities.append(quality)
        else:
            # Replace lowest quality face if this one is better
            min_idx = np.argmin(self.face_qualities)
            if quality > self.face_qualities[min_idx]:
                self.face_crops[min_idx] = face_crop
                self.face_qualities[min_idx] = quality
    
    def create_face_grid_image(self):
        """Create master grid image from all face crops"""
        grid_width = self.grid_size * self.crop_size
        grid_height = self.grid_size * self.crop_size
        grid_image = np.ones((grid_height, grid_width, 3), dtype=np.uint8) * 255
        
        for idx, face_crop in enumerate(self.face_crops):
            row = idx // self.grid_size
            col = idx % self.grid_size
            y_start = row * self.crop_size
            x_start = col * self.crop_size
            grid_image[y_start:y_start+self.crop_size, 
                      x_start:x_start+self.crop_size] = face_crop
        
        return grid_image
    
    def create_3d_mesh_from_landmarks(self, landmarks, image_width, image_height):
        """Create 3D mesh from MediaPipe face landmarks"""
        self.vertices = []
        self.texture_coords = []
        
        # Extract 3D coordinates (MediaPipe provides z-coordinate)
        for lm in landmarks.landmark:
            # Normalize coordinates to [-1, 1] range
            x = (lm.x - 0.5) * 2
            y = (0.5 - lm.y) * 2  # Flip Y
            z = lm.z * 2
            self.vertices.append([x, y, z])
            
            # Texture coordinates
            self.texture_coords.append([lm.x, lm.y])
        
        # Create face indices using MediaPipe's tesselation
        self.faces_indices = mp.solutions.face_mesh.FACEMESH_TESSELATION
    
    def load_initial_image(self):
        """Load initial frontal face image"""
        filepath = filedialog.askopenfilename(
            title="Select Face Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if not filepath:
            return
        
        image = cv2.imread(filepath)
        if image is None:
            messagebox.showerror("Error", "Could not load image")
            return
        
        face_crop, landmarks = self.extract_face_from_image(image)
        
        if face_crop is None:
            messagebox.showerror("Error", "No face detected in image")
            return
        
        # Add to grid
        self.add_face_to_grid(face_crop)
        
        # Create 3D mesh
        h, w = image.shape[:2]
        self.create_3d_mesh_from_landmarks(landmarks, w, h)
        
        # Create texture from grid
        self.update_texture()
        
        messagebox.showinfo("Success", "Face model created successfully!")
    
    def load_video(self):
        """Load and process video to enhance model"""
        filepath = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
        )
        
        if not filepath:
            return
        
        self.video_cap = cv2.VideoCapture(filepath)
        if not self.video_cap.isOpened():
            messagebox.showerror("Error", "Could not open video")
            return
        
        self.video_playing = True
        self.video_thread = threading.Thread(target=self.process_video)
        self.video_thread.start()
    
    def process_video(self):
        """Process video frames to extract faces"""
        frame_count = 0
        processed_count = 0
        
        while self.video_playing and self.video_cap.isOpened():
            ret, frame = self.video_cap.read()
            if not ret:
                break
            
            frame_count += 1
            # Process every 10th frame to speed up
            if frame_count % 10 != 0:
                continue
            
            face_crop, landmarks = self.extract_face_from_image(frame)
            
            if face_crop is not None:
                self.add_face_to_grid(face_crop)
                processed_count += 1
                
                # Update texture periodically
                if processed_count % 5 == 0:
                    self.update_texture()
        
        self.video_cap.release()
        self.video_playing = False
        self.update_texture()
        messagebox.showinfo("Complete", f"Processed {processed_count} faces from video")
    
    def update_texture(self):
        """Update OpenGL texture from face grid"""
        if len(self.face_crops) == 0:
            return
        
        grid_image = self.create_face_grid_image()
        self.texture_image = cv2.cvtColor(grid_image, cv2.COLOR_BGR2RGB)
        
        # Update OpenGL texture
        if self.texture_id is not None:
            glDeleteTextures([self.texture_id])
        
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 
                     self.texture_image.shape[1], 
                     self.texture_image.shape[0], 
                     0, GL_RGB, GL_UNSIGNED_BYTE, self.texture_image)
    
    def save_model(self):
        """Save model and face grid to master.bmp"""
        if len(self.face_crops) == 0:
            messagebox.showwarning("Warning", "No face data to save")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".bmp",
            initialfile="master.bmp",
            filetypes=[("Bitmap files", "*.bmp")]
        )
        
        if not filepath:
            return
        
        # Save face grid
        grid_image = self.create_face_grid_image()
        cv2.imwrite(filepath, grid_image)
        
        # Save metadata (vertices, texture coords, faces)
        metadata_path = filepath.replace('.bmp', '_metadata.npz')
        np.savez(metadata_path,
                 vertices=np.array(self.vertices),
                 texture_coords=np.array(self.texture_coords),
                 faces_indices=np.array(list(self.faces_indices)),
                 face_qualities=np.array(self.face_qualities))
        
        messagebox.showinfo("Success", f"Model saved to {filepath}")
    
    def load_model(self):
        """Load model from master.bmp"""
        filepath = filedialog.askopenfilename(
            title="Select master.bmp",
            filetypes=[("Bitmap files", "*.bmp")]
        )
        
        if not filepath:
            return
        
        # Load face grid
        grid_image = cv2.imread(filepath)
        if grid_image is None:
            messagebox.showerror("Error", "Could not load image")
            return
        
        # Extract individual face crops from grid
        self.face_crops = []
        self.face_qualities = []
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                y_start = row * self.crop_size
                x_start = col * self.crop_size
                face_crop = grid_image[y_start:y_start+self.crop_size,
                                      x_start:x_start+self.crop_size]
                
                # Check if it's not just white
                if np.mean(face_crop) < 250:
                    self.face_crops.append(face_crop)
                    quality = self.calculate_face_quality(face_crop)
                    self.face_qualities.append(quality)
        
        # Load metadata
        metadata_path = filepath.replace('.bmp', '_metadata.npz')
        if os.path.exists(metadata_path):
            data = np.load(metadata_path, allow_pickle=True)
            self.vertices = data['vertices'].tolist()
            self.texture_coords = data['texture_coords'].tolist()
            self.faces_indices = [tuple(face) for face in data['faces_indices']]
            if 'face_qualities' in data:
                self.face_qualities = data['face_qualities'].tolist()
        
        self.update_texture()
        messagebox.showinfo("Success", "Model loaded successfully!")
    
    def render_3d_model(self):
        """Render the 3D face model"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Apply camera transformations
        glTranslatef(0, 0, self.zoom)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        
        if len(self.vertices) == 0:
            pygame.display.flip()
            return
        
        # Enable texturing
        if self.texture_id is not None:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
        
        # Render mesh
        glBegin(GL_TRIANGLES)
        for face in self.faces_indices:
            for vertex_idx in face:
                if vertex_idx < len(self.vertices):
                    if vertex_idx < len(self.texture_coords):
                        glTexCoord2fv(self.texture_coords[vertex_idx])
                    glVertex3fv(self.vertices[vertex_idx])
        glEnd()
        
        glDisable(GL_TEXTURE_2D)
        pygame.display.flip()
    
    def handle_mouse(self, event):
        """Handle mouse events for rotation and zoom"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.mouse_down = True
                self.last_mouse_pos = pygame.mouse.get_pos()
            elif event.button == 4:  # Mouse wheel up
                self.zoom += 0.3
            elif event.button == 5:  # Mouse wheel down
                self.zoom -= 0.3
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.mouse_down = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.mouse_down:
                current_pos = pygame.mouse.get_pos()
                dx = current_pos[0] - self.last_mouse_pos[0]
                dy = current_pos[1] - self.last_mouse_pos[1]
                self.rotation_y += dx * 0.5
                self.rotation_x += dy * 0.5
                self.last_mouse_pos = current_pos
    
    def run_viewer(self):
        """Run the 3D viewer window"""
        pygame.init()
        display = (800, 600)
        pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Face Avatar Viewer")
        
        # OpenGL setup
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_mouse(event)
            
            self.render_3d_model()
            clock.tick(60)
        
        pygame.quit()


class FaceAvatarGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("3D Face Avatar Generator")
        self.root.geometry("400x300")
        
        self.avatar = FaceAvatar3D()
        
        # Create UI
        self.create_widgets()
    
    def create_widgets(self):
        """Create GUI buttons"""
        title_label = tk.Label(self.root, text="3D Face Avatar Generator",
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Button 1: Load Initial Image
        btn_load_image = tk.Button(self.root, text="1. Load Initial Image",
                                   command=self.load_image,
                                   width=30, height=2, bg="#4CAF50", fg="white")
        btn_load_image.pack(pady=10)
        
        # Button 2: Load Video
        btn_load_video = tk.Button(self.root, text="2. Load Video",
                                   command=self.load_video,
                                   width=30, height=2, bg="#2196F3", fg="white")
        btn_load_video.pack(pady=10)
        
        # Button 3: Load Model
        btn_load_model = tk.Button(self.root, text="3. Load Model",
                                   command=self.load_model,
                                   width=30, height=2, bg="#FF9800", fg="white")
        btn_load_model.pack(pady=10)
        
        # Button 4: Save Model
        btn_save_model = tk.Button(self.root, text="4. Save Model",
                                   command=self.save_model,
                                   width=30, height=2, bg="#f44336", fg="white")
        btn_save_model.pack(pady=10)
        
        # View 3D Model button
        btn_view_3d = tk.Button(self.root, text="View 3D Model",
                               command=self.view_3d,
                               width=30, height=2, bg="#9C27B0", fg="white")
        btn_view_3d.pack(pady=10)
    
    def load_image(self):
        self.avatar.load_initial_image()
    
    def load_video(self):
        self.avatar.load_video()
    
    def load_model(self):
        self.avatar.load_model()
    
    def save_model(self):
        self.avatar.save_model()
    
    def view_3d(self):
        if len(self.avatar.vertices) == 0:
            messagebox.showwarning("Warning", "No 3D model loaded. Load an image first.")
            return
        
        # Run viewer in separate thread
        viewer_thread = threading.Thread(target=self.avatar.run_viewer)
        viewer_thread.daemon = True
        viewer_thread.start()
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = FaceAvatarGUI()
    app.run()
