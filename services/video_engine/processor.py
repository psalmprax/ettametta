from moviepy import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ColorClip, vfx
import os
import random
import logging
from typing import List, Optional
from .transcription import transcription_service
from api.config import settings

class VideoProcessor:
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        # Check for GPU availability
        self.use_gpu = os.getenv("USE_GPU", "true").lower() == "true"
        self.codec = "h264_nvenc" if self.use_gpu else "libx264"
        
        # Dynamic Font Resolution
        self.font_path = settings.FONT_PATH
        if not os.path.exists(self.font_path):
            # Fallback for systems where the path differs
            fallbacks = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
                "/usr/local/share/fonts/DejaVuSans-Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc", # macOS
                "arial.ttf" # Windows
            ]
            for f in fallbacks:
                if os.path.exists(f):
                    self.font_path = f
                    break
            else:
                logging.warning(f"⚠️ No valid font found. Captions may fail. Configured: {self.font_path}")
        
        logging.info(f"Video Engine initialized with font: {self.font_path}")

    def apply_originality_transformation(self, input_path: str, output_name: str) -> str:
        """
        Applies 'Copyright-Safe' transformations:
        - Restructure flow
        - Remove dead space (simple silent part removal placeholder)
        - Add new hook overlay
        - Insert pattern interrupts
        """
        clip = VideoFileClip(input_path)
        
        # 1. Basic Transformation: Mirror and slightly zoom to change hash
        transformed = clip.with_effects([vfx.MirrorX()]).resized(height=int(clip.h * 1.05))
        
        # 1.1 Color Grading (Subtle shift to avoid deduplication)
        transformed = transformed.with_effects([vfx.LumContrast(lum=0, contrast=0.05)])

        # 2. Add 'Pattern Interrupt' (e.g., a simple flash or text overlay every 3 seconds)
        duration = transformed.duration
        overlays = []
        for i in range(2, int(duration), 3):
            txt_clip = TextClip(text="!", font_size=70, color='white', font=self.font_path).with_start(i).with_duration(0.2).with_position('center')
            overlays.append(txt_clip)
        
        final_clip = CompositeVideoClip([transformed] + overlays)
        
        output_path = os.path.join(self.output_dir, output_name)
        try:
            final_clip.write_videofile(output_path, codec=self.codec, audio_codec="aac")
        except Exception:
            # Fallback to CPU if NVENC fails
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        return output_path

    def concatenate_highlights(self, clip_paths: List[str], output_name: str) -> str:
        clips = [VideoFileClip(p) for p in clip_paths]
        final_clip = concatenate_videoclips(clips, method="compose")
        
        output_path = os.path.join(self.output_dir, output_name)
        try:
            final_clip.write_videofile(output_path, codec=self.codec)
        except Exception:
            final_clip.write_videofile(output_path, codec="libx264")
        return output_path

    def apply_speed_ramping(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Randomly shifts speed between 0.9x and 1.1x to reset algorithm clocks.
        """
        # Simplistic implementation: change overall speed slightly
        speed = random.uniform(0.95, 1.05)
        return clip.with_effects([vfx.MultiplySpeed(speed)])

    def apply_dynamic_jitter(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Simulates handheld motion by applying small random position offsets.
        Uses a slightly larger canvas to avoid black edges.
        """
        def jitter(t):
            # Reduced jitter intensity for organic feel
            x = int(random.uniform(-1, 1))
            y = int(random.uniform(-1, 1))
            return (x, y)
        
        # Increase zoom slightly more to ensure zero black edge bleeding during jitter
        zoomed = clip.resized(height=int(clip.h * 1.04))
        return zoomed.with_position(jitter)

    def apply_cinematic_overlays(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Adds high-energy light leaks/overlays with smooth transitions.
        """
        leak = ColorClip(size=clip.size, color=(255, 210, 160)) \
            .with_start(random.uniform(0, clip.duration - 1.0)) \
            .with_duration(0.6) \
            .with_opacity(0.08) \
            .with_effects([vfx.CrossFadeIn(0.2), vfx.CrossFadeOut(0.2)])
        
        return CompositeVideoClip([clip, leak.with_position('center')])

    async def process_full_pipeline(self, input_path: str, output_name: str, enabled_filters: Optional[List[str]] = None) -> str:
        """
        Full ViralForge Pipeline with Dynamic Filters and Ultra-High Quality Render.
        """
        # 1. Transcribe
        transcript = await transcription_service.transcribe_video(input_path)
        
        # 2. Base Clip setup
        clip = VideoFileClip(input_path)
        
        # 3. Apply Multi-Layer Transformations
        # Default core transforms
        transformed = clip.with_effects([vfx.MirrorX()]).resized(height=int(clip.h * (1.05)))
        
        # Optional Add-ons (Pro Filters)
        if enabled_filters:
            if "f6" in enabled_filters:
                transformed = self.apply_speed_ramping(transformed)
            if "f8" in enabled_filters:
                transformed = self.apply_dynamic_jitter(transformed)
            if "f7" in enabled_filters:
                transformed = self.apply_cinematic_overlays(transformed)

        # 4. Pattern Interrupts & Audio Integration
        duration = transformed.duration
        elements = [transformed]
        
        for i in range(2, int(duration), 3):
            # Smooth flash interrupt
            flash = ColorClip(size=transformed.size, color=(255, 255, 255)) \
                .with_start(i).with_duration(0.15) \
                .with_opacity(0.12) \
                .with_effects([vfx.CrossFadeIn(0.05), vfx.CrossFadeOut(0.05)])
            elements.append(flash)

        # 5. Add Captions from transcript
        caption_clips = []
        for item in transcript:
            txt = TextClip(
                text=item["text"].upper(),
                font_size=72,
                color='#FFE100', # High-vis YouTube Yellow
                font=self.font_path,
                stroke_color='black',
                stroke_width=2.5,
                method='caption',
                size=(int(transformed.w * 0.85), None)
            ).with_start(item["start"]).with_duration(item["end"] - item["start"]).with_position(('center', 0.8))
            caption_clips.append(txt)
            
        final_clip = CompositeVideoClip(elements + caption_clips)
        output_path = os.path.join(self.output_dir, output_name)
        
        # Premium Render Settings
        render_args = {
            "filename": output_path,
            "fps": 30,
            "threads": 4,
            "audio_codec": "aac",
            "ffmpeg_params": [
                "-crf", "18",        # Constant Rate Factor: 18 is visually lossless
                "-maxrate", "12M",    # Target high-end social bitrate
                "-bufsize", "24M",
                "-preset", "slower"   # Better compression artifacts
            ]
        }
        
        try:
            if self.use_gpu:
                final_clip.write_videofile(**{**render_args, "codec": "h264_nvenc"})
            else:
                final_clip.write_videofile(**{**render_args, "codec": "libx264"})
        except Exception:
            # Absolute fallback
            final_clip.write_videofile(output_path, codec="libx264", fps=24)
        
        return output_path

base_video_processor = VideoProcessor()
