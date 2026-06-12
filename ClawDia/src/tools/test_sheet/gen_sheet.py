import cv2
import numpy as np
from pathlib import Path

out_dir = Path(r"C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ClawDia\src\tools\test_sheet")

ROWS, COLS = 2, 6
W = 10 + COLS * 80
H = 50 + ROWS * 120
sheet = np.ones((H, W, 3), dtype=np.uint8) * 250

COCOA = (90, 70, 130)
TEAL = (140, 150, 60)

def fig(canvas, ox, oy, color, breast, pose):
    hr, bl, al, ll = 9, 28, 16, 22
    ny = oy - bl
    hc = ny - hr
    cv2.circle(canvas, (ox, hc), hr, color, 2)
    cv2.line(canvas, (ox, ny), (ox, oy), color, 2)
    if breast:
        lx, rx = ox - 6, ox + 6
        by = ny + 8
        cv2.circle(canvas, (lx, by), 4, color, 2)
        cv2.circle(canvas, (rx, by), 4, color, 2)
        cv2.circle(canvas, (lx, by), 2, color, -1)
        cv2.circle(canvas, (rx, by), 2, color, -1)
    if pose == "stand":
        cv2.line(canvas, (ox, ny + 3), (ox - al, ny + 12), color, 2)
        cv2.line(canvas, (ox, ny + 3), (ox + al, ny + 12), color, 2)
        cv2.line(canvas, (ox, oy), (ox - 7, oy + ll), color, 2)
        cv2.line(canvas, (ox, oy), (ox + 7, oy + ll), color, 2)
    elif pose == "wide":
        cv2.line(canvas, (ox, ny + 3), (ox - al - 4, ny + 10), color, 2)
        cv2.line(canvas, (ox, ny + 3), (ox + al + 4, ny + 10), color, 2)
        cv2.line(canvas, (ox, oy), (ox - 16, oy + ll), color, 2)
        cv2.line(canvas, (ox, oy), (ox + 16, oy + ll), color, 2)
    elif pose == "arms_up":
        cv2.line(canvas, (ox, ny + 3), (ox - al + 3, ny - 8), color, 2)
        cv2.line(canvas, (ox, ny + 3), (ox + al - 3, ny - 8), color, 2)
        cv2.line(canvas, (ox, oy), (ox - 8, oy + ll), color, 2)
        cv2.line(canvas, (ox, oy), (ox + 8, oy + ll), color, 2)
    elif pose == "point":
        cv2.line(canvas, (ox, ny + 3), (ox - al - 2, ny + 10), color, 2)
        cv2.line(canvas, (ox, ny + 3), (ox + al + 6, ny - 2), color, 2)
        cv2.line(canvas, (ox, oy), (ox - 8, oy + ll), color, 2)
        cv2.line(canvas, (ox, oy), (ox + 8, oy + ll), color, 2)
    elif pose == "hips":
        cv2.line(canvas, (ox, ny + 3), (ox - al + 2, oy - 4), color, 2)
        cv2.line(canvas, (ox, ny + 3), (ox + al - 2, oy - 4), color, 2)
        cv2.line(canvas, (ox, oy), (ox - 12, oy + ll - 4), color, 2)
        cv2.line(canvas, (ox, oy), (ox + 12, oy + ll - 4), color, 2)
    elif pose == "splay":
        cv2.line(canvas, (ox, ny + 3), (ox - al - 6, ny + 14), color, 2)
        cv2.line(canvas, (ox, ny + 3), (ox + al + 6, ny + 14), color, 2)
        cv2.line(canvas, (ox, oy), (ox - 20, oy + ll + 4), color, 2)
        cv2.line(canvas, (ox, oy), (ox + 20, oy + ll + 4), color, 2)

poses = ["stand", "wide", "arms_up", "point", "hips", "splay"]
labels = ["STAND", "WIDE", "ARMS UP", "POINT", "ON HIPS", "SPLAY"]

for ci, pose in enumerate(poses):
    cx = 10 + ci * 80 + 40
    # Ara (female, teal) - WITH nipples
    fig(sheet, cx, 70, TEAL, True, pose)
    cv2.putText(sheet, "Ara", (cx - 14, 112), cv2.FONT_HERSHEY_SIMPLEX, 0.35, TEAL, 1)
    # Gerrit (male, cocoa)
    fig(sheet, cx, 190, COCOA, False, pose)
    cv2.putText(sheet, "Gerrit", (cx - 20, 232), cv2.FONT_HERSHEY_SIMPLEX, 0.35, COCOA, 1)
    # Pose label
    cv2.putText(sheet, labels[ci], (cx - 18, 254), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (120, 120, 120), 1)

cv2.putText(sheet, "midnight_rage_volume5  -  Character Sprite Sheet", (90, 278),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1)

out_path = out_dir / "midnight_rage_sprite_sheet.png"
cv2.imwrite(str(out_path), sheet)
print("MIDNIGHT RAGE: %dx%d  %d bytes" % (sheet.shape[1], sheet.shape[0], out_path.stat().st_size))

# ===========================
# THE UNBALANCED LEDGER - Volume 1 Sprite Sheet
# ===========================
# Characters: Liora Vance, Seraphine (The Caged), The Butler (Laurence Wells)
UL_R, UL_C = 3, 6
UL_W = 10 + UL_C * 80
UL_H = 60 + UL_R * 120
ul = np.ones((UL_H, UL_W, 3), dtype=np.uint8) * 250

LIORA = (200, 140, 30)    # electric blue
SERAPHINE = (30, 200, 220) # luminous gold
BUTLER = (120, 120, 120)   # charcoal / sterile gray

chars_v1 = [
    ("Liora",   LIORA,    True,  110),
    ("Seraphine", SERAPHINE, True,  230),
    ("The Butler", BUTLER,      False, 350),
]

for ci, pose in enumerate(poses):
    cx = 10 + ci * 80 + 40
    for name, col, has_breast, oy in chars_v1:
        fig(ul, cx, oy, col, has_breast, pose)
        tw = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)[0][0]
        cv2.putText(ul, name, (cx - tw // 2, oy + 44), cv2.FONT_HERSHEY_SIMPLEX, 0.35, col, 1)
    cv2.putText(ul, labels[ci], (cx - 18, UL_H - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (120, 120, 120), 1)

cv2.putText(ul, "THE UNBALANCED LEDGER  -  Character Sprite Sheet", (75, UL_H - 34),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1)

out_path2 = out_dir / "unbalanced_ledger_sprite_sheet.png"
cv2.imwrite(str(out_path2), ul)
print("UNBALANCED LEDGER: %dx%d  %d bytes" % (ul.shape[1], ul.shape[0], out_path2.stat().st_size))

print("DONE")
