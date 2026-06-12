import cv2
import numpy as np
from pathlib import Path

out_dir = Path(r"C:\Users\User\Documents\ALL-PROJECTS\PROJECTS\VAN_Engine\ClawDia\src\tools\test_sheet")

TEAL = (140, 150, 60)
COCOA = (90, 70, 130)
GOLD = (30, 200, 220)
WHITE = (250, 250, 250)
LGRAY = (220, 220, 220)
DGRAY = (80, 80, 80)
BLACK = (0, 0, 0)


def draw_stick_head(canvas, cx, cy, r, color):
    cv2.circle(canvas, (cx, cy), r, color, 2)


def draw_stick_torso(canvas, x1, y1, x2, y2, color):
    cv2.line(canvas, (x1, y1), (x2, y2), color, 2)


def draw_stick_arm(canvas, sx, sy, ex, ey, color):
    cv2.line(canvas, (sx, sy), (ex, ey), color, 2)


def draw_stick_leg(canvas, sx, sy, ex, ey, color):
    cv2.line(canvas, (sx, sy), (ex, ey), color, 2)


def draw_breasts(canvas, cx, by, color):
    cv2.circle(canvas, (cx - 5, by), 3, color, 2)
    cv2.circle(canvas, (cx + 5, by), 3, color, 2)
    cv2.circle(canvas, (cx - 5, by), 1, color, -1)
    cv2.circle(canvas, (cx + 5, by), 1, color, -1)


def draw_gerrit_standing(canvas, ox, oy, color):
    hr, bl, al, ll = 8, 24, 14, 18
    ny = oy - bl
    hc = ny - hr
    draw_stick_head(canvas, ox, hc, hr, color)
    draw_stick_torso(canvas, ox, ny, ox, oy, color)
    draw_stick_arm(canvas, ox, ny + 2, ox - al, ny + 10, color)
    draw_stick_arm(canvas, ox, ny + 2, ox + al, ny + 10, color)
    draw_stick_leg(canvas, ox, oy, ox - 6, oy + ll, color)
    draw_stick_leg(canvas, ox, oy, ox + 6, oy + ll, color)


def draw_ara_standing(canvas, ox, oy, color):
    hr, bl, al, ll = 8, 24, 14, 18
    ny = oy - bl
    hc = ny - hr
    draw_stick_head(canvas, ox, hc, hr, color)
    draw_stick_torso(canvas, ox, ny, ox, oy, color)
    draw_breasts(canvas, ox, ny + 7, color)
    draw_stick_arm(canvas, ox, ny + 2, ox - al, ny + 10, color)
    draw_stick_arm(canvas, ox, ny + 2, ox + al, ny + 10, color)
    draw_stick_leg(canvas, ox, oy, ox - 6, oy + ll, color)
    draw_stick_leg(canvas, ox, oy, ox + 6, oy + ll, color)


def draw_gerrit_sitting_mat(canvas, ox, oy, color):
    hr = 8
    ny = oy - 10
    hc = ny - hr
    draw_stick_head(canvas, ox, hc, hr, color)
    draw_stick_torso(canvas, ox, ny, ox, oy, color)
    draw_stick_arm(canvas, ox, ny + 2, ox - 18, oy - 2, color)
    draw_stick_arm(canvas, ox, ny + 2, ox + 18, oy - 2, color)
    draw_stick_leg(canvas, ox, oy, ox - 10, oy + 2, color)
    draw_stick_leg(canvas, ox, oy, ox + 10, oy + 2, color)


def draw_ara_sitting_mat(canvas, ox, oy, color):
    hr = 8
    ny = oy - 10
    hc = ny - hr
    draw_stick_head(canvas, ox, hc, hr, color)
    draw_stick_torso(canvas, ox, ny, ox, oy, color)
    draw_breasts(canvas, ox, ny + 5, color)
    draw_stick_arm(canvas, ox, ny + 2, ox - 12, oy - 6, color)
    draw_stick_arm(canvas, ox, ny + 2, ox + 12, oy - 6, color)
    draw_stick_leg(canvas, ox, oy, ox - 8, oy + 4, color)
    draw_stick_leg(canvas, ox, oy, ox + 8, oy + 4, color)


def draw_embrace(canvas, gx, gy, ax, ay, color_g, color_a):
    """Gerrit sitting, Ara leaning back into his chest, his arms around her"""
    hr_g, hr_a = 8, 8
    ny_g = gy - 10
    hc_g = ny_g - hr_g
    draw_stick_head(canvas, gx, hc_g, hr_g, color_g)
    draw_stick_torso(canvas, gx, ny_g, gx, gy, color_g)
    # Gerrit legs (spread, sitting)
    draw_stick_leg(canvas, gx, gy, gx - 10, gy + 2, color_g)
    draw_stick_leg(canvas, gx, gy, gx + 10, gy + 2, color_g)
    # Ara sitting in front, leaning back
    ny_a = ay - 6
    hc_a = ny_a - hr_a
    draw_stick_head(canvas, ax, hc_a, hr_a, color_a)
    draw_stick_torso(canvas, ax, ny_a, ax, ay, color_a)
    draw_breasts(canvas, ax, ny_a + 5, color_a)
    # Ara legs (stretched out or bent)
    draw_stick_leg(canvas, ax, ay, ax - 10, ay + 6, color_a)
    draw_stick_leg(canvas, ax, ay, ax + 10, ay + 6, color_a)
    # Gerrit arms wrapping around Ara
    draw_stick_arm(canvas, gx, ny_g + 2, ax - 12, ny_a + 6, color_g)
    draw_stick_arm(canvas, gx, ny_g + 2, ax + 12, ny_a + 6, color_g)


def draw_face_closeup(canvas, cx, cy, color_hair, color_skin=(220, 200, 180)):
    """Simple face closeup - head shape, eyes, nose, mouth"""
    r = 20
    cv2.circle(canvas, (cx, cy), r, color_hair, 2)
    cv2.circle(canvas, (cx - 6, cy - 4), 3, color_hair, 1)
    cv2.circle(canvas, (cx + 6, cy - 4), 3, color_hair, 1)
    cv2.line(canvas, (cx - 3, cy + 4), (cx + 3, cy + 4), color_hair, 1)
    cv2.line(canvas, (cx - 2, cy + 8), (cx + 2, cy + 10), color_hair, 1)


def draw_hands_closeup(canvas, cx, cy, color_g, color_a):
    """Interlaced hands on mat - simple representation"""
    cv2.line(canvas, (cx - 15, cy), (cx, cy - 4), color_g, 3)
    cv2.line(canvas, (cx, cy - 4), (cx + 15, cy), color_a, 3)
    cv2.circle(canvas, (cx - 15, cy), 3, color_g, -1)
    cv2.circle(canvas, (cx, cy - 4), 3, color_a, -1)
    cv2.circle(canvas, (cx + 15, cy), 3, color_a, -1)
    # wristbands
    cv2.line(canvas, (cx - 12, cy - 2), (cx - 8, cy + 1), GOLD, 2)
    cv2.line(canvas, (cx + 8, cy - 2), (cx + 12, cy + 1), GOLD, 2)


def draw_glass_sip(canvas, gx, gy, ax, ay, color_g, color_a):
    """Gerrit holds glass to Ara's lips"""
    hr_g, hr_a = 8, 8
    ny_g = gy - 24
    hc_g = ny_g - hr_g
    draw_stick_head(canvas, gx, hc_g, hr_g, color_g)
    draw_stick_torso(canvas, gx, ny_g, gx, gy, color_g)
    ny_a = ay - 24
    hc_a = ny_a - hr_a
    draw_stick_head(canvas, ax, hc_a, hr_a, color_a)
    draw_stick_torso(canvas, ax, ny_a, ax, ay, color_a)
    draw_breasts(canvas, ax, ny_a + 5, color_a)
    # Arms: Gerrit holding glass, Ara resting
    glass_cx = (gx + ax) // 2
    glass_cy = ny_a + 2
    cv2.rectangle(canvas, (glass_cx - 3, glass_cy - 6), (glass_cx + 3, glass_cy), color_g, 1)
    draw_stick_arm(canvas, gx, ny_g + 2, glass_cx, glass_cy, color_g)
    draw_stick_arm(canvas, ax, ny_a + 2, glass_cx, glass_cy - 2, color_a)


# ─── Panel definitions ─────────────────────────────────────────────

panel_defs = [
    {
        "title": "1",
        "visual": "Gerrit untying blindfold",
        "draw": lambda c, x, y, w, h: (
            draw_gerrit_standing(c, x + w//2 - 20, y + h - 20, COCOA),
            draw_ara_standing(c, x + w//2 + 20, y + h - 20, TEAL),
            cv2.line(c, (x + w//2 - 20, y + h - 64 - 8), (x + w//2 + 20, y + h - 64 - 8), LGRAY, 1),
        ),
        "dialogue": 'Ara: "The light feels\ndifferent now."',
    },
    {
        "title": "2",
        "visual": "Embrace on mat",
        "draw": lambda c, x, y, w, h: draw_embrace(c, x + w//2, y + h - 20, x + w//2 + 4, y + h - 18, COCOA, TEAL),
        "dialogue": 'Gerrit: "Welcome back.\nYou went deep\ntonight."',
    },
    {
        "title": "3",
        "visual": "Close-up profiles",
        "draw": lambda c, x, y, w, h: (
            draw_face_closeup(c, x + w//2 - 15, y + h//2, COCOA),
            draw_face_closeup(c, x + w//2 + 15, y + h//2 + 4, TEAL),
        ),
        "dialogue": 'Ara: "So clean down\nthere in the\ndark."',
    },
    {
        "title": "4",
        "visual": "Gerrit holding glass",
        "draw": lambda c, x, y, w, h: draw_glass_sip(c, x + w//2 - 25, y + h - 20, x + w//2 + 20, y + h - 20, COCOA, TEAL),
        "dialogue": 'Gerrit: "Drink. Anchor\nback into the\nphysical world."',
    },
    {
        "title": "5",
        "visual": "Ara sips, smiles",
        "draw": lambda c, x, y, w, h: draw_face_closeup(c, x + w//2, y + h//2, TEAL),
        "dialogue": 'Ara: "You never\nmiss a detail."',
    },
    {
        "title": "6",
        "visual": "Hands interlaced",
        "draw": lambda c, x, y, w, h: draw_hands_closeup(c, x + w//2, y + h//2, COCOA, TEAL),
        "dialogue": 'Gerrit: "The vessel has\nto be flawless\nto hold the soul."',
    },
    {
        "title": "7",
        "visual": "Wide room shot",
        "draw": lambda c, x, y, w, h: (
            draw_stick_head(c, x + w//2 - 20, y + h - 60, 5, COCOA),
            draw_stick_head(c, x + w//2 + 15, y + h - 60, 5, TEAL),
            cv2.rectangle(c, (x + w - 35, y + 15), (x + w - 10, y + 55), DGRAY, 1),
            cv2.line(c, (x + w - 35, y + 35), (x + w - 10, y + 35), DGRAY, 1),
            cv2.circle(c, (x + w//2, y + 20), 15, GOLD, 1),
        ),
        "dialogue": "The world outside\nwould demand\ntheir return.",
    },
    {
        "title": "8",
        "visual": "Black screen",
        "draw": lambda c, x, y, w, h: (
            cv2.rectangle(c, (x+5, y+5), (x+w-5, y+h-5), BLACK, -1),
            cv2.putText(c, "THE", (x + w//2 - 38, y + h//2 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2),
            cv2.putText(c, "ARCHITECTURE", (x + w//2 - 65, y + h//2 + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, WHITE, 1),
            cv2.putText(c, "HOLDS.", (x + w//2 - 40, y + h//2 + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2),
        ),
        "dialogue": "",
    },
]

PW, PH = 200, 240
M = 4
COLS = 4
ROWS = 2
CW = COLS * PW + (COLS + 1) * M
RH = ROWS * PH + (ROWS + 1) * M + 30
canvas = np.ones((RH, CW, 3), dtype=np.uint8) * 245

header_y = 20
cv2.putText(canvas, "MIDNIGHT RAGE  |  Vol 5  |  Chapter 3: THE RECLAMATION CODE",
            (M, header_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, DGRAY, 1)

for idx, panel in enumerate(panel_defs):
    col = idx % COLS
    row = idx // COLS
    px = M + col * (PW + M)
    py = M + row * (PH + M) + 30

    cv2.rectangle(canvas, (px, py), (px + PW, py + PH), DGRAY, 1, cv2.LINE_AA)

    label_x = px + 4
    label_y = py + 14
    cv2.putText(canvas, panel["title"], (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, DGRAY, 1)

    inner = canvas[py + 18:py + PH - 4, px + 4:px + PW - 4]
    ih, iw = inner.shape[:2]
    panel["draw"](canvas, px + 4, py + 18, PW - 8, PH - 22)

    if panel["dialogue"]:
        lines = panel["dialogue"].split("\n")
        tx = px + 8
        ty = py + PH - 8
        for li, line in enumerate(reversed(lines)):
            cv2.putText(canvas, line, (tx, ty - li * 12), cv2.FONT_HERSHEY_SIMPLEX, 0.3, DGRAY, 1)

out_path = out_dir / "midnight_rage_ch3_reclamation_code.png"
cv2.imwrite(str(out_path), canvas)
print("OK: %dx%d  %d bytes" % (canvas.shape[1], canvas.shape[0], out_path.stat().st_size))
