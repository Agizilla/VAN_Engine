import gradio as gr
import numpy as np
import cv2
import torch
from segment_anything import sam_model_registry, SamPredictor
import requests
import os
import logging
import zipfile

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

SAM_CHECKPOINT_URL = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
SAM_CHECKPOINT_PATH = "sam_vit_b_01ec64.pth"
MAX_IMAGE_SIZE = 1024
INPAINT_RADIUS_SCALE = 128

input_image = None
input_points = []

def download_sam_checkpoint():
    if os.path.exists(SAM_CHECKPOINT_PATH):
        try:
            with zipfile.ZipFile(SAM_CHECKPOINT_PATH, 'r') as zf:
                zf.testzip()
            logger.info("SAM checkpoint already exists.")
            return
        except:
            logger.info("SAM checkpoint corrupted, removing...")
            os.remove(SAM_CHECKPOINT_PATH)
    
    logger.info("Downloading SAM checkpoint...")
    response = requests.get(SAM_CHECKPOINT_URL, stream=True, timeout=300)
    response.raise_for_status()
    with open(SAM_CHECKPOINT_PATH, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    logger.info("SAM checkpoint download complete.")

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

def ensure_rgb(image_np):
    if len(image_np.shape) == 2:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
    elif len(image_np.shape) == 3 and image_np.shape[2] == 4:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
    elif image_np.dtype != np.uint8:
        image_np = (image_np * 255).astype(np.uint8)
    return image_np

def resize_if_needed(image_np):
    h, w = image_np.shape[:2]
    max_dim = max(h, w)
    if max_dim > MAX_IMAGE_SIZE:
        scale = MAX_IMAGE_SIZE / max_dim
        new_h, new_w = int(h * scale), int(w * scale)
        logger.info(f"Resizing from {w}x{h} to {new_w}x{new_h}")
        image_np = cv2.resize(image_np, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return image_np

def get_person_mask(image_np, point_x, point_y):
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
    logger.info(f"SAM mask - confidence: {scores[best_idx]:.3f}")
    return mask

def inpaint_background(image_np, mask):
    kernel = np.ones((3, 3), np.uint8)
    mask_dilated = cv2.dilate(mask, kernel, iterations=2)
    max_dim = max(image_np.shape[:2])
    inpaint_radius = max(3, int(max_dim / INPAINT_RADIUS_SCALE))
    result = cv2.inpaint(image_np, mask_dilated, inpaint_radius, flags=cv2.INPAINT_TELEA)
    return result

def on_image_select(img, evt: gr.SelectData):
    global input_image, input_points
    
    if img is None:
        raise gr.Error("Please upload an image first.")
    
    img = ensure_rgb(img)
    img = resize_if_needed(img)
    
    x = evt.index[0]
    y = evt.index[1]
    input_points.append([x, y])
    input_image = img.copy()
    
    logger.info(f"Click at ({x}, {y})")
    
    person_mask = get_person_mask(img, x, y)
    result = inpaint_background(img, person_mask)
    
    return result

def on_clear():
    global input_image, input_points
    input_points = []
    input_image = None
    return None

CUSTOM_CSS = """
* { font-family: 'Segoe UI', system-ui, sans-serif; }
h1 { font-weight: 800; color: #1e293b; }
"""

demo = gr.Blocks(css=CUSTOM_CSS)
with demo:
    gr.Markdown("# Person Eraser\n### Remove anyone from photos with one click")
    
    gr.Markdown("""
    **How to use:**
    1. Upload a photo
    2. Click on the person
    3. Done!
    """)
    
    with gr.Row():
        input_img = gr.Image(label="Upload & Click", type="numpy", interactive=True, height=500)
        output_img = gr.Image(label="Result", type="numpy", interactive=False, height=500)
    
    input_img.select(on_image_select, inputs=input_img, outputs=output_img)
    input_img.clear(on_clear)
    
    gr.Markdown("---")
    gr.Markdown("*Powered by SAM + OpenCV*")

demo.launch(server_name="0.0.0.0", server_port=7861)