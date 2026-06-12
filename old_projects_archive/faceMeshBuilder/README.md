# 3D Face Avatar Generator

A Python application that creates interactive 3D face models from photos and videos with texture mapping and quality enhancement.

## Features

- **3D Face Mesh Generation**: Creates a 3D face model from a single frontal photo using MediaPipe landmarks
- **Interactive 3D Viewer**: Rotate (mouse drag) and zoom (mouse wheel) the 3D model in real-time
- **Video Processing**: Extract faces from video to fill in missing details and improve texture quality
- **Intelligent Quality Control**: Automatically replaces lower quality face captures with better ones
- **Texture Atlas**: Creates a 10x10 grid (200x200 per face) of all faces used in the model
- **Model Persistence**: Save/load models as `master.bmp` with associated metadata

## Requirements

- Python 3.8+
- Webcam or video files for video processing
- Frontal face images for initial model creation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python face_avatar_3d.py
```

## Usage

### Main Interface

The application provides 5 main functions:

#### 1. Load Initial Image
- Click "1. Load Initial Image"
- Select a frontal face photo (JPG, PNG, BMP)
- The system will:
  - Detect the face using MediaPipe
  - Extract 3D landmarks (478 points)
  - Create initial 3D mesh
  - Crop and add face to texture grid (200x200)
  - Initialize the texture atlas

#### 2. Load Video
- Click "2. Load Video"
- Select a video file (MP4, AVI, MOV, MKV)
- The system will:
  - Process frames (every 10th frame for speed)
  - Extract faces and calculate quality scores
  - Replace lower quality faces in the grid
  - Update the texture atlas in real-time
  - Show progress when complete

**Quality Metrics:**
- Sharpness (Laplacian variance): 70% weight
- Brightness: 30% weight
- Only better quality faces replace existing ones

#### 3. Load Model
- Click "3. Load Model"
- Select a `master.bmp` file
- The system will:
  - Load the 10x10 face grid
  - Extract individual 200x200 face crops
  - Load 3D mesh metadata from `*_metadata.npz`
  - Reconstruct the complete model

#### 4. Save Model
- Click "4. Save Model"
- Choose save location (defaults to `master.bmp`)
- The system will:
  - Save face grid as BMP (2000x2000 pixels)
  - Save metadata as NPZ (vertices, texture coords, face indices, quality scores)

#### 5. View 3D Model
- Click "View 3D Model"
- A new window opens with the 3D viewer
- **Controls:**
  - **Left Mouse Drag**: Rotate model
  - **Mouse Wheel Up**: Zoom in
  - **Mouse Wheel Down**: Zoom out
  - **Close Window**: Return to main interface

## Technical Details

### 3D Mesh Structure
- **Vertices**: 478 facial landmarks from MediaPipe Face Mesh
- **Coordinates**: Normalized 3D positions (x, y, z)
- **Texture Mapping**: UV coordinates for each vertex
- **Faces**: Triangulated mesh using MediaPipe tesselation

### Texture Atlas
- **Grid Size**: 10x10 = 100 face crops maximum
- **Crop Size**: 200x200 pixels each
- **Total Size**: 2000x2000 pixels
- **Format**: BGR (OpenCV) → RGB (OpenGL)

### Face Quality Scoring
```python
quality = laplacian_variance * 0.7 + brightness * 0.3
```
- Higher scores indicate sharper, better-lit faces
- Automatic replacement of lower quality textures

### File Structure
When you save a model:
```
master.bmp          # 2000x2000 texture atlas
master_metadata.npz # Numpy archive with:
                    # - vertices (478x3 array)
                    # - texture_coords (478x2 array)
                    # - faces_indices (array of triangles)
                    # - face_qualities (quality scores)
```

## Workflow Example

1. **Initial Setup**:
   - Load a frontal face photo
   - System creates base 3D mesh

2. **Enhancement**:
   - Load a video of the person's face from different angles
   - System extracts and evaluates faces
   - Better quality faces replace existing ones
   - Texture atlas improves over time

3. **Review**:
   - View the 3D model
   - Rotate and inspect from all angles

4. **Save**:
   - Save the model to `master.bmp`
   - Share or reload later

5. **Reload**:
   - Load `master.bmp` to instantly recreate the model
   - Continue enhancement with more videos

## Tips for Best Results

1. **Initial Image**:
   - Use a well-lit frontal face photo
   - Face should be clearly visible
   - Neutral expression works best

2. **Video Processing**:
   - Include various angles (left, right, up, down)
   - Good lighting improves quality scores
   - Slow, smooth movements work better than quick jerks
   - 30-60 second videos provide plenty of data

3. **Quality**:
   - The system automatically selects best quality faces
   - Multiple videos can be processed to keep improving
   - Grid fills up to 100 faces maximum

## Troubleshooting

**"No face detected in image"**
- Ensure face is clearly visible and frontal
- Check lighting conditions
- Try a different photo

**Video processing is slow**
- System processes every 10th frame by default
- Longer videos take more time but provide more data
- Processing happens in background thread

**3D model looks incomplete**
- Only frontal view is textured from single image
- Process videos from multiple angles to fill in gaps
- White areas indicate missing texture data

**Model won't load**
- Ensure both `.bmp` and `_metadata.npz` files exist
- Check file isn't corrupted
- Try recreating from original images

## Advanced Features

### Threading
- Video processing runs in separate thread
- UI remains responsive during processing
- Real-time texture updates every 5 faces

### OpenGL Rendering
- Hardware-accelerated 3D graphics
- Smooth 60 FPS rendering
- Perspective projection with proper depth

### MediaPipe Integration
- 478-point facial landmark detection
- Real-time face tracking in video
- 3D coordinates with depth information

## License

This project uses:
- MediaPipe (Apache 2.0)
- OpenCV (Apache 2.0)
- PyOpenGL (BSD)
- Pygame (LGPL)

## Future Enhancements

Potential improvements:
- Export to OBJ/FBX formats
- Lighting and shader options
- Animation support
- Multiple face models
- Depth map integration
