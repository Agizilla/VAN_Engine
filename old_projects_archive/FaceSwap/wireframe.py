from PIL import Image, ImageDraw

def create_transparent_wireframe(vector_dict, size=(1000, 1000), filename="harley_overlay.png"):
    # 1. Initialize 'RGBA' image with full transparency (0, 0, 0, 0)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    w, h = size

    # Helper to map normalized coordinates to pixel space
    to_px = lambda pt: (int(pt[0] * w), int(pt[1] * h))

    # Color configuration: [R, G, B, Alpha]
    # We use a bright neon red to contrast with the dark Harley aesthetic
    wire_color = (255, 0, 60, 255) 
    pupil_color = (0, 255, 255, 255) # Cyan pupils for focus tracking

    landmarks = vector_dict["landmarks"]

    # 2. Draw the Jawline
    jaw_pts = [to_px(p) for p in landmarks["jawline"]]
    draw.line(jaw_pts, fill=wire_color, width=4, joint="curve")

    # 3. Draw Brows (Left & Right)
    for side in ["left", "right"]:
        pts = [to_px(p) for p in landmarks["brows"][side]]
        draw.line(pts, fill=wire_color, width=3)

    # 4. Draw Ocular Geometry (Eyes)
    for side in ["left", "right"]:
        # Eye boundaries
        bounds = [to_px(p) for p in landmarks["eyes"][f"{side}_bounds"]]
        bounds.append(bounds[0]) # Close the loop
        draw.line(bounds, fill=wire_color, width=2)
        
        # Pupils
        pupil = to_px(landmarks["eyes"][f"{side}_pupil"])
        r = 5
        draw.ellipse([pupil[0]-r, pupil[1]-r, pupil[0]+r, pupil[1]+r], fill=pupil_color)

    # 5. Draw Nasal Structure
    bridge = [to_px(p) for p in landmarks["nose"]["bridge"]]
    draw.line(bridge, fill=wire_color, width=2)
    
    tip = to_px(landmarks["nose"]["tip"])
    nostrils = [to_px(p) for p in landmarks["nose"]["nostrils"]]
    draw.line([nostrils[0], tip, nostrils[1]], fill=wire_color, width=3)

    # 6. Draw Mouth (Upper & Lower Lips)
    corners = [to_px(p) for p in landmarks["mouth"]["outer_corners"]]
    peaks = [to_px(p) for p in landmarks["mouth"]["upper_lip_peaks"]]
    base = to_px(landmarks["mouth"]["lower_lip_base"])
    
    # Simple polyline mouth
    draw.line([corners[0], peaks[0], peaks[1], corners[1]], fill=wire_color, width=3)
    draw.line([corners[0], base, corners[1]], fill=wire_color, width=3)

    # 7. Save as PNG to preserve transparency
    img.save(filename, "PNG")
    print(f"Transparent overlay created: {filename}")

# Reuse your vector dictionary here
face_data = {
    "landmarks": {
        "jawline": [[0.18, 0.42], [0.20, 0.55], [0.25, 0.68], [0.32, 0.78], [0.40, 0.85], [0.50, 0.88], [0.60, 0.85], [0.68, 0.78], [0.75, 0.68], [0.80, 0.55], [0.82, 0.42]],
        "brows": {
            "left": [[0.28, 0.32], [0.32, 0.30], [0.38, 0.30], [0.44, 0.33]],
            "right": [[0.56, 0.33], [0.62, 0.30], [0.68, 0.30], [0.72, 0.32]]
        },
        "eyes": {
            "left_pupil": [0.345, 0.385],
            "left_bounds": [[0.29, 0.38], [0.34, 0.36], [0.40, 0.38], [0.34, 0.41]],
            "right_pupil": [0.655, 0.385],
            "right_bounds": [[0.60, 0.38], [0.65, 0.36], [0.71, 0.38], [0.65, 0.41]]
        },
        "nose": {
            "bridge": [[0.50, 0.35], [0.50, 0.48]],
            "tip": [0.50, 0.58],
            "nostrils": [[0.45, 0.58], [0.55, 0.58]]
        },
        "mouth": {
            "outer_corners": [[0.37, 0.72], [0.63, 0.72]],
            "upper_lip_peaks": [[0.465, 0.695], [0.535, 0.695]],
            "lower_lip_base": [0.50, 0.78]
        }
    }
}

if __name__ == "__main__":
    create_transparent_wireframe(face_data)