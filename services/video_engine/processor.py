from moviepy import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ColorClip, vfx
import os
import random
import logging
from typing import List, Optional, Dict
from .transcription import transcription_service
from .ocr_service import ocr_service
from .stock_service import stock_service
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
        
        # IMPORTANT: Preserve original audio from the source video
        if clip.audio:
            final_clip = final_clip.with_audio(clip.audio)
        
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

    def apply_speed_ramping(self, clip: VideoFileClip, speed_range: List[float] = [0.95, 1.05]) -> VideoFileClip:
        """
        Randomly shifts speed based on AI strategy range to reset algorithm clocks.
        """
        speed = random.uniform(speed_range[0], speed_range[1])
        return clip.with_effects([vfx.MultiplySpeed(speed)])

    def apply_dynamic_jitter(self, clip: VideoFileClip, intensity: float = 1.0) -> VideoFileClip:
        """
        Simulates handheld motion by applying small random position offsets.
        Uses intensity from AI strategy.
        """
        def jitter(t):
            # Scale jitter by intensity
            x = int(random.uniform(-1 * intensity, 1 * intensity))
            y = int(random.uniform(-1 * intensity, 1 * intensity))
            return (x, y)
        
        # Increase zoom slightly more as intensity increases to avoid black edges
        zoom_factor = 1.04 + (intensity * 0.01)
        zoomed = clip.resized(height=int(clip.h * zoom_factor))
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

    def apply_atmospheric_glow(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Adds a soft, glowing atmospheric layer (f9).
        """
        glow = clip.with_effects([vfx.LumContrast(lum=5, contrast=0.1)]).with_opacity(0.3)
        return CompositeVideoClip([clip, glow])

    def apply_film_grain(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Adds a subtle film grain effect to simulate analog texture (f10).
        """
        # Placeholder for real noise generation; for now, we use a subtle contrast jitter
        return clip.with_effects([vfx.LumContrast(lum=0, contrast=0.08)])

    def apply_grayscale(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Converts video to black and white for the Noir style (f11).
        """
        return clip.with_effects([vfx.BlackAndWhite()])

    def apply_random_glitch(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Applies a random glitch effect by shifting RGB channels or adding noise (f12).
        """
        # MoviePy doesn't have a direct RGB shift, so we apply a jittered color shift
        return clip.with_effects([vfx.Colorx(factor=random.uniform(0.9, 1.1))]).resized(height=int(clip.h * 1.01))

    def trim_to_hooks(self, clip: VideoFileClip, hooks: List[List[float]]) -> VideoFileClip:
        """
        Cuts the video to only the segments identified as high-energy hooks.
        """
        if not hooks:
            return clip
        
        segments = []
        for start, end in hooks:
            # Buffer the end slightly
            end = min(end + 0.5, clip.duration)
            segments.append(clip.subclipped(start, end))
        
        if not segments:
            return clip
            
        return concatenate_videoclips(segments, method="compose")

            
        return concatenate_videoclips(segments, method="compose")

    async def inject_b_roll(self, clip: VideoFileClip, keywords: List[str]) -> VideoFileClip:
        """
        Fetches a stock B-roll clip and overlays it onto the main video.
        """
        if not keywords:
            return clip
            
        keyword = random.choice(keywords)
        logging.info(f"[VideoProcessor] Attempting B-roll injection for keyword: {keyword}")
        
        urls = await stock_service.fetch_b_roll(keyword, count=1)
        if not urls:
            return clip
            
        b_roll_path = await stock_service.download_stock_video(urls[0])
        if not b_roll_path:
            return clip
            
        try:
            b_roll_clip = VideoFileClip(b_roll_path).resized(width=clip.w)
            # Take 2-3 seconds of B-roll
            b_roll_duration = min(b_roll_clip.duration, 3.0)
            b_roll_clip = b_roll_clip.subclipped(0, b_roll_duration)
            
            # Insert at a random point in the first half of the main clip
            insert_point = random.uniform(2.0, max(2.5, clip.duration / 2))
            
            # Simple overlay (for now, we just place it on top of the elements list later)
            b_roll_clip = b_roll_clip.with_start(insert_point).with_position('center')
            
            return b_roll_clip
        except Exception as e:
            logging.error(f"[VideoProcessor] Error in B-roll injection: {e}")
            return None

    async def process_full_pipeline(self, input_path: str, output_name: str, enabled_filters: Optional[List[str]] = None, strategy: Optional[Dict] = None) -> str:
        """
        Full ViralForge Pipeline with Dynamic AI Strategies.
        """
        # 1. Transcribe
        transcript = await transcription_service.transcribe_video(input_path)
        
        # 2. Base Clip setup
        clip = VideoFileClip(input_path)
        
        # 2.1 OCR-Aware Strategy
        caption_strategy = ocr_service.get_caption_strategy(input_path)
        logging.info(f"[VideoProcessor] OCR Strategy identifies: {caption_strategy}")
        
        # 2.2 Semantic Trimming (Hooks)
        if strategy and strategy.get("hook_points"):
            logging.info(f"[VideoProcessor] Semantic trimming to hooks: {strategy['hook_points']}")
            clip = self.trim_to_hooks(clip, strategy["hook_points"])

        # 2.3 B-Roll Injection
        b_roll_overlay = None
        if strategy and strategy.get("b_roll_keywords"):
            b_roll_overlay = await self.inject_b_roll(clip, strategy["b_roll_keywords"])

        # 3. Apply Multi-Layer Transformations
        # Default core transforms
        transformed = clip.with_effects([vfx.MirrorX()]).resized(height=int(clip.h * (1.05)))
        
        # Merge Dashboard filters with AI recommendations if strategy exists
        active_filters = enabled_filters or []
        if strategy and strategy.get("recommended_filters"):
            # Add AI recommendations (avoid duplicates)
            active_filters = list(set(active_filters + strategy["recommended_filters"]))

        # 4. Optional Add-ons (Pro Filters) with Dynamic Intensity
        if active_filters:
            if "f6" in active_filters:
                transformed = self.apply_speed_ramping(transformed, speed_range=strategy.get("speed_range", [0.95, 1.05]) if strategy else [0.95, 1.05])
            if "f8" in active_filters:
                transformed = self.apply_dynamic_jitter(transformed, intensity=strategy.get("jitter_intensity", 1.0) if strategy else 1.0)
            if "f7" in active_filters:
                transformed = self.apply_cinematic_overlays(transformed)
            if "f9" in active_filters:
                transformed = self.apply_atmospheric_glow(transformed)
            if "f10" in active_filters:
                transformed = self.apply_film_grain(transformed)
            if "f11" in active_filters:
                transformed = self.apply_grayscale(transformed)
            if "f12" in active_filters:
                transformed = self.apply_random_glitch(transformed)

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

        # 4.1 Apply B-Roll Overlay if exists
        if b_roll_overlay:
            elements.append(b_roll_overlay)

        # 5. Add Captions from transcript with dynamic positioning
        caption_clips = []
        # Calculate Y position based on OCR strategy
        y_pos = 0.8 # Default bottom
        if caption_strategy == "top":
            y_pos = 0.15
        elif caption_strategy == "center":
            y_pos = 0.5

        # VLM-Driven Aesthetic: Contrasting Caption Color
        caption_color = '#FFE100' # Default Viral Yellow
        if strategy and strategy.get("vibe") == "Dramatic":
            caption_color = '#FFFFFF' # Stark White for drama
        elif strategy and strategy.get("vibe") == "Energetic":
            caption_color = '#00FF00' # Neon Green for energy

        for item in transcript:
            # Check if word is within current trimmed timeline
            if item["start"] > transformed.duration:
                continue

            txt = TextClip(
                text=item["text"].upper(),
                font_size=72,
                color=caption_color,
                font=self.font_path,
                stroke_color='black',
                stroke_width=2.5,
                method='caption',
                size=(int(transformed.w * 0.85), None)
            ).with_start(item["start"]).with_duration(item["end"] - item["start"]).with_position(('center', y_pos))
            caption_clips.append(txt)
            
        final_clip = CompositeVideoClip(elements + caption_clips)
        
        # IMPORTANT: Preserve original audio from the source video
        if clip.audio:
            final_clip = final_clip.with_audio(clip.audio)
        output_path = os.path.join(self.output_dir, output_name)
        
        # Premium Render Settings
        render_args = {
            "filename": output_path,
            "fps": 30,
            "threads": 4,
            "audio_codec": "aac",
            "audio": True,  # Ensure audio is enabled
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
