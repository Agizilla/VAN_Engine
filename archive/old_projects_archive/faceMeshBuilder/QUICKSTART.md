# Quick Start Guide

## Installation (5 minutes)

1. **Install Python 3.8+** (if not already installed)
   - Download from https://python.org
   - Make sure to check "Add Python to PATH" during installation

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python verify_installation.py
   ```

## First Time Use (2 minutes)

1. **Run the application**:
   ```bash
   python face_avatar_3d.py
   ```

2. **Create your first 3D avatar**:
   - Click "1. Load Initial Image"
   - Select a frontal face photo
   - Click "View 3D Model" to see your 3D face
   - Use mouse to rotate, scroll to zoom

3. **Enhance with video** (optional):
   - Click "2. Load Video"
   - Select a video file showing the face from different angles
   - Wait for processing (you'll see a completion message)
   - View the improved model

4. **Save your work**:
   - Click "4. Save Model"
   - Choose location (defaults to `master.bmp`)

## Example Workflow

### Scenario: Create a 3D avatar from photos and videos

```bash
# Step 1: Start the app
python face_avatar_3d.py

# Step 2: In the GUI
1. Click "Load Initial Image" → select your frontal face photo
2. Click "View 3D Model" → see the initial model
3. Close the 3D viewer window
4. Click "Load Video" → select a video of your face
5. Wait for processing to complete
6. Click "View 3D Model" again → see the improved model
7. Click "Save Model" → save as "my_avatar.bmp"

# Step 3: Later, reload your model
1. Click "Load Model" → select "my_avatar.bmp"
2. Your model is instantly recreated!
```

## Controls

### Main Window
- **Button 1**: Load initial face image (required first step)
- **Button 2**: Load video to enhance model (optional)
- **Button 3**: Load saved model from master.bmp
- **Button 4**: Save current model to master.bmp
- **View 3D Model**: Open interactive 3D viewer

### 3D Viewer Window
- **Left Mouse + Drag**: Rotate the face model
- **Mouse Wheel Up**: Zoom in
- **Mouse Wheel Down**: Zoom out
- **Close Window**: Return to main interface

## Tips for Best Results

### For Initial Image:
✓ Use a clear, well-lit frontal face photo
✓ Face should fill most of the frame
✓ Neutral expression works best
✗ Avoid extreme angles
✗ Avoid heavy shadows

### For Video Enhancement:
✓ Show face from multiple angles (left, right, up, down)
✓ Move slowly and smoothly
✓ Good lighting throughout
✓ 30-60 seconds is plenty
✗ Avoid fast movements
✗ Don't obscure face with hands

## Common Questions

**Q: How long does video processing take?**
A: Depends on video length. A 1-minute video typically takes 30-60 seconds.

**Q: Can I process multiple videos?**
A: Yes! Process as many videos as you want. The system keeps improving quality.

**Q: What's the face grid for?**
A: It's a 10x10 texture atlas (100 faces max) that stores all the face captures used to build your model.

**Q: Why does my model have white areas?**
A: White areas are unmapped texture. Load videos from more angles to fill them in.

**Q: Can I share my model?**
A: Yes! Share both the .bmp file and the _metadata.npz file.

**Q: What format is the 3D model?**
A: The model uses 478 MediaPipe facial landmarks with texture mapping.

## Troubleshooting

**Problem**: "No face detected in image"
**Solution**: Ensure face is clearly visible and frontal. Try better lighting.

**Problem**: Video processing seems stuck
**Solution**: It's working! Processing happens in background. Wait for completion message.

**Problem**: 3D viewer won't open
**Solution**: 
1. Make sure you loaded an initial image first
2. Check OpenGL drivers are installed
3. Run `python verify_installation.py`

**Problem**: Model won't load
**Solution**: Make sure both .bmp and _metadata.npz files are in the same directory.

## Next Steps

Once you're comfortable with basic usage:

1. **Experiment with multiple videos** from different lighting conditions
2. **Compare quality** before and after video processing
3. **Save iterations** with different filenames to compare
4. **Try different initial images** to see how they affect the final model

## Need Help?

Check the full README.md for:
- Detailed technical information
- Advanced features
- Architecture details
- Troubleshooting guide

Enjoy creating 3D avatars! 🎭
