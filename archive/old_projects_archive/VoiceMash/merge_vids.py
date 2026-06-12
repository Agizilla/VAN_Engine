import os
import random
import gc
# Stable v2.x sub-module imports
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.concatenate import concatenate_videoclips

def build_production():
    # 1. Asset Discovery
    video_files = sorted([f for f in os.listdir('.') if f.endswith('.mp4') and "Output" not in f and "Final" not in f])
    image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    audio_path = next((f for f in os.listdir('.') if f.endswith('.mp3')), None) or \
                 next((f for f in os.listdir('.') if f.endswith('.mpeg')), None)

    if not video_files or not audio_path:
        print("Required assets (mp4 + audio) not found.")
        return

    # 2. Load Base Video and Get Meta-Data
    video_clips = [VideoFileClip(f) for f in video_files]
    main_video = concatenate_videoclips(video_clips)
    
    target_res = main_video.size  # [Width, Height]
    target_fps = main_video.fps if main_video.fps else 24
    
    audio = AudioFileClip(audio_path)
    v_dur = main_video.duration
    a_dur = audio.duration

    # 3. Handle Extension (3 images per second)
    if v_dur >= a_dur:
        try:
            final_clip = main_video.subclipped(0, a_dur)
        except AttributeError:
            final_clip = main_video.subclip(0, a_dur)
    else:
        gap_duration = a_dur - v_dur
        print(f"Extending video by {round(gap_duration, 2)}s using 3 images/sec...")
        
        img_duration = 0.333
        num_images_needed = int(gap_duration / img_duration) + 1
        
        extension_clips = []
        for i in range(num_images_needed):
            if not image_files: break
            
            img_path = random.choice(image_files)
            
            # --- COMPATIBILITY FIX ---
            # Using set_duration and set_fps as requested by your traceback.
            # We use 'margin' or manual size setting if resize() is missing.
            img_clip = ImageClip(img_path).set_duration(img_duration).set_fps(target_fps)
            
            # Manual Resizing Logic: This bypasses the missing .resize() attribute
            # by forcing the clip to the target resolution
            img_clip = img_clip.set_position('center').on_color(
                size=target_res, color=(0,0,0), col_opacity=1
            )
            
            extension_clips.append(img_clip)

        extension_video = concatenate_videoclips(extension_clips)
        final_clip = concatenate_videoclips([main_video, extension_video])
        
        # Ensure exact match
        try:
            final_clip = final_clip.subclipped(0, a_dur)
        except AttributeError:
            final_clip = final_clip.subclip(0, a_dur)

    # 4. Final Export
    output_name = f"Final_Production_Stable.mp4"
    
    try:
        final_clip = final_clip.with_audio(audio)
    except AttributeError:
        final_clip = final_clip.set_audio(audio)
    
    print(f"Exporting: {output_name} ({target_res[0]}x{target_res[1]})")
    
    # pix_fmt yuv420p is the secret sauce for fixing visual glitches in players
    final_clip.write_videofile(
        output_name, 
        codec="libx264", 
        audio_codec="aac", 
        fps=target_fps, 
        preset="ultrafast",
        ffmpeg_params=["-pix_fmt", "yuv420p"]
    )

    # 5. Resource Cleanup
    for clip in video_clips: clip.close()
    audio.close()
    gc.collect()

if __name__ == "__main__":
    build_production()