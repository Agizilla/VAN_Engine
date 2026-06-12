import cv2
import dlib
import numpy as np
import pygame
import os
import time
import json
import random
from tkinter import filedialog, Tk

# --- PATHS ---
DATA_DIR = "oracle_data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"

# --- CORE INITIALIZATION ---
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((1400, 950))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Courier", 14)

# --- SYSTEM STATE ---
CONFIG = {"THRESHOLD": 8.0, "SCALE_ADJUST": 1.2, "PLAY_SPEED": 0.15, "SHOW_MESH": True, "STRATEGY": "AUTO-THRESHOLD"}
STATE = {
    "cv_img": None, "neutral_landmarks": None, "frame_deltas": [],
    "dictionary": {}, "input_text": "", "status": "READY", "is_playing": False,
    "current_frame_idx": 0, "tarot_card": None
}

TAROT_DECK = {
    "THE TOWER": "Sudden upheaval and revelation.",
    "THE STAR": "Hope and renewed faith.",
    "THE MOON": "Intuition and the subconscious.",
    "THE SUN": "Success and vitality."
}

# --- GEOMETRIC ENGINE ---

def apply_mesh_warp(img, base_lms, delta):
    """Implementation of [M] Mesh Toggle logic and [2/W] Warp Scaling."""
    applied_delta = delta * CONFIG["SCALE_ADJUST"]
    dst_lms = base_lms.copy()
    dst_lms[48:68] += applied_delta
    
    # Precise triangulation for lip/mouth mesh
    triangles = [[48,49,60], [49,50,61], [50,51,62], [51,52,62], [52,53,63], [53,54,64], [54,55,64], [55,56,65], [56,57,66], [57,58,67], [58,48,67], [48,60,67]]
    
    out_img = img.copy()
    for tri in triangles:
        src = np.float32([base_lms[i] for i in tri])
        dst = np.float32([dst_lms[i] for i in tri])
        r1, r2 = cv2.boundingRect(src), cv2.boundingRect(dst)
        img1_rect = img[r1[1]:r1[1]+r1[3], r1[0]:r1[0]+r1[2]]
        src_rect, dst_rect = src - (r1[0], r1[1]), dst - (r2[0], r2[1])
        mask = np.zeros((r2[3], r2[2], 3), dtype=np.float32)
        cv2.fillConvexPoly(mask, np.int32(dst_rect), (1.0, 1.0, 1.0), 16, 0)
        warp_mat = cv2.getAffineTransform(src_rect, dst_rect)
        img2_rect = cv2.warpAffine(img1_rect, warp_mat, (r2[2], r2[3]))
        x, y, w, h = r2
        out_img[y:y+h, x:x+w] = (out_img[y:y+h, x:x+w] * (1 - mask) + img2_rect * mask).astype(np.uint8)
    return out_img

# --- SYSTEM ACTION HANDLERS ---

def get_mouth_coords(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)
    if not rects: return None
    shape = predictor(gray, rects[0])
    return np.array([[p.x, p.y] for p in shape.parts()])

def run_training(path):
    """Implementation of [L] Load/Train Video."""
    cap = cv2.VideoCapture(path)
    ret, frame = cap.read()
    if not ret: return
    STATE["neutral_landmarks"] = get_mouth_coords(frame)
    STATE["cv_img"] = frame
    STATE["frame_deltas"] = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        lms = get_mouth_coords(frame)
        if lms is not None:
            delta = lms[48:68] - STATE["neutral_landmarks"][48:68]
            STATE["frame_deltas"].append(delta)
            # [S] Strategy logic
            if CONFIG["STRATEGY"] == "AUTO-THRESHOLD":
                if np.linalg.norm(delta) > CONFIG["THRESHOLD"]:
                    STATE["dictionary"][f"v_{len(STATE['dictionary'])}"] = delta
            else:
                STATE["dictionary"][f"f_{len(STATE['frame_deltas'])}"] = delta
    cap.release()
    STATE["status"] = "TRAINING COMPLETE"

def render_frame(delta):
    if STATE["cv_img"] is None: return
    # [M] Mesh vs Dot Overlay
    if CONFIG["SHOW_MESH"]:
        img = apply_mesh_warp(STATE["cv_img"], STATE["neutral_landmarks"], delta)
    else:
        img = STATE["cv_img"].copy()
        for pt in (STATE["neutral_landmarks"][48:68] + delta * CONFIG["SCALE_ADJUST"]):
            cv2.circle(img, (int(pt[0]), int(pt[1])), 2, (0, 255, 0), -1)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    surf = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
    scale = min(800/img.shape[1], 600/img.shape[0])
    scaled = pygame.transform.smoothscale(surf, (int(img.shape[1]*scale), int(img.shape[0]*scale)))
    screen.blit(scaled, (450, 100))
    pygame.display.flip()

def play_text(text):
    """Implementation of [P] Play/Replay Text with [Phonetic Approximation]."""
    STATE["is_playing"] = True
    for word in text.lower().split():
        delta = STATE["dictionary"].get(word, None)
        if delta is None:
            # Phonetic Approximation: Choose random from dictionary
            delta = random.choice(list(STATE["dictionary"].values())) if STATE["dictionary"] else np.zeros((20, 2))
            # 440Hz Sine Beep
            sample_rate = 44100
            buf = np.sin(2 * np.pi * np.arange(int(sample_rate*0.1)) * 440 / sample_rate).astype(np.float32)
            pygame.mixer.Sound(array=buf).play()
        render_frame(delta)
        time.sleep(CONFIG["PLAY_SPEED"])
    STATE["is_playing"] = False

def export_mp4():
    """Implementation of [E] Export MP4."""
    if STATE["cv_img"] is None: return
    h, w = STATE["cv_img"].shape[:2]
    out = cv2.VideoWriter("exported_sync.mp4", cv2.VideoWriter_fourcc(*'mp4v'), 30, (w, h))
    for delta in STATE["frame_deltas"]:
        out.write(apply_mesh_warp(STATE["cv_img"], STATE["neutral_landmarks"], delta))
    out.release()
    STATE["status"] = "EXPORTED: exported_sync.mp4"

# --- MAIN LOOP ---
while True:
    screen.fill((20, 20, 25))
    # Render static face if idle
    if STATE["cv_img"] is not None and not STATE["is_playing"]:
        d = STATE["frame_deltas"][STATE["current_frame_idx"]] if STATE["frame_deltas"] else np.zeros((20, 2))
        render_frame(d)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); exit()
        if event.type == pygame.KEYDOWN:
            # File Actions
            if event.key == pygame.K_l:
                tk = Tk(); tk.withdraw(); p = filedialog.askopenfilename(); tk.destroy()
                if p: run_training(p)
            if event.key == pygame.K_r: # [R] Replace Face
                tk = Tk(); tk.withdraw(); p = filedialog.askopenfilename(); tk.destroy()
                if p:
                    STATE["cv_img"] = cv2.imread(p)
                    STATE["neutral_landmarks"] = get_mouth_coords(STATE["cv_img"])
            
            # Logic Actions
            if event.key == pygame.K_p: play_text(STATE["input_text"])
            if event.key == pygame.K_s: CONFIG["STRATEGY"] = "MANUAL" if CONFIG["STRATEGY"] == "AUTO-THRESHOLD" else "AUTO-THRESHOLD"
            if event.key == pygame.K_m: CONFIG["SHOW_MESH"] = not CONFIG["SHOW_MESH"]
            if event.key == pygame.K_e: export_mp4()
            if event.key == pygame.K_t: # [T] Tarot
                STATE["tarot_card"] = random.choice(list(TAROT_DECK.keys()))
                play_text(TAROT_DECK[STATE["tarot_card"]])
            
            # [1/Q] and [2/W] Config
            if event.key == pygame.K_1: CONFIG["THRESHOLD"] += 1
            if event.key == pygame.K_q: CONFIG["THRESHOLD"] = max(1, CONFIG["THRESHOLD"] - 1)
            if event.key == pygame.K_2: CONFIG["SCALE_ADJUST"] += 0.1
            if event.key == pygame.K_w: CONFIG["SCALE_ADJUST"] = max(0.1, CONFIG["SCALE_ADJUST"] - 0.1)

            # Typing
            if event.key == pygame.K_BACKSPACE: STATE["input_text"] = STATE["input_text"][:-1]
            elif event.unicode.isprintable(): STATE["input_text"] += event.unicode

    pygame.display.flip()
    clock.tick(30)