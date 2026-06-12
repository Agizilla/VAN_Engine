import cv2
import dlib
import numpy as np
import pygame
import os
import time
import random
from tkinter import filedialog, Tk

# --- TAROT DATABASE (LOCAL) ---
TAROT_DECK = {
    "THE FOOL": "New beginnings, optimism, and trust in the universe.",
    "THE MAGICIAN": "Manifestation, resourcefulness, and personal power.",
    "THE HIGH PRIESTESS": "Intuition, sacred knowledge, and the subconscious mind.",
    "THE EMPRESS": "Femininity, beauty, nature, and abundance.",
    "THE EMPEROR": "Authority, establishment, structure, and a father figure.",
    "THE HIEROPHANT": "Spiritual wisdom, religious beliefs, and tradition.",
    "THE LOVERS": "Love, harmony, partnerships, and choices.",
    "THE CHARIOT": "Control, willpower, success, and determination.",
    "STRENGTH": "Strength, courage, persuasion, and influence.",
    "THE HERMIT": "Soul searching, introspection, and being alone.",
    "WHEEL OF FORTUNE": "Good luck, karma, life cycles, and destiny.",
    "JUSTICE": "Justice, fairness, truth, and the law.",
    "THE HANGED MAN": "Pause, surrender, letting go, and new perspectives.",
    "DEATH": "Endings, change, transformation, and transition.",
    "TEMPERANCE": "Balance, moderation, patience, and purpose.",
    "THE DEVIL": "Shadow self, attachment, addiction, and restriction.",
    "THE TOWER": "Sudden change, upheaval, chaos, and revelation.",
    "THE STAR": "Hope, faith, purpose, and renewal.",
    "THE MOON": "Illusion, fear, anxiety, and intuition.",
    "THE SUN": "Positivity, fun, warmth, success, and vitality.",
    "JUDGEMENT": "Judgement, rebirth, inner calling, and absolution.",
    "THE WORLD": "Completion, integration, accomplishment, and travel."
}

# --- CONFIG & STATE ---
PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"
WIDTH, HEIGHT = 1350, 950
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neural Oracle - Offline Tarot & LipSync")
font = pygame.font.SysFont("Courier", 14)
oracle_font = pygame.font.SysFont("Georgia", 22, italic=True)

CONFIG = {"THRESHOLD": 8.0, "PLAY_SPEED": 0.25, "BEEP_FREQ": 440}
STATE = {
    "cv_img": None, "display_surface": None, "neutral_landmarks": None,
    "frame_deltas": [], "dictionary": {}, "current_frame_idx": 0,
    "input_text": "", "status": "OFFLINE ORACLE READY", "is_playing": False,
    "current_card": None, "oracle_text": ""
}

# --- CORE UTILITIES ---

def generate_beep():
    sample_rate = 44100
    n_samples = int(sample_rate * 0.1)
    buf = np.sin(2 * np.pi * np.arange(n_samples) * CONFIG["BEEP_FREQ"] / sample_rate).astype(np.float32)
    pygame.mixer.Sound(array=buf).play()

def apply_mesh_warp(img, base_lms, delta):
    dst_lms = base_lms.copy()
    dst_lms[48:68] += delta
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
        out_img[y:y+h, x:x+w] = out_img[y:y+h, x:x+w] * (1 - mask) + img2_rect * mask
    return out_img

# --- ORACLE LOGIC ---

def draw_tarot():
    """Selects a card and prepares the face to 'read' the meaning."""
    card, meaning = random.choice(list(TAROT_DECK.items()))
    STATE["current_card"] = card
    STATE["oracle_text"] = meaning
    STATE["status"] = f"ORACLE DRAWN: {card}"
    
    # Execution: Replay the meaning visually
    words = meaning.lower().replace(",", "").replace(".", "").split()
    for w in words:
        # Check if word or phonetic equivalent exists in dictionary
        # If not in dictionary, we find the closest "word_X" from training
        target_delta = None
        if w in STATE["dictionary"]:
            target_delta = STATE["dictionary"][w]
        elif STATE["dictionary"]: # Fallback to a random learned movement
            target_delta = random.choice(list(STATE["dictionary"].values()))
        
        if target_delta is not None:
            render_face(target_delta)
        else:
            generate_beep()
        
        # UI Update during reading
        pygame.event.pump()
        time.sleep(CONFIG["PLAY_SPEED"])
    
    render_face(np.zeros((20, 2))) # Return to neutral

def render_face(delta):
    if STATE["cv_img"] is None: return
    warped = apply_mesh_warp(STATE["cv_img"], STATE["neutral_landmarks"], delta)
    surf = cv2.surfarray.make_surface(np.transpose(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB), (1, 0, 2)))
    # Positioning logic omitted for brevity, same as V5
    screen.blit(pygame.transform.smoothscale(surf, (800, 600)), (400, 100))
    pygame.display.flip()

# --- UI & CONFIG PANEL ---

def draw_ui():
    screen.fill((10, 10, 15))
    # Sidebar
    pygame.draw.rect(screen, (25, 25, 30), (0, 0, 350, HEIGHT))
    y = 30
    screen.blit(font.render("--- ORACLE CONTROLS ---", True, (150, 0, 255)), (20, y))
    y += 40
    screen.blit(font.render("[T] DRAW TAROT CARD", True, (255, 255, 255)), (20, y))
    y += 30
    screen.blit(font.render("[L] TRAIN NEW VIDEO", True, (200, 200, 200)), (20, y))
    y += 30
    
    if STATE["current_card"]:
        pygame.draw.rect(screen, (40, 40, 60), (20, y, 310, 150), border_radius=10)
        screen.blit(bold_font.render(STATE["current_card"], True, (255, 215, 0)), (40, y + 20))
        # Simple wrap for meaning text
        m_lines = [STATE["oracle_text"][i:i+30] for i in range(0, len(STATE["oracle_text"]), 30)]
        for i, line in enumerate(m_lines):
            screen.blit(font.render(line, True, (200, 200, 200)), (40, y + 60 + i*20))

# --- MAIN LOOP ---
running = True
while running:
    draw_ui()
    # Rendering face and scrubber logic from V5...
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t: draw_tarot()
            # Other keys (L, R, S, P) as per previous versions...

    pygame.display.flip()
    clock.tick(30)
pygame.quit()