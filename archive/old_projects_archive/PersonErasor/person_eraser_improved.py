import gradio as gr
import numpy as np
import cv2
import torch
from PIL import Image
import requests
import os
import logging
from segment_anything import sam_model_registry, SamPredictor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SAM_CHECKPOINT_URL = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
SAM_CHECKPOINT_PATH = "sam_vit_b_01ec64.pth"
MAX_IMAGE_SIZE = 1024  # Pixels on longest side
INPAINT_RADIUS_SCALE = 128  # Adaptive radius: img_size / this value

# ============================================================
# 1. Load SAM model (cached) with error handling
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
# 2. Image validation and preprocessing
# ============================================================
def ensure_rgb(image_np):
    """Convert image to RGB if needed."""
    if len(image_np.shape) == 2:  # Grayscale
        image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
    elif len(image_np.shape) == 3 and image_np.shape[2] == 4:  # RGBA
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
# 3. SAM segmentation
# ============================================================
def get_person_mask(image_np, point_x, point_y):
    """
    Use SAM to segment the entire person from a single point click.
    
    Args:
        image_np: RGB numpy array (H, W, 3)
        point_x, point_y: Click coordinates in pixels
    
    Returns:
        Binary mask (0/255) of the segmented person
    """
    try:
        # Set image for SAM
        sam_predictor.set_image(image_np)
        
        # Prepare input point
        input_point = np.array([[point_x, point_y]])
        input_label = np.array([1])  # 1 = foreground
        
        # Get segmentation masks
        masks, scores, _ = sam_predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=True
        )
        
        # Use the highest confidence mask
        best_idx = np.argmax(scores)
        mask = masks[best_idx].astype(np.uint8) * 255
        
        logger.info(f"Segmentation confidence: {scores[best_idx]:.3f}")
        return mask
    
    except Exception as e:
        logger.error(f"SAM segmentation failed: {e}")
        raise gr.Error(f"Failed to segment person. Try clicking closer to the face.")

# ============================================================
# 4. Inpainting
# ============================================================
def inpaint_background(image_np, mask):
    """
    Remove the masked area and inpaint the background.
    
    Args:
        image_np: RGB image numpy array
        mask: Binary mask (255 = area to remove)
    
    Returns:
        Inpainted image with same shape as input
    """
    try:
        # Dilate mask slightly for better blending
        kernel = np.ones((3, 3), np.uint8)
        mask_dilated = cv2.dilate(mask, kernel, iterations=2)
        
        # Adaptive inpaint radius based on image size
        max_dim = max(image_np.shape[:2])
        inpaint_radius = max(3, int(max_dim / INPAINT_RADIUS_SCALE))
        
        logger.info(f"Inpainting with radius: {inpaint_radius}")
        result = cv2.inpaint(image_np, mask_dilated, inpaint_radius, flags=cv2.INPAINT_TELEA)
        
        return result
    
    except Exception as e:
        logger.error(f"Inpainting failed: {e}")
        raise gr.Error(f"Inpainting failed: {str(e)}")

# ============================================================
# 5. Main processing function
# ============================================================
def erase_person(original_image, mask_image):
    """
    Main function: detect person from click point and remove them.
    
    Args:
        original_image: Uploaded RGB image
        mask_image: Image with user's drawing (white dot on black)
    
    Returns:
        Inpainted image with person removed
    """
    try:
        # Validate inputs
        original_image = validate_image(original_image)
        
        if mask_image is None:
            raise gr.Error("Please draw a dot on the person's face.")
        
        # Convert mask to grayscale if needed
        if len(mask_image.shape) == 3:
            mask_gray = cv2.cvtColor(mask_image, cv2.COLOR_RGB2GRAY)
        else:
            mask_gray = mask_image
        
        # Find user's drawing (white pixels)
        points = np.column_stack(np.where(mask_gray > 200))
        
        if len(points) == 0:
            raise gr.Error("No drawing detected. Please draw a small dot on the person's face.")
        
        # Use centroid of drawing as click point
        center_y = int(np.mean(points[:, 0]))
        center_x = int(np.mean(points[:, 1]))
        
        logger.info(f"Click point: ({center_x}, {center_y})")
        
        # Segment person using SAM
        person_mask = get_person_mask(original_image, center_x, center_y)
        
        # Inpaint background
        result = inpaint_background(original_image, person_mask)
        
        logger.info("Person erased successfully.")
        return result
    
    except gr.Error:
        raise  # Re-raise Gradio errors
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise gr.Error(f"An unexpected error occurred: {str(e)}")

# ============================================================
# 6. Gradio UI
# ============================================================
with gr.Blocks(title="Person Eraser", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🧑‍🦱 Remove Person from Photo
    
    **How to use:**
    1. **Upload** a photo with a person
    2. **Click once** on the person's face (in the editor on the right)
    3. **Press Erase** – the entire person will be removed and background filled
    
    Works best with clear backgrounds and single subjects.
    """)
    
    with gr.Row():
        with gr.Column():
            original_upload = gr.Image(
                label="📸 Step 1: Upload Photo", 
                type="numpy", 
                interactive=True
            )
        
        with gr.Column():
            editor = gr.ImageEditor(
                label="✍️ Step 2: Click on the person's face", 
                type="numpy",
                brush=gr.Brush(
                    colors=["white"], 
                    default_color="white", 
                    default_size=3  # Smaller for precision
                ),
                interactive=True
            )
    
    erase_btn = gr.Button("🧹 Erase Person", variant="primary", size="lg")
    output_image = gr.Image(label="✨ Result", type="numpy")
    
    # When image is uploaded, copy to editor
    def update_editor(img):
        """Update editor with uploaded image."""
        if img is None:
            return None
        return img
    
    original_upload.change(
        fn=update_editor, 
        inputs=original_upload, 
        outputs=editor
    )
    
    # Erase button click
    erase_btn.click(
        fn=erase_person,
        inputs=[original_upload, editor],
        outputs=output_image,
        scroll_to_output=True
    )
    
    gr.Markdown("""
    ---
    
    **How it works:**
    - 🎯 Your click tells SAM (Segment Anything) where the person is
    - 🤖 SAM creates a precise mask of the entire person
    - 🎨 OpenCV Telea algorithm fills in the background naturally
    
    **Tips for best results:**
    - Click directly on the person's face
    - Works with multiple people (erase one at a time)
    - Best with clear, distinct backgrounds
    """)

if __name__ == "__main__":
    demo.launch(share=False)
