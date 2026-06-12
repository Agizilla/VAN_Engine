---
name: ImageSkill
description: Master Image Skill — MediaPipe face landmarks, blink/talk animation (RBF warp), 3D face mesh, SAM segmentation, Stable Diffusion inpainting, face averaging/swapping, OCR, cartoonization. USE WHEN image, photo, face, detect faces, animate face, segment image, inpaint, OCR, cartoon, swap face, effects, vision, computer vision, edit photo.
how_to: Invoke via IPC `image:*` or directly from Python `from master_skills.imageSkill import ImageSkill`
version: 1.0.0
mergedProjects: 11
countPublicMethods: 52
countLineNumbers: 768
---

# ImageSkill

Master image skill aggregating 11 projects. Use the ImageSkill class for any image operation.

## Capabilities (14)

| Capability | Methods | Description |
|---|---|---|
| Face Detection | `detect_faces`, `get_face_landmarks` | MediaPipe face detection |
| Face Animation | `animate_face`, `animate_blink`, `animate_talk` | RBF warp-based animation |
| 3D Face Mesh | `build_face_mesh`, `generate_texture_atlas` | 3D reconstruction |
| Segmentation | `segment`, `segment_with_points` | SAM-based segmentation |
| Inpainting | `inpaint`, `inpaint_with_mask` | Stable Diffusion inpainting |
| Face Ops | `average_faces`, `swap_faces` | Face averaging and swapping |
| OCR | `ocr`, `ocr_regions` | Text extraction from images |
| Effects | `apply_effect`, `cartoonize` | Image stylization |
| Classification | `classify` | Image classification |
| Info | `get_capabilities`, `get_meta` | Introspection |

## Usage

```python
from master_skills.imageSkill import ImageSkill

skill = ImageSkill()
faces = skill.detect_faces(image)
animated = skill.animate_face(image, frames=30)
mask = skill.segment(image, points=[(100, 200), (300, 400)])
result = skill.inpaint(image, mask, prompt='a cat')
text = skill.ocr(image)
```

## IPC Channels

- `image:detect` — Detect faces in image
- `image:segment` — Segment image regions
- `image:inpaint` — Inpaint image regions
- `image:ocr` — Extract text from image
- `image:animate` — Animate a face image
- `image:effects` — Apply image effects
- `image:info` — Get skill metadata
