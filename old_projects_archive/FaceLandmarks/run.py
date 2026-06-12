import os
import json
import numpy as np
import cv2
from pathlib import Path

def load_landmark_file():
    # Scan root for JSON files
    root_path = Path('.')
    json_files = list(root_path.glob('*.json'))
    
    # Filter for files that actually contain landmark data
    valid_files = []
    for f in json_files:
        try:
            with open(f, 'r') as j:
                content = json.load(j)
                if "landmarks" in content:
                    valid_files.append((f.name, content))
        except Exception:
            continue

    if not valid_files:
        print("No valid L-68 landmark files found in root.")
        return None

    # Logic for file selection
    if len(valid_files) > 1:
        print("\n--- Multiple Landmark Files Found ---")
        for i, (name, _) in enumerate(valid_files):
            print(f"[{i}] {name}")
        
        choice = int(input(f"\nSelect a file index (0-{len(valid_files)-1}): "))
        return valid_files[choice][1]
    
    print(f"Loading single file found: {valid_files[0][0]}")
    return valid_files[0][1]

def render_scaffold(data, width=800):
    # Calculate height based on metadata aspect ratio (default 4:5)
    aspect_raw = data.get("metadata", {}).get("aspect_ratio", "4:5")
    w_ratio, h_ratio = map(int, aspect_raw.split(':'))
    height = int((width / w_ratio) * h_ratio)
    
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Recursively extract coordinates
    def get_points(d):
        pts = []
        if isinstance(d, list):
            if len(d) > 0 and isinstance(d[0], (int, float)):
                pts.append((int(d[0] * width), int(d[1] * height)))
            else:
                for item in d: pts.extend(get_points(item))
        elif isinstance(d, dict):
            for v in d.values(): pts.extend(get_points(v))
        return pts

    points = get_points(data['landmarks'])

    # Draw landmarks with identity metadata
    for (x, y) in points:
        cv2.circle(canvas, (x, y), 2, (0, 255, 0), -1)
    
    identity = data.get("identity", "Unknown Subject")
    cv2.putText(canvas, identity, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    
    cv2.imshow(f"Reconstructed Scaffold: {identity}", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    face_data = load_landmark_file()
    if face_data:
        render_scaffold(face_data)