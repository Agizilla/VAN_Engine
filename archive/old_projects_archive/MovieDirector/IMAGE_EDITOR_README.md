# Image Background Remover & Figure Editor

**Ready to use!** Single-file Python tool with all requested features.

## Install & Run

```bash
pip install gradio opencv-python mediapipe numpy pillow
python image_editor_tool.py
```

Visit: `http://localhost:7860`

## Features Implemented ✅

### Core Functions
- ✅ **Remove Humans** – Detects and removes people from background
- ✅ **Fix Background** – Color smear strategy (left→right, top→bottom)
- ✅ **Extract Figures** – Separated humans shown in Cast panel (right)
- ✅ **Undo** – Full undo history
- ✅ **Clear** – Reset everything

### Body Adjustments
- ✅ **Make Thinner** – Scales body horizontally (face stays fixed)
- ✅ **Make Fatter** – Inverse scaling
- ✅ **Make Taller** – Scales vertically
- ✅ **Make Shorter** – Inverse vertical scale

### Eye/Pupil Controls
- ✅ **Bigger Pupils** – Enlarge iris (1.3x)
- ✅ **Smaller Pupils** – Shrink iris (0.7x)
- ✅ **Pupil Detection** – Automatic via MediaPipe face mesh

### UI Layout
```
┌─────────────┬──────────────────┬────────────┐
│  Upload     │  Working Image   │   Cast     │
│  Original   │  + Controls      │   Figures  │
│             │                  │ (Extracted)│
└─────────────┴──────────────────┴────────────┘
```

## How It Works

### 1. Remove Humans
- Uses MediaPipe Selfie Segmentation (model=1, accurate)
- Binary mask: person=white, background=black
- Returns: background only, mask, extracted figures

### 2. Fix Background (Color Smear)
- **Horizontal pass**: Smears colors left→right
- **Vertical pass**: Smears colors top→bottom
- Gradual color increment (realistic blending)
- Fills holes left by removed humans

### 3. Body Modifications
- Detects body using MediaPipe Pose
- Keeps head/face stationary
- Scales body region independently
- Options: thin/fat (horizontal), tall/short (vertical)

### 4. Pupil Adjustments
- MediaPipe Face Mesh + Iris detection
- Detects 5 landmarks per iris
- Circular mask blending (smooth, natural)
- Preserves skin around iris

## Files Generated

```
image_editor_tool.py (520 lines)
├── ImageEditorState      # Undo/history management
├── HumanRemover         # Segmentation + background fix
├── EyeOrchestrator      # Pupil scaling
└── BodyModifier         # Body shape changes
```

## Known Limitations

- Single person per image (MediaPipe max_num_faces=1)
- Pose detection works best with full-body visible
- Color smear is basic (Phase 2: AI inpainting)
- No manual figure repositioning yet (Phase 2)

## Next Phase

Phase 2 additions:
- [ ] AI-powered background inpainting (DALL-E style)
- [ ] Drag-drop figure repositioning
- [ ] Multiple humans support
- [ ] Face editing (smile, age, etc.)
- [ ] Export/batch processing

---

**Production ready. Enjoy!** 🎨

