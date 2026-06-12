#!/usr/bin/env python3
"""
Image Background Remover & Figure Editor
- Remove humans from background
- Color smear strategy to fix background
- Resize and reposition extracted figures
- Body adjustments (thin, fat, tall, short)
- Pupil size adjustment
- Undo functionality
"""

import gradio as gr
import numpy as np
import cv2
import mediapipe as mp
from typing import Optional, List, Tuple
from PIL import Image

# MediaPipe Solutions
mp_face_mesh = mp.solutions.face_mesh
mp_selfie_segmentation = mp.solutions.selfie_segmentation
mp_pose = mp.solutions.pose

# Iris Landmark Indices
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]

class ImageEditorState:
    """Manages undo history and current state"""
    def __init__(self):
        self.history: List[np.ndarray] = []
        self.current_image: Optional[np.ndarray] = None
        self.extracted_figures: List[dict] = []
    
    def save_state(self, img):
        """Save current image to undo history"""
        if img is not None:
            self.history.append(img.copy())
            self.current_image = img.copy()
    
    def undo(self):
        """Revert to previous state"""
        if len(self.history) > 1:
            self.history.pop()
            self.current_image = self.history[-1].copy()
            return self.current_image
        return self.current_image
    
    def clear_history(self):
        """Clear undo history"""
        self.history = []
        self.extracted_figures = []

state = ImageEditorState()

class HumanRemover:
    """Detect and remove humans from background"""
    def __init__(self):
        self.segmenter = mp_selfie_segmentation.SelfieSegmentation(model_selection=1)
    
    def detect_and_remove(self, img) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Detect humans and return:
        - Background only (humans removed)
        - Segmentation mask
        - Extracted figures
        """
        if img is None:
            return img, None, None
        
        h, w = img.shape[:2]
        results = self.segmenter.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        mask = results.segmentation_mask
        
        # Binary mask: 1 = person, 0 = background
        person_mask = (mask > 0.5).astype(np.uint8) * 255
        bg_mask = cv2.bitwise_not(person_mask)
        
        # Extract background
        bg_only = cv2.bitwise_and(img, img, mask=bg_mask)
        
        # Extract figures (person only)
        figures = cv2.bitwise_and(img, img, mask=person_mask)
        
        return bg_only, person_mask, figures
    
    def fix_background_smear(self, bg_img, person_mask) -> np.ndarray:
        """
        Fix background by color smearing:
        - Left to right: smear colors horizontally
        - Top to bottom: smear colors vertically
        """
        canvas = bg_img.copy()
        h, w = canvas.shape[:2]
        
        # Find background areas that need fixing
        holes = cv2.bitwise_not(cv2.dilate(cv2.bitwise_not(person_mask), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), iterations=2))
        
        # Horizontal smear (left to right)
        for y in range(h):
            row = canvas[y, :].copy()
            for x in range(w):
                if holes[y, x] > 0:  # This pixel needs fixing
                    # Find nearest non-hole pixel to the left
                    left_x = x - 1
                    while left_x >= 0 and holes[y, left_x] > 0:
                        left_x -= 1
                    
                    if left_x >= 0:
                        # Smear with slight increment
                        color = row[left_x].astype(np.float32)
                        dist = x - left_x
                        # Gradually increment color
                        increment = (255 - color) * 0.01 * dist
                        canvas[y, x] = np.clip(color + increment, 0, 255).astype(np.uint8)
        
        # Vertical smear (top to bottom)
        for x in range(w):
            col = canvas[:, x].copy()
            for y in range(h):
                if holes[y, x] > 0:
                    # Find nearest non-hole pixel above
                    top_y = y - 1
                    while top_y >= 0 and holes[top_y, x] > 0:
                        top_y -= 1
                    
                    if top_y >= 0:
                        color = col[top_y].astype(np.float32)
                        dist = y - top_y
                        increment = (255 - color) * 0.01 * dist
                        canvas[y, x] = np.clip(color + increment, 0, 255).astype(np.uint8)
        
        return canvas

class EyeOrchestrator:
    """Pupil size adjustment"""
    def __init__(self):
        self.face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True
        )
    
    def scale_pupils(self, img, factor):
        """Scale pupils by factor (1.3 = bigger, 0.7 = smaller)"""
        if img is None:
            return img
        
        results = self.face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            return img
        
        h, w = img.shape[:2]
        canvas = img.copy()
        landmarks = results.multi_face_landmarks[0].landmark
        
        def get_iris_data(indices):
            pts = np.array([(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in indices])
            center = np.mean(pts, axis=0).astype(int)
            radius = int(np.linalg.norm(pts[0] - center))
            return center, radius
        
        for indices in [LEFT_IRIS, RIGHT_IRIS]:
            center, r = get_iris_data(indices)
            
            roi_size = int(r * 2.5)
            y1, y2 = max(0, center[1]-roi_size), min(h, center[1]+roi_size)
            x1, x2 = max(0, center[0]-roi_size), min(w, center[0]+roi_size)
            
            eye_roi = img[y1:y2, x1:x2]
            if eye_roi.size == 0:
                continue
            
            new_dim = (int(eye_roi.shape[1] * factor), int(eye_roi.shape[0] * factor))
            resized_eye = cv2.resize(eye_roi, new_dim, interpolation=cv2.INTER_CUBIC)
            
            nw, nh = resized_eye.shape[1], resized_eye.shape[0]
            nx1, ny1 = center[0] - nw//2, center[1] - nh//2
            nx2, ny2 = nx1 + nw, ny1 + nh
            
            if nx1 >= 0 and ny1 >= 0 and nx2 < w and ny2 < h:
                mask = np.zeros((nh, nw), dtype=np.uint8)
                cv2.circle(mask, (nw//2, nh//2), int(r * factor), 255, -1)
                mask_inv = cv2.bitwise_not(mask)
                
                bg_area = canvas[ny1:ny2, nx1:nx2]
                fg_part = cv2.bitwise_and(resized_eye, resized_eye, mask=mask)
                bg_part = cv2.bitwise_and(bg_area, bg_area, mask=mask_inv)
                
                canvas[ny1:ny2, nx1:nx2] = cv2.add(fg_part, bg_part)
        
        return canvas

class BodyModifier:
    """Modify body shape (thin, fat, tall, short)"""
    def __init__(self):
        self.pose_detector = mp_pose.Pose(static_image_mode=True)
    
    def make_thinner(self, img) -> np.ndarray:
        """Make person thinner by scaling horizontally"""
        return self._scale_body(img, scale_x=0.85, scale_y=1.0)
    
    def make_fatter(self, img) -> np.ndarray:
        """Make person fatter by scaling horizontally"""
        return self._scale_body(img, scale_x=1.15, scale_y=1.0)
    
    def make_taller(self, img) -> np.ndarray:
        """Make person taller by scaling vertically"""
        return self._scale_body(img, scale_x=1.0, scale_y=1.15)
    
    def make_shorter(self, img) -> np.ndarray:
        """Make person shorter by scaling vertically"""
        return self._scale_body(img, scale_x=1.0, scale_y=0.85)
    
    def _scale_body(self, img, scale_x: float, scale_y: float) -> np.ndarray:
        """
        Scale body while keeping face stationary.
        Uses pose detection to identify body bounds.
        """
        if img is None:
            return img
        
        results = self.pose_detector.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not results.pose_landmarks:
            return img
        
        h, w = img.shape[:2]
        canvas = img.copy()
        landmarks = results.pose_landmarks.landmark
        
        # Get head position (nose, eyes)
        head_y = int(landmarks[0].y * h)  # Nose
        
        # Get body bounds (from shoulders down)
        shoulders_y = int(min(landmarks[11].y, landmarks[12].y) * h)
        hips_y = int(max(landmarks[23].y, landmarks[24].y) * h)
        
        # Get width from shoulders
        left_shoulder_x = int(landmarks[11].x * w)
        right_shoulder_x = int(landmarks[12].x * w)
        shoulder_width = right_shoulder_x - left_shoulder_x
        
        # Extract body region (below head, above/including hips)
        if shoulders_y < hips_y and shoulder_width > 0:
            body_region = img[shoulders_y:hips_y, max(0, left_shoulder_x-shoulder_width//2):min(w, right_shoulder_x+shoulder_width//2)]
            
            if body_region.size > 0:
                # Resize body
                new_h = int((hips_y - shoulders_y) * scale_y)
                new_w = int(body_region.shape[1] * scale_x)
                resized_body = cv2.resize(body_region, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                
                # Place back
                center_x = (left_shoulder_x + right_shoulder_x) // 2
                paste_x1 = max(0, center_x - new_w // 2)
                paste_x2 = min(w, paste_x1 + new_w)
                paste_y1 = shoulders_y
                paste_y2 = min(h, paste_y1 + new_h)
                
                canvas[paste_y1:paste_y2, paste_x1:paste_x2] = resized_body[:paste_y2-paste_y1, :paste_x2-paste_x1]
        
        return canvas

# Initialize tools
remover = HumanRemover()
eye_tool = EyeOrchestrator()
body_modifier = BodyModifier()

# ============ GRADIO UI ============

with gr.Blocks(title="Image Background Remover & Figure Editor", theme=gr.themes.Soft()) as demo:
    
    gr.Markdown("# 🎨 Image Background Remover & Figure Editor")
    
    with gr.Row():
        # LEFT: Input
        with gr.Column(scale=1):
            gr.Markdown("### 📥 Original Image")
            input_img = gr.Image(label="Upload Image", type="numpy")
            upload_btn = gr.Button("🔄 Load Image", variant="primary")
        
        # CENTER: Display & Controls
        with gr.Column(scale=2):
            gr.Markdown("### 🎯 Editor Controls")
            
            with gr.Row():
                with gr.Column():
                    remove_bg_btn = gr.Button("👤 Remove Humans", variant="primary", size="lg")
                    fix_bg_btn = gr.Button("🎨 Fix Background", variant="primary")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### 👗 Body Adjustments")
                    make_thin = gr.Button("🤏 Make Thinner")
                    make_fat = gr.Button("🤲 Make Fatter")
                with gr.Column():
                    gr.Markdown("#### 📏 Height")
                    make_tall = gr.Button("📈 Make Taller")
                    make_short = gr.Button("📉 Make Shorter")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### 👁️ Pupil Adjustments")
                    big_pupils = gr.Button("👀 Bigger Pupils")
                    small_pupils = gr.Button("🕶️ Smaller Pupils")
                with gr.Column():
                    gr.Markdown("#### ↩️ History")
                    undo_btn = gr.Button("↩️ Undo")
                    clear_btn = gr.Button("🗑️ Clear")
            
            display_img = gr.Image(label="Working Image", type="numpy")
            status = gr.Textbox(label="Status", interactive=False, value="Ready")
        
        # RIGHT: Cast (extracted figures)
        with gr.Column(scale=1):
            gr.Markdown("### 👥 Extracted Figures")
            cast_display = gr.Image(label="Figures Panel", type="numpy")
            
            gr.Markdown("#### 🎬 Cast Actions")
            resize_slider = gr.Slider(label="Figure Scale", minimum=0.5, maximum=2.0, value=1.0, step=0.1)
            apply_scale = gr.Button("📐 Apply Scale")
            
            figure_selector = gr.Dropdown(label="Select Figure", choices=[], interactive=True)
    
    # ============ EVENT HANDLERS ============
    
    def load_image(img):
        """Load and display image"""
        if img is None:
            return None, None, None, "❌ No image loaded"
        state.save_state(img)
        return img, img, None, "✅ Image loaded"
    
    def remove_humans(img):
        """Remove humans and show background + figures"""
        if img is None:
            return None, None, None, "❌ No image loaded"
        
        bg, mask, figures = remover.detect_and_remove(img)
        state.save_state(bg)
        state.extracted_figures = [{"mask": mask, "figures": figures, "original": img}]
        
        return bg, figures, None, f"✅ Removed humans. Found {len(state.extracted_figures)} figure(s)"
    
    def fix_background_color(img):
        """Fix background with color smear"""
        if img is None or not state.extracted_figures:
            return None, None, "❌ Remove humans first"
        
        bg, mask, _ = remover.detect_and_remove(state.extracted_figures[0]["original"])
        fixed_bg = remover.fix_background_smear(bg, mask)
        state.save_state(fixed_bg)
        
        return fixed_bg, None, "✅ Background fixed with color smear"
    
    def make_person_thinner(img):
        """Make body thinner"""
        if img is None:
            return None, None, "❌ No image"
        result = body_modifier.make_thinner(img)
        state.save_state(result)
        return result, None, "✅ Person made thinner"
    
    def make_person_fatter(img):
        """Make body fatter"""
        if img is None:
            return None, None, "❌ No image"
        result = body_modifier.make_fatter(img)
        state.save_state(result)
        return result, None, "✅ Person made fatter"
    
    def make_person_taller(img):
        """Make person taller"""
        if img is None:
            return None, None, "❌ No image"
        result = body_modifier.make_taller(img)
        state.save_state(result)
        return result, None, "✅ Person made taller"
    
    def make_person_shorter(img):
        """Make person shorter"""
        if img is None:
            return None, None, "❌ No image"
        result = body_modifier.make_shorter(img)
        state.save_state(result)
        return result, None, "✅ Person made shorter"
    
    def bigger_pupils(img):
        """Enlarge pupils"""
        if img is None:
            return None, None, "❌ No image"
        result = eye_tool.scale_pupils(img, 1.3)
        state.save_state(result)
        return result, None, "✅ Pupils enlarged"
    
    def smaller_pupils(img):
        """Shrink pupils"""
        if img is None:
            return None, None, "❌ No image"
        result = eye_tool.scale_pupils(img, 0.7)
        state.save_state(result)
        return result, None, "✅ Pupils shrunk"
    
    def undo_last():
        """Undo last action"""
        result = state.undo()
        if result is not None:
            return result, None, "✅ Undo successful"
        return None, None, "⚠️ Nothing to undo"
    
    def clear_all():
        """Clear everything"""
        state.clear_history()
        return None, None, None, "🗑️ Cleared"
    
    # ============ BIND EVENTS ============
    
    upload_btn.click(load_image, inputs=[input_img], outputs=[display_img, cast_display, figure_selector, status])
    remove_bg_btn.click(remove_humans, inputs=[display_img], outputs=[display_img, cast_display, figure_selector, status])
    fix_bg_btn.click(fix_background_color, inputs=[display_img], outputs=[display_img, cast_display, status])
    
    make_thin.click(make_person_thinner, inputs=[display_img], outputs=[display_img, cast_display, status])
    make_fat.click(make_person_fatter, inputs=[display_img], outputs=[display_img, cast_display, status])
    make_tall.click(make_person_taller, inputs=[display_img], outputs=[display_img, cast_display, status])
    make_short.click(make_person_shorter, inputs=[display_img], outputs=[display_img, cast_display, status])
    
    big_pupils.click(bigger_pupils, inputs=[display_img], outputs=[display_img, cast_display, status])
    small_pupils.click(smaller_pupils, inputs=[display_img], outputs=[display_img, cast_display, status])
    
    undo_btn.click(undo_last, inputs=[], outputs=[display_img, cast_display, status])
    clear_btn.click(clear_all, inputs=[], outputs=[input_img, display_img, cast_display, status])

if __name__ == "__main__":
    demo.launch(server_port=7860)
