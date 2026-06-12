import cv2
import dlib
import numpy as np
import pygame
import os
from tkinter import filedialog, Tk

# --- CONFIG ---
PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"
WIDTH, HEIGHT = 1250, 850

if not os.path.exists(PREDICTOR_PATH):
    print(f"CRITICAL: {PREDICTOR_PATH} not found.")
    exit()

# Initialize Models
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neural Lip-Sync Lab")
font = pygame.font.SysFont("Arial", 16)
clock = pygame.time.Clock()

STATE = {
    "display_surface": None,
    "neutral_landmarks": None,
    "frame_deltas": [],
    "current_frame_idx": 0,
    "progress": 0,
    "is_training": False,
    "status": "READY: Press 'L' to Load Video"
}

def open_file_dialog(file_types):
    """Safely opens a file dialog without crashing PyGame."""
    root = Tk()
    root.withdraw()  # Hide the main Tkinter window
    root.attributes("-topmost", True) # Bring dialog to front
    file_path = filedialog.askopenfilename(filetypes=file_types)
    root.destroy()
    return file_path

def get_mouth_coords(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)
    if not rects: return None
    shape = predictor(gray, rects[0])
    return np.array([[shape.part(i).x, shape.part(i).y] for i in range(68)])

def cv2_to_pygame(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.transpose(frame, (1, 0, 2))
    return pygame.surfarray.make_surface(frame)

def run_training(path):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    ret, frame = cap.read()
    if not ret: return
    
    STATE["neutral_landmarks"] = get_mouth_coords(frame)
    STATE["display_surface"] = cv2_to_pygame(frame)
    STATE["frame_deltas"] = []
    STATE["is_training"] = True
    
    idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        curr_lms = get_mouth_coords(frame)
        if curr_lms is not None:
            # Numerical diff (48-68 is the mouth)
            delta = curr_lms[48:68] - STATE["neutral_landmarks"][48:68]
            STATE["frame_deltas"].append(delta)
        
        idx += 1
        STATE["progress"] = int((idx / total) * 100)
        
        draw_ui()
        pygame.event.pump()
        pygame.display.flip()

    cap.release()
    STATE["is_training"] = False
    STATE["status"] = "TRAINING DONE. Use Slider to Scrub."

def draw_ui():
    screen.fill((20, 20, 25))
    
    # UI Panel
    pygame.draw.rect(screen, (35, 35, 45), (0, 0, 320, HEIGHT))
    screen.blit(font.render("CONTROLS", True, (0, 255, 150)), (20, 30))
    screen.blit(font.render("[L] LOAD VIDEO FILE", True, (255, 255, 255)), (20, 70))
    screen.blit(font.render("[R] REPLACE FACE IMG", True, (255, 255, 255)), (20, 100))
    
    # Status Message
    screen.blit(font.render(STATE["status"], True, (0, 200, 255)), (350, 20))

    if STATE["is_training"]:
        pygame.draw.rect(screen, (50, 50, 50), (20, 150, 280, 10))
        pygame.draw.rect(screen, (0, 255, 150), (20, 150, int(2.8 * STATE["progress"]), 10))

    # Canvas
    if STATE["display_surface"]:
        surf = pygame.transform.scale(STATE["display_surface"], (800, 600))
        screen.blit(surf, (350, 60))
        
        # Mouth Visualization
        if STATE["frame_deltas"] and not STATE["is_training"]:
            current_delta = STATE["frame_deltas"][STATE["current_frame_idx"]]
            for i, delta_pt in enumerate(current_delta):
                base_pt = STATE["neutral_landmarks"][48+i]
                # Map coordinates from original resolution to scaled 800x600 preview
                ratio_x = 800 / STATE["display_surface"].get_width()
                ratio_y = 600 / STATE["display_surface"].get_height()
                x = 350 + (base_pt[0] + delta_pt[0]) * ratio_x
                y = 60 + (base_pt[1] + delta_pt[1]) * ratio_y
                pygame.draw.circle(screen, (0, 255, 150), (int(x), int(y)), 3)

    # Scrubber
    bar_rect = pygame.Rect(350, 700, 800, 30)
    pygame.draw.rect(screen, (40, 40, 50), bar_rect, border_radius=15)
    if len(STATE["frame_deltas"]) > 0:
        handle_x = 350 + (STATE["current_frame_idx"] / len(STATE["frame_deltas"])) * 800
        pygame.draw.circle(screen, (0, 255, 150), (int(handle_x), 715), 12)

# --- MAIN LOOP ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_l:
                path = open_file_dialog([("Video files", "*.mp4 *.avi *.mov")])
                if path:
                    run_training(path)
            
            if event.key == pygame.K_r:
                path = open_file_dialog([("Image files", "*.jpg *.png *.jpeg")])
                if path:
                    img = cv2.imread(path)
                    lms = get_mouth_coords(img)
                    if lms is not None:
                        STATE["neutral_landmarks"] = lms
                        STATE["display_surface"] = cv2_to_pygame(img)
                        STATE["status"] = "Reference face updated."

    # Scrubber Input
    if mouse_click[0] and 350 < mouse_pos[0] < 1150 and 690 < mouse_pos[1] < 730:
        if len(STATE["frame_deltas"]) > 0:
            rel_x = mouse_pos[0] - 350
            STATE["current_frame_idx"] = int((rel_x / 800) * (len(STATE["frame_deltas"]) - 1))

    draw_ui()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()