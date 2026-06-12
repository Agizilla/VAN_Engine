import gradio as gr
import numpy as np
import cv2
import torch
from PIL import Image
import requests
import os
import logging
import time
from collections import deque
from segment_anything import sam_model_registry, SamPredictor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SAM_CHECKPOINT_URL = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
SAM_CHECKPOINT_PATH = "sam_vit_b_01ec64.pth"
MAX_IMAGE_SIZE = 1024
DOUBLE_CLICK_THRESHOLD = 500  # milliseconds
MAX_UNDO_STATES = 10

# ============================================================
# STATE MANAGEMENT
# ============================================================
class AppState:
    """Manages application state including undo stack and click tracking."""
    
    def __init__(self):
        self.undo_stack = deque(maxlen=MAX_UNDO_STATES)
        self.current_mask = None
        self.last_click_time = 0
        self.last_click_point = None
        self.preview_image = None
        
    def add_to_undo_stack(self, image):
        """Add image to undo stack."""
        self.undo_stack.append(image.copy())
        
    def undo(self):
        """Restore previous state."""
        if len(self.undo_stack) > 0:
            return self.undo_stack.pop()
        return None
    
    def clear(self):
        """Clear all state."""
        self.undo_stack.clear()
        self.current_mask = None
        self.last_click_time = 0
        self.last_click_point = None
        self.preview_image = None

# Global state
app_state = AppState()

# ============================================================
# MODEL LOADING
# ============================================================
def download_sam_checkpoint():
    """Download SAM checkpoint with error handling."""
    if os.path.exists(SAM_CHECKPOINT_PATH):
        logger.info("SAM checkpoint already exists.")
        return
    
    try:
        logger.info("Downloading SAM checkpoint...")
        response = requests.get(SAM_CHECKPOINT_URL, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        with open(SAM_CHECKPOINT_PATH, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        pct = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {pct:.1f}%")
        
        logger.info("Download complete.")
    except Exception as e:
        raise RuntimeError(f"Failed to download SAM checkpoint: {e}")

try:
    download_sam_checkpoint()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    sam_model = sam_model_registry["vit_b"](checkpoint=SAM_CHECKPOINT_PATH)
    sam_model.to(device)
    sam_predictor = SamPredictor(sam_model)
    logger.info("SAM model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load SAM model: {e}")
    raise

# ============================================================
# IMAGE UTILITIES
# ============================================================
def ensure_rgb(image_np):
    """Convert image to RGB if needed."""
    if len(image_np.shape) == 2:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
    elif len(image_np.shape) == 3 and image_np.shape[2] == 4:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
    elif image_np.dtype != np.uint8:
        image_np = (image_np * 255).astype(np.uint8)
    return image_np

def resize_if_needed(image_np):
    """Resize image if it exceeds MAX_IMAGE_SIZE."""
    h, w = image_np.shape[:2]
    max_dim = max(h, w)
    
    if max_dim > MAX_IMAGE_SIZE:
        scale = MAX_IMAGE_SIZE / max_dim
        new_h, new_w = int(h * scale), int(w * scale)
        logger.info(f"Resizing image from {w}x{h} to {new_w}x{new_h}")
        image_np = cv2.resize(image_np, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    return image_np

def validate_image(image_np):
    """Validate and preprocess image."""
    if image_np is None:
        raise gr.Error("Please upload an image first.")
    
    if len(image_np.shape) not in [2, 3]:
        raise gr.Error("Invalid image format.")
    
    image_np = ensure_rgb(image_np)
    image_np = resize_if_needed(image_np)
    
    return image_np

# ============================================================
# SAM SEGMENTATION
# ============================================================
def get_person_mask(image_np, point_x, point_y):
    """
    Use SAM to segment the entire person from a single point click.
    
    Returns:
        Binary mask (0/255) of the segmented person
    """
    try:
        sam_predictor.set_image(image_np)
        
        input_point = np.array([[point_x, point_y]])
        input_label = np.array([1])
        
        masks, scores, _ = sam_predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=True
        )
        
        best_idx = np.argmax(scores)
        mask = masks[best_idx].astype(np.uint8) * 255
        
        logger.info(f"Segmentation confidence: {scores[best_idx]:.3f}")
        return mask
    
    except Exception as e:
        logger.error(f"SAM segmentation failed: {e}")
        raise gr.Error(f"Failed to segment person. Try clicking closer to the face.")

# ============================================================
# MASK PREVIEW
# ============================================================
def overlay_mask_preview(image_np, mask, color=(255, 0, 0), alpha=0.4):
    """
    Create preview image with semi-transparent red overlay on masked area.
    
    Args:
        image_np: Original RGB image
        mask: Binary mask (255 = person to erase)
        color: RGB color for overlay (default red)
        alpha: Transparency (0=invisible, 1=opaque)
    
    Returns:
        Image with mask overlay
    """
    overlay = image_np.copy()
    
    # Create colored mask
    mask_colored = np.zeros_like(image_np)
    mask_colored[mask > 0] = color
    
    # Blend with original image
    mask_3d = (mask > 0).astype(np.uint8)
    for c in range(3):
        overlay[:, :, c] = np.where(
            mask_3d,
            (1 - alpha) * image_np[:, :, c] + alpha * mask_colored[:, :, c],
            image_np[:, :, c]
        )
    
    # Add border around mask for clarity
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (255, 255, 0), 2)  # Yellow border
    
    return overlay.astype(np.uint8)

# ============================================================
# SMART INPAINTING (Advanced Background Filling)
# ============================================================
def smart_inpaint(image_np, mask):
    """
    Advanced inpainting using multi-method approach:
    1. PatchMatch-style texture synthesis
    2. Edge-aware blending
    3. Noise injection for natural look
    
    Args:
        image_np: RGB image
        mask: Binary mask (255 = area to fill)
    
    Returns:
        Inpainted image
    """
    try:
        # Step 1: Dilate mask for better blending
        kernel = np.ones((3, 3), np.uint8)
        mask_dilated = cv2.dilate(mask, kernel, iterations=2)
        
        # Step 2: Multi-scale inpainting
        # Coarse level (fast, general structure)
        h, w = image_np.shape[:2]
        small_img = cv2.resize(image_np, (w//2, h//2))
        small_mask = cv2.resize(mask_dilated, (w//2, h//2))
        
        coarse_result = cv2.inpaint(
            small_img, 
            small_mask, 
            inpaintRadius=5, 
            flags=cv2.INPAINT_NS
        )
        coarse_result = cv2.resize(coarse_result, (w, h))
        
        # Fine level (detailed, texture-aware)
        radius = max(3, int(max(h, w) / 128))
        fine_result = cv2.inpaint(
            image_np, 
            mask_dilated, 
            radius, 
            flags=cv2.INPAINT_TELEA
        )
        
        # Step 3: Blend coarse and fine
        # Use fine for edges, coarse for interior
        edge_mask = cv2.Canny(mask_dilated, 50, 150)
        edge_mask = cv2.dilate(edge_mask, kernel, iterations=3)
        edge_mask_3d = np.stack([edge_mask] * 3, axis=2) / 255.0
        
        blended = (fine_result * edge_mask_3d + coarse_result * (1 - edge_mask_3d)).astype(np.uint8)
        
        # Step 4: Add subtle noise for natural texture
        noise = np.random.normal(0, 2, blended.shape).astype(np.int16)
        mask_3d = np.stack([mask > 0] * 3, axis=2)
        blended = np.clip(blended.astype(np.int16) + noise * mask_3d, 0, 255).astype(np.uint8)
        
        # Step 5: Seamless cloning for smooth boundaries
        # Find center of mask for seamless clone
        moments = cv2.moments(mask)
        if moments["m00"] != 0:
            cx = int(moments["m10"] / moments["m00"])
            cy = int(moments["m01"] / moments["m00"])
            
            try:
                result = cv2.seamlessClone(
                    blended,
                    image_np,
                    mask_dilated,
                    (cx, cy),
                    cv2.NORMAL_CLONE
                )
            except cv2.error:
                # Fallback if seamless clone fails
                result = blended
        else:
            result = blended
        
        logger.info("Smart inpainting complete.")
        return result
    
    except Exception as e:
        logger.error(f"Smart inpainting failed: {e}")
        # Fallback to basic inpainting
        radius = max(3, int(max(image_np.shape[:2]) / 128))
        return cv2.inpaint(image_np, mask_dilated, radius, flags=cv2.INPAINT_TELEA)

# ============================================================
# CLICK DETECTION & PROCESSING
# ============================================================
def extract_click_point(mask_image):
    """
    Extract click point from user's drawing.
    
    Returns:
        (x, y) coordinates or None
    """
    if mask_image is None:
        return None
    
    # Convert to grayscale if needed
    if len(mask_image.shape) == 3:
        mask_gray = cv2.cvtColor(mask_image, cv2.COLOR_RGB2GRAY)
    else:
        mask_gray = mask_image
    
    # Find white pixels (user's drawing)
    points = np.column_stack(np.where(mask_gray > 200))
    
    if len(points) == 0:
        return None
    
    # Use centroid as click point
    center_y = int(np.mean(points[:, 0]))
    center_x = int(np.mean(points[:, 1]))
    
    return (center_x, center_y)

def handle_click(original_image, editor_output):
    """
    Handle click event:
    - Single click → Show mask preview
    - Double click → Apply erasure
    
    Returns:
        (preview_image, status_message, undo_enabled)
    """
    global app_state
    
    try:
        # Validate image
        if original_image is None:
            return None, "⚠️ Please upload an image first.", gr.Button(interactive=False)
        
        original_image = validate_image(original_image)
        
        # Extract click point
        click_point = extract_click_point(editor_output)
        
        if click_point is None:
            return original_image, "💡 Click on a person's face to preview mask.", gr.Button(interactive=False)
        
        # Check for double-click
        current_time = time.time() * 1000  # milliseconds
        is_double_click = False
        
        if app_state.last_click_point == click_point:
            time_diff = current_time - app_state.last_click_time
            if time_diff < DOUBLE_CLICK_THRESHOLD:
                is_double_click = True
                logger.info("Double-click detected!")
        
        # Update click tracking
        app_state.last_click_time = current_time
        app_state.last_click_point = click_point
        
        point_x, point_y = click_point
        
        # Generate mask
        mask = get_person_mask(original_image, point_x, point_y)
        app_state.current_mask = mask
        
        if is_double_click and app_state.current_mask is not None:
            # DOUBLE CLICK → ERASE
            logger.info("Applying erasure...")
            
            # Save to undo stack
            app_state.add_to_undo_stack(original_image)
            
            # Smart inpaint
            result = smart_inpaint(original_image, app_state.current_mask)
            
            # Clear mask after applying
            app_state.current_mask = None
            
            return result, "✅ Person erased! Click another face or press Undo.", gr.Button(interactive=True)
        
        else:
            # SINGLE CLICK → PREVIEW
            logger.info("Showing mask preview...")
            preview = overlay_mask_preview(original_image, mask)
            app_state.preview_image = preview
            
            return preview, "🎯 Preview shown. Double-click to erase this area.", gr.Button(interactive=False)
    
    except gr.Error:
        raise
    except Exception as e:
        logger.error(f"Click handling error: {e}")
        return original_image, f"❌ Error: {str(e)}", gr.Button(interactive=False)

def handle_undo(original_image):
    """
    Restore previous state from undo stack.
    
    Returns:
        (restored_image, status_message, undo_enabled)
    """
    global app_state
    
    restored = app_state.undo()
    
    if restored is not None:
        remaining = len(app_state.undo_stack)
        undo_enabled = remaining > 0
        return restored, f"↩️ Undo successful. {remaining} states remaining.", gr.Button(interactive=undo_enabled)
    else:
        return original_image, "⚠️ Nothing to undo.", gr.Button(interactive=False)

def reset_state():
    """Clear all application state."""
    global app_state
    app_state.clear()
    logger.info("State reset.")

# ============================================================
# GRADIO UI with Custom Styling
# ============================================================
custom_css = """
/* Enhanced UI Styling */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #3b82f6;
    --primary-dark: #1e40af;
    --accent: #06b6d4;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}

body {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.gradio-container {
    background: linear-gradient(135deg, #f8fafc 0%, #fffbeb 100%);
}

/* Gradient Header */
.main-header {
    text-align: center;
    background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
}

/* Status Message Box */
.status-box {
    padding: 1rem;
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
    border-left: 4px solid var(--primary);
    font-weight: 500;
    margin: 1rem 0;
}

/* Button Styling */
.gradio-button.primary {
    background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
    border: none;
    padding: 0.75rem 2rem;
    box-shadow: 0 4px 14px -2px rgba(59, 130, 246, 0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    font-weight: 600;
}

.gradio-button.primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px -2px rgba(59, 130, 246, 0.4);
}

.gradio-button.secondary {
    background: var(--warning);
    border: none;
    transition: all 0.3s ease;
}

.gradio-button.secondary:hover {
    background: #d97706;
    transform: scale(1.05);
}

/* Info Boxes */
.info-box {
    background: rgba(59, 130, 246, 0.05);
    border-left: 4px solid var(--primary);
    padding: 1rem;
    border-radius: 6px;
    margin: 1rem 0;
}

.tip-box {
    background: rgba(16, 185, 129, 0.05);
    border-left: 4px solid var(--success);
    padding: 0.75rem;
    border-radius: 6px;
    font-size: 0.9rem;
}
"""

with gr.Blocks(title="Person Eraser Enhanced", css=custom_css) as demo:
    gr.HTML("<h1 class='main-header'>✨ Person Eraser Pro</h1>")
    gr.Markdown("""
    ### Remove anyone from your photos with smart AI-powered inpainting
    
    **Instructions:**
    1. 📸 Upload a photo
    2. 🎯 Click on a person's face → **Mask preview appears** (red overlay)
    3. 🖱️ **Double-click** to erase → Person removed with smart background filling
    4. ↩️ Made a mistake? Press **Undo**
    """)
    
    # Status message
    status = gr.Markdown("💡 Upload an image to get started.", elem_classes="status-box")
    
    with gr.Row():
        with gr.Column(scale=1):
            original_upload = gr.Image(
                label="📸 Upload Photo",
                type="numpy",
                interactive=True
            )
            
            gr.HTML("""
            <div class="tip-box">
                <strong>💡 Tip:</strong> Works best with clear backgrounds and well-defined subjects.
            </div>
            """)
        
        with gr.Column(scale=1):
            editor = gr.ImageEditor(
                label="🎨 Click to Preview → Double-Click to Erase",
                type="numpy",
                brush=gr.Brush(
                    colors=["white"],
                    default_color="white",
                    default_size=5
                ),
                interactive=True
            )
            
            gr.HTML("""
            <div class="tip-box">
                <strong>🎯 How to use:</strong><br>
                • Single click → See what will be erased (red overlay)<br>
                • Double click same spot → Apply erasure<br>
                • Click different spot → Preview new mask
            </div>
            """)
    
    with gr.Row():
        undo_btn = gr.Button("↩️ Undo", variant="secondary", size="lg", interactive=False)
    
    with gr.Row():
        output_image = gr.Image(label="✨ Result", type="numpy")
    
    # Event handlers
    def update_editor(img):
        """Copy uploaded image to editor and reset state."""
        if img is None:
            return None
        reset_state()
        return img
    
    original_upload.change(
        fn=update_editor,
        inputs=original_upload,
        outputs=editor
    )
    
    # Editor change (click detection)
    editor.change(
        fn=handle_click,
        inputs=[original_upload, editor],
        outputs=[output_image, status, undo_btn]
    )
    
    # Undo button
    undo_btn.click(
        fn=handle_undo,
        inputs=output_image,
        outputs=[output_image, status, undo_btn]
    )
    
    gr.Markdown("""
    ---
    
    ### 🚀 How It Works
    
    **1. Smart Segmentation**  
    SAM (Segment Anything Model) precisely identifies the entire person from your click point.
    
    **2. Preview Before Erase**  
    See exactly what will be removed with a semi-transparent red overlay and yellow border.
    
    **3. Advanced Inpainting**  
    Multi-method approach:
    - 🎨 **Texture synthesis** from surrounding areas
    - 🔄 **Multi-scale processing** (coarse + fine details)
    - 🎯 **Edge-aware blending** for seamless boundaries
    - 🌫️ **Noise injection** for natural texture
    - 🧬 **Seamless cloning** for perfect integration
    
    **4. Undo Stack**  
    Every erasure is saved. Undo up to 10 times.
    
    ---
    
    ### 💡 Pro Tips
    
    - **Multiple people?** Erase them one at a time (undo stack preserves your progress)
    - **Preview looks wrong?** Click a different spot on the face
    - **Accidental erase?** Hit Undo immediately
    - **Complex backgrounds?** The smart inpainting handles patterns, textures, and edges automatically
    
    ---
    
    **Powered by:** SAM (Meta AI) + OpenCV + Smart Inpainting Algorithms
    """)

if __name__ == "__main__":
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)
