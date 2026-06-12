import pygame
import cv2
import dlib
import numpy as np
import json
import os
import csv
import random
import tkinter as tk
from tkinter import filedialog

# --- CONFIGURATION & CONSTANTS ---
WINDOW_WIDTH, WINDOW_HEIGHT = 1400, 950
SIDEBAR_WIDTH = 420
CANVAS_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH

# Colors
C_BG_MAIN = (10, 10, 12)
C_SIDEBAR = (15, 15, 18)
C_ACCENT = (0, 255, 128)
C_TEXT_MAIN = (220, 220, 220)
C_TEXT_DIM = (100, 100, 120)
C_ALERT = (255, 50, 80)
C_MENU_BG = (28, 28, 32)

DATA_DIR = "oracle_data"
LANDMARK_PATH = "shape_predictor_68_face_landmarks.dat"
MOMENTS_FILE = os.path.join(DATA_DIR, "moments.json")
PHONETIC_FILE = os.path.join(DATA_DIR, "phonetic_dictionary.csv")

# --- GEOMETRIC ENGINE ---
class DelaunayWarper:
    def apply_affine_transform(self, src, src_tri, dst_tri, size):
        warp_mat = cv2.getAffineTransform(np.float32(src_tri), np.float32(dst_tri))
        return cv2.warpAffine(src, warp_mat, (size[0], size[1]), None, 
                             flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

    def warp_triangle(self, img_src, img_dst, t_src, t_dst):
        r1 = cv2.boundingRect(np.float32([t_src]))
        r2 = cv2.boundingRect(np.float32([t_dst]))
        t1_rect = [((t_src[i][0] - r1[0]), (t_src[i][1] - r1[1])) for i in range(3)]
        t2_rect = [((t_dst[i][0] - r2[0]), (t_dst[i][1] - r2[1])) for i in range(3)]
        
        mask = np.zeros((r2[3], r2[2], 3), dtype=np.float32)
        cv2.fillConvexPoly(mask, np.int32(t2_rect), (1.0, 1.0, 1.0), 16, 0)
        
        img1_rect = img_src[r1[1]:r1[1] + r1[3], r1[0]:r1[0] + r1[2]]
        img2_rect = self.apply_affine_transform(img1_rect, t1_rect, t2_rect, (r2[2], r2[3]))
        
        img_dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = \
            img_dst[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] * (1 - mask) + (img2_rect * mask)

    def process(self, img_src, points_src, points_dst, triangles):
        img_warped = np.copy(img_src).astype(np.float32)
        img_src_f = img_src.astype(np.float32)
        for tri in triangles:
            t1 = [points_src[tri[i]] for i in range(3)]
            t2 = [points_dst[tri[i]] for i in range(3)]
            self.warp_triangle(img_src_f, img_warped, t1, t2)
        return img_warped.astype(np.uint8)

# --- MAIN APP ---
class NeuralOracle:
    def __init__(self):
        self._init_persistence()
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Neural Oracle Rig")
        self.clock = pygame.time.Clock()
        
        # Resources
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(LANDMARK_PATH)
        self.warper = DelaunayWarper()
        self.font = pygame.font.SysFont("Consolas", 14)
        
        # State
        self.face_img = None
        self.base_lms = None
        self.curr_lms = None
        self.triangles = []
        self.playback_buffer = [] # List of (delta_array, phoneme_text)
        self.buffer_idx = 0
        self.sensitivity = 1.0
        self.mesh_mode = False
        self.running = True
        self.msg = "Oracle Ready. Press [L] for Video or [R] for Image."

    def _init_persistence(self):
        if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
        if not os.path.exists(PHONETIC_FILE):
            with open(PHONETIC_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['char', 'open', 'width'])
                writer.writerows([['A',15,5],['O',20,-5],['E',5,10],['M',0,-5],[' ',0,0]])
        if not os.path.exists(MOMENTS_FILE):
            with open(MOMENTS_FILE, 'w') as f:
                json.dump([{"id":1, "text":"Eyes widen... wicked smile.", "cat":"Mouth"}], f)

    def _get_phonetics(self):
        dct = {}
        with open(PHONETIC_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader: dct[row['char'].upper()] = (float(row['open']), float(row['width']))
        return dct

    def load_source(self, is_video=False):
        tk.Tk().withdraw()
        path = filedialog.askopenfilename()
        if not path: return
        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        cap.release()
        if ret:
            h, w = frame.shape[:2]
            scale = min(CANVAS_WIDTH/w, WINDOW_HEIGHT/h)
            frame = cv2.resize(frame, (int(w*scale), int(h*scale)))
            self.face_img = frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rects = self.detector(gray, 0)
            if rects:
                shape = self.predictor(gray, rects[0])
                self.base_lms = np.array([[p.x, p.y] for p in shape.parts()], dtype=np.float64)
                self.curr_lms = self.base_lms.copy()
                self._build_mesh()
                self.msg = "Baseline set. Calibration Complete."

    def _build_mesh(self):
        rect = (0, 0, self.face_img.shape[1], self.face_img.shape[0])
        subdiv = cv2.Subdiv2D(rect)
        indices = list(range(48, 68)) + [4, 8, 12] # Mouth + Jaw Anchors
        for i in indices: subdiv.insert((float(self.base_lms[i][0]), float(self.base_lms[i][1])))
        for t in subdiv.getTriangleList():
            pts = [(t[0], t[1]), (t[2], t[3]), (t[4], t[5])]
            tri_idx = []
            for p in pts:
                for i in indices:
                    if abs(p[0]-self.base_lms[i][0]) < 1 and abs(p[1]-self.base_lms[i][1]) < 1:
                        tri_idx.append(i)
                        break
            if len(tri_idx) == 3: self.triangles.append(tri_idx)

    def play_sequence(self, text):
        ph_map = self._get_phonetics()
        self.playback_buffer = []
        for char in text.upper():
            delta = np.zeros((68, 2), dtype=np.float64)
            vals = ph_map.get(char, (0, 0))
            delta[61:68, 1] = vals[0] # Vertical Open
            delta[[48, 54, 60, 64], 0] = [vals[1], -vals[1], vals[1], -vals[1]] # Width
            self.playback_buffer.extend([(delta, char)] * 4) # 4 frames per phoneme
        self.buffer_idx = 0

    def update(self):
        if self.playback_buffer and self.buffer_idx < len(self.playback_buffer):
            delta, char = self.playback_buffer[self.buffer_idx]
            self.curr_lms = self.base_lms + (delta * self.sensitivity)
            self.buffer_idx += 1
        elif self.base_lms is not None:
            self.curr_lms = self.base_lms.copy()

    def draw(self):
        self.screen.fill(C_BG_MAIN)
        # Sidebar
        pygame.draw.rect(self.screen, C_SIDEBAR, (0, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT))
        y = 20
        for cmd in ["[L] Load Video", "[R] Image", "[P] Speak Moment", "[T] Tarot", "[M] Mesh", "[1/Q] Sens"]:
            self.screen.blit(self.font.render(cmd, True, C_TEXT_DIM), (20, y))
            y += 25
        
        # Canvas
        if self.face_img is not None:
            img = self.face_img
            if self.mesh_mode:
                img = self.warper.process(self.face_img, self.base_lms, self.curr_lms, self.triangles)
            
            surf = pygame.surfarray.make_surface(cv2.cvtColor(img, cv2.COLOR_BGR2RGB).swapaxes(0,1))
            self.screen.blit(surf, (SIDEBAR_WIDTH + 20, 20))
            
            # Scrubber
            if self.playback_buffer:
                prog = self.buffer_idx / len(self.playback_buffer)
                pygame.draw.rect(self.screen, C_MENU_BG, (SIDEBAR_WIDTH + 50, 900, 800, 15))
                pygame.draw.rect(self.screen, C_ACCENT, (SIDEBAR_WIDTH + 50, 900, 800 * prog, 15))
                char_txt = self.playback_buffer[self.buffer_idx-1][1] if self.buffer_idx > 0 else "-"
                self.screen.blit(self.font.render(f"Phoneme: {char_txt}", True, C_ACCENT), (SIDEBAR_WIDTH + 50, 875))

        pygame.display.flip()

    def run(self):
        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: self.running = False
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_l: self.load_source(True)
                    if e.key == pygame.K_r: self.load_source(False)
                    if e.key == pygame.K_m: self.mesh_mode = not self.mesh_mode
                    if e.key == pygame.K_p: self.play_sequence("AAA OOO EEE")
                    if e.key == pygame.K_q: self.sensitivity += 0.2
                    if e.key == pygame.K_1: self.sensitivity -= 0.2
            self.update()
            self.draw()
            self.clock.tick(30)

if __name__ == "__main__":
    NeuralOracle().run()