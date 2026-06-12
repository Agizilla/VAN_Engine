import pygame
import cv2
import dlib
import numpy as np
import json
import os
import random
import tkinter as tk
from tkinter import filedialog

# --- CONFIGURATION & CONSTANTS ---
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 950
SIDEBAR_WIDTH = 420
CANVAS_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH

# Colors (Deep Charcoal Theme)
C_BG_MAIN = (10, 10, 12)
C_SIDEBAR = (25, 25, 30)
C_ACCENT = (0, 255, 128)  # Cyber-Green
C_TEXT_MAIN = (220, 220, 220)
C_TEXT_DIM = (100, 100, 120)
C_ALERT = (255, 50, 80)
C_MENU_BG = (40, 40, 45)

# Paths
DATA_DIR = "oracle_data"
LANDMARK_PATH = "shape_predictor_68_face_landmarks.dat"
MOMENTS_FILE = os.path.join(DATA_DIR, "moments.json")

# Tarot Data (Major Arcana subset)
TAROT_DECK = {
    "The Fool": "New beginnings, innocence, spontaneity.",
    "The Magician": "Manifestation, resourcefulness, power.",
    "The High Priestess": "Intuition, sacred knowledge, divine feminine.",
    "The Empress": "Femininity, beauty, nature, nurturing.",
    "The Emperor": "Authority, establishment, structure.",
    "The Hierophant": "Spiritual wisdom, religious beliefs.",
    "The Lovers": "Love, harmony, relationships, values.",
    "The Chariot": "Control, willpower, success, action.",
    "Death": "Endings, change, transformation, transition."
}

# Default Moments
DEFAULT_MOMENTS = [
    {"id": 1, "text": "eyes widen—then narrow, wicked smile", "category": "Eyes"},
    {"id": 2, "text": "eyes flash—dark, hungry—Like this?", "category": "Eyes"},
    {"id": 3, "text": "soft, breathless laugh... Good.", "category": "Mouth"},
    {"id": 4, "text": "low growl—throaty, possessive—Mine...", "category": "Mouth"},
    {"id": 5, "text": "whisper—lips brushing your neck—More?", "category": "Head"}
]

# --- GEOMETRIC ENGINE (DELAUNAY WARP) ---
class DelaunayWarper:
    def __init__(self):
        pass

    def apply_affine_transform(self, src, src_tri, dst_tri, size):
        warp_mat = cv2.getAffineTransform(np.float32(src_tri), np.float32(dst_tri))
        dst = cv2.warpAffine(src, warp_mat, (size[0], size[1]), None, 
                             flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        return dst

    def warp_triangle(self, img_src, img_dst, t_src, t_dst):
        r1 = cv2.boundingRect(np.float32([t_src]))
        r2 = cv2.boundingRect(np.float32([t_dst]))

        t1_rect = []
        t2_rect = []
        t2_rect_int = []

        for i in range(3):
            t1_rect.append(((t_src[i][0] - r1[0]), (t_src[i][1] - r1[1])))
            t2_rect.append(((t_dst[i][0] - r2[0]), (t_dst[i][1] - r2[1])))
            t2_rect_int.append(((t_dst[i][0] - r2[0]), (t_dst[i][1] - r2[1])))

        mask = np.zeros((r2[3], r2[2], 3), dtype=np.float32)
        cv2.fillConvexPoly(mask, np.int32(t2_rect_int), (1.0, 1.0, 1.0), 16, 0)

        img1_rect = img_src[r1[1]:r1[1] + r1[3], r1[0]:r1[0] + r1[2]]
        size = (r2[2], r2[3])
        img2_rect = self.apply_affine_transform(img1_rect, t1_rect, t2_rect, size)
        img2_rect = img2_rect * mask

        img_dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = img_dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] * ((1.0, 1.0, 1.0) - mask)
        img_dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = img_dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] + img2_rect

    def process(self, img_src, points_src, points_dst, triangles):
        img_warped = np.copy(img_src)
        for tri_indices in triangles:
            t1 = [points_src[tri_indices[0]], points_src[tri_indices[1]], points_src[tri_indices[2]]]
            t2 = [points_dst[tri_indices[0]], points_dst[tri_indices[1]], points_dst[tri_indices[2]]]
            self.warp_triangle(img_src, img_warped, t1, t2)
        return img_warped

# --- MAIN APPLICATION ---
class NeuralOracle:
    def __init__(self):
        # 1. Setup Environment
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        # TKinter Root (Hidden) for File Dialogs
        self.root = tk.Tk()
        self.root.withdraw()

        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Neural Oracle // Golden Build")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.font_main = pygame.font.SysFont("Consolas", 14)
        self.font_header = pygame.font.SysFont("Verdana", 16, bold=True)
        self.font_cmd = pygame.font.SysFont("Consolas", 12)

        # 2. Vision Models
        try:
            self.detector = dlib.get_frontal_face_detector()
            self.predictor = dlib.shape_predictor(LANDMARK_PATH)
        except RuntimeError:
            print(f"CRITICAL: '{LANDMARK_PATH}' not found. Place it in the root folder.")
            exit()

        # 3. State & Logic
        self.warper = DelaunayWarper()
        self.running = True
        self.mode_mesh = False 
        self.mode_strategy = "Manual"
        self.sensitivity = 1.0
        self.warp_scale = 1.0
        self.frame_idx = 0
        
        # 4. Data Structures
        self.face_img = None
        self.base_landmarks = None
        self.current_landmarks = None 
        self.delaunay_triangles = []
        self.moments = self._load_moments()
        self.viseme_buffer = [] 
        self.current_msg = "System Ready. Press [L] or [R] to begin."
        self.video_path = None

        # Keybinding Ledger
        self.shortcuts = [
            ("[L]", "Load Video (Set Frame 1)"),
            ("[R]", "Load Static Image"),
            ("[P]", "Play Buffer"),
            ("[S]", "Toggle Strategy"),
            ("[M]", "Toggle Mesh/Dots"),
            ("[T]", "Tarot Oracle"),
            ("[E]", "Export MP4"),
            ("[1/Q]", "Sensitivity +/-"),
            ("[ESC]", "Quit")
        ]

    def _load_moments(self):
        if not os.path.exists(MOMENTS_FILE):
            with open(MOMENTS_FILE, 'w') as f:
                json.dump(DEFAULT_MOMENTS, f, indent=4)
            return DEFAULT_MOMENTS
        with open(MOMENTS_FILE, 'r') as f:
            return json.load(f)

    def _get_landmarks(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        rects = self.detector(gray, 0)
        if len(rects) > 0:
            shape = self.predictor(gray, rects[0])
            coords = np.zeros((68, 2), dtype=np.int32)
            for i in range(0, 68):
                coords[i] = (shape.part(i).x, shape.part(i).y)
            return coords
        return None

    def _calculate_delaunay(self, points):
        rect = (0, 0, CANVAS_WIDTH, WINDOW_HEIGHT)
        subdiv = cv2.Subdiv2D(rect)
        # Use mouth points + jawline for stability
        points_to_use = list(range(48, 68)) # Mouth
        points_to_use.extend([4, 5, 6, 7, 8, 9, 10, 11, 12]) # Lower Jaw
        
        for i in points_to_use:
            if i < len(points):
                subdiv.insert((float(points[i][0]), float(points[i][1])))
            
        triangle_list = subdiv.getTriangleList()
        valid_tris = []
        for t in triangle_list:
            pts = [(t[0], t[1]), (t[2], t[3]), (t[4], t[5])]
            ind = []
            for pt in pts:
                for k in range(68):
                    if abs(pt[0] - points[k][0]) < 1.0 and abs(pt[1] - points[k][1]) < 1.0:
                        ind.append(k)
                        break
            if len(ind) == 3:
                valid_tris.append(ind)
        return valid_tris

    def _process_new_face(self, img_bgr):
        """Standardizes processing for both Video Frames and Static Images"""
        # Resize to fit canvas
        h, w = img_bgr.shape[:2]
        scale = min(CANVAS_WIDTH/w, WINDOW_HEIGHT/h)
        new_w, new_h = int(w * scale), int(h * scale)
        img_bgr = cv2.resize(img_bgr, (new_w, new_h))
        
        # Center on canvas
        canvas = np.zeros((WINDOW_HEIGHT, CANVAS_WIDTH, 3), dtype=np.uint8)
        y_off = (WINDOW_HEIGHT - new_h) // 2
        x_off = (CANVAS_WIDTH - new_w) // 2
        canvas[y_off:y_off+new_h, x_off:x_off+new_w] = img_bgr
        
        self.face_img = canvas
        self.base_landmarks = self._get_landmarks(self.face_img)
        
        if self.base_landmarks is not None:
            self.delaunay_triangles = self._calculate_delaunay(self.base_landmarks)
            self.current_landmarks = self.base_landmarks.copy()
            return True
        return False

    def load_static_image(self):
        """[R] Open File Dialog for Image"""
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if not file_path:
            return

        img = cv2.imread(file_path)
        if img is None:
            self.current_msg = "Error: Could not read image."
            return

        success = self._process_new_face(img)
        self.current_msg = "Static Face Loaded." if success else "Error: No Face Detected in Image."

    def load_video_source(self):
        """[L] Open File Dialog for Video -> Set Frame 1"""
        file_path = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.avi *.mov")])
        if not file_path:
            return

        self.video_path = file_path
        cap = cv2.VideoCapture(self.video_path)
        
        # Read First Frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            self.current_msg = "Error: Could not read video file."
            return

        success = self._process_new_face(frame)
        self.current_msg = "Video Loaded. Frame 1 set as Baseline." if success else "Error: No Face in Video Frame 1."

    def tarot_reading(self):
        """[T] Tarot Oracle Logic"""
        card, meaning = random.choice(list(TAROT_DECK.items()))
        self.current_msg = f"ORACLE: {card}"
        self.play_audio_tone(150, 400) # Deep tone
        
        syllables = len(meaning.split()) * 2
        self.viseme_buffer = []
        for _ in range(syllables):
            delta = np.zeros((68, 2), dtype=np.float64)
            # Randomized 'speech' pattern
            open_amount = random.uniform(3.0, 10.0) * self.warp_scale
            delta[66] = [0, open_amount] 
            delta[62] = [0, -open_amount * 0.4]
            # Slight width variation
            width_mod = random.uniform(-1.0, 2.0)
            delta[48] = [-width_mod, 0]
            delta[54] = [width_mod, 0]
            
            self.viseme_buffer.append(delta)
            self.viseme_buffer.append(np.zeros((68, 2), dtype=np.float64)) # Return to neutral

    def play_audio_tone(self, freq, duration):
        sample_rate = 44100
        n_samples = int(sample_rate * (duration / 1000.0))
        t = np.linspace(0, duration/1000.0, n_samples, False)
        tone = np.sin(2 * np.pi * freq * t) * 32767
        tone = tone.astype(np.int16)
        stereo = np.column_stack((tone, tone))
        sound = pygame.sndarray.make_sound(stereo)
        sound.play()

    def update_geometry(self):
        if self.face_img is None or self.base_landmarks is None:
            return

        if self.viseme_buffer:
            delta = self.viseme_buffer.pop(0)
            # Ensure Float64 math
            dst_lms = self.base_landmarks.astype(np.float64)
            dst_lms += delta * self.sensitivity
            self.current_landmarks = dst_lms.astype(np.int32)
        else:
            self.current_landmarks = self.base_landmarks.copy()

    def render_sidebar(self, surface):
        surface.fill(C_SIDEBAR)
        
        # Header
        title = self.font_header.render("NEURAL ORACLE", True, C_ACCENT)
        surface.blit(title, (20, 20))
        
        # Status
        y_cursor = 60
        stats = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Sens: {self.sensitivity:.1f} | Scale: {self.warp_scale:.1f}",
            f"Mesh: {'ON' if self.mode_mesh else 'OFF'}"
        ]
        for stat in stats:
            txt = self.font_main.render(stat, True, C_TEXT_MAIN)
            surface.blit(txt, (20, y_cursor))
            y_cursor += 20

        # Shortcut Menu
        y_cursor += 20
        pygame.draw.rect(surface, C_MENU_BG, (10, y_cursor, 400, 200))
        head_keys = self.font_header.render("COMMAND LEDGER", True, C_TEXT_DIM)
        surface.blit(head_keys, (20, y_cursor + 10))
        
        ky = y_cursor + 40
        for keys, desc in self.shortcuts:
            k_surf = self.font_cmd.render(f"{keys:<7} {desc}", True, C_TEXT_MAIN)
            surface.blit(k_surf, (25, ky))
            ky += 18
            
        y_cursor += 220

        # Moments Gallery
        head_moments = self.font_header.render("MOMENTS", True, C_TEXT_MAIN)
        surface.blit(head_moments, (20, y_cursor))
        y_cursor += 30
        
        for m in self.moments:
            cat_surf = self.font_main.render(f"[{m['category']}]", True, C_ACCENT)
            surface.blit(cat_surf, (20, y_cursor))
            body_txt = m['text'][:40] + "..." 
            body_surf = self.font_main.render(body_txt, True, C_TEXT_DIM)
            surface.blit(body_surf, (20, y_cursor + 20))
            y_cursor += 45

        # Console Log
        pygame.draw.rect(surface, (0,0,0), (0, WINDOW_HEIGHT-100, SIDEBAR_WIDTH, 100))
        msg_lines = [self.current_msg[i:i+40] for i in range(0, len(self.current_msg), 40)]
        my = WINDOW_HEIGHT - 90
        for line in msg_lines:
            mt = self.font_main.render(line, True, C_ACCENT)
            surface.blit(mt, (10, my))
            my += 18

    def render_canvas(self, surface):
        if self.face_img is None:
            txt = self.font_header.render("AWAITING INPUT... [L] Video / [R] Image", True, C_ALERT)
            surface.blit(txt, (CANVAS_WIDTH//2 - 200, WINDOW_HEIGHT//2))
            return

        # 1. Image Render
        img_to_draw = self.face_img
        
        if self.mode_mesh and len(self.delaunay_triangles) > 0:
            warped_img = self.warper.process(
                self.face_img, 
                self.base_landmarks, 
                self.current_landmarks, 
                self.delaunay_triangles
            )
            # Pygame Surface conversion
            frame_rgb = cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB)
            img_to_draw = frame_rgb
        else:
            frame_rgb = cv2.cvtColor(self.face_img, cv2.COLOR_BGR2RGB)
            img_to_draw = frame_rgb

        # Surface Rotation/Flip for Pygame
        frame_surf = pygame.surfarray.make_surface(img_to_draw.swapaxes(0,1))
        surface.blit(frame_surf, (0,0))

        # 2. Overlay
        if not self.mode_mesh and self.current_landmarks is not None:
            # Draw mouth points only for clarity
            for i in range(48, 68):
                x, y = self.current_landmarks[i]
                pygame.draw.circle(surface, C_ACCENT, (x, y), 2)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_l:
                        self.load_video_source()
                    elif event.key == pygame.K_r:
                        self.load_static_image()
                    elif event.key == pygame.K_p:
                        self.current_msg = "Playing Buffer Sequence..."
                    elif event.key == pygame.K_s:
                        self.mode_strategy = "Auto" if self.mode_strategy == "Manual" else "Manual"
                        self.current_msg = f"Strategy: {self.mode_strategy}"
                    elif event.key == pygame.K_m:
                        self.mode_mesh = not self.mode_mesh
                    elif event.key == pygame.K_t:
                        self.tarot_reading()
                    elif event.key == pygame.K_1:
                        self.sensitivity = max(0.1, self.sensitivity - 0.1)
                    elif event.key == pygame.K_q:
                        self.sensitivity += 0.1
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

            self.update_geometry()

            # Render
            self.screen.fill(C_BG_MAIN)
            
            sidebar_surf = pygame.Surface((SIDEBAR_WIDTH, WINDOW_HEIGHT))
            self.render_sidebar(sidebar_surf)
            self.screen.blit(sidebar_surf, (0,0))
            
            canvas_surf = pygame.Surface((CANVAS_WIDTH, WINDOW_HEIGHT))
            self.render_canvas(canvas_surf)
            self.screen.blit(canvas_surf, (SIDEBAR_WIDTH, 0))
            
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = NeuralOracle()
    app.run()