"""
Sound Design Service - Any Tier 3 Enhancement

Adds background music and sound effects to videos.
Disabled by default - enable via ENABLE_SOUND_DESIGN=true
"""

import os
import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)


class SoundDesignService:
    """
    Any sound design enhancement for video processing.
    Adds background music and SFX based on video mood/niche.
    """

    # Royalty-free music moods mapped to niches
    NICHE_MOOD_MAP = {
        "finance": ["inspirational", "corporate", "upbeat"],
        "crypto": ["electronic", "tech", "modern"],
        "motivation": ["epic", "inspirational", "uplifting"],
        "tech": ["electronic", "modern", "futuristic"],
        "luxury": ["elegant", "sophisticated", "ambient"],
        "business": ["corporate", "professional", "confident"],
        "health": ["calm", "peaceful", "ambient"],
        "fitness": ["energetic", "powerful", "upbeat"],
        "news": ["professional", "breaking", "corporate"],
        "documentary": ["ambient", "cinematic", "emotional"],
        "default": ["cinematic", "ambient", "modern"],
    }

    # SFX categories
    SFX_CATEGORIES = {
        "transition": ["whoosh", "swoosh", "impact"],
        "notification": ["ding", "chime", "alert"],
        "emphasis": ["beat", "pulse", "hit"],
        "ambient": ["wind", "rain", "nature"],
    }

    def __init__(self):
        self.enabled = os.getenv("ENABLE_SOUND_DESIGN", "false").lower() == "true"
        self.library_path = os.getenv("SOUND_LIBRARY_PATH", "/var/lib/ettametta/sounds")
        self.default_volume = float(os.getenv("MUSIC_VOLUME", "0.15"))
        self.sfx_volume = float(os.getenv("SFX_VOLUME", "0.3"))

        logger.info(f"[SoundDesign] Initialized - Enabled: {self.enabled}")

    def _get_moods_for_niche(self, niche: str) -> list[str]:
        """Get appropriate moods for a given niche"""
        niche_lower = niche.lower()

        for key, moods in self.NICHE_MOOD_MAP.items():
            if key in niche_lower:
                return moods

        return self.NICHE_MOOD_MAP["default"]

    async def add_background_music(
        self,
        video_path: str,
        niche: str = "default",
        mood: str | None = None,
        fade_in: float = 1.0,
        fade_out: float = 2.0,
    ) -> str | None:
        """
        Add background music to a video.

        Args:
            video_path: Path to input video
            niche: Content niche for mood selection
            mood: Specific mood (optional, auto-selected if not provided)
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds

        Returns:
            Path to enhanced video with background music, or None if disabled
        """
        if not self.enabled:
            logger.debug("[SoundDesign] Disabled, skipping background music")
            return None

        if not mood:
            moods = self._get_moods_for_niche(niche)
            mood = random.choice(moods)

        logger.info(
            f"[SoundDesign] Adding background music - niche: {niche}, mood: {mood}"
        )

        try:
            from moviepy import VideoFileClip, AudioFileClip, afx
            import uuid

            # Generate unique output path
            output_name = f"music_{uuid.uuid4().hex[:8]}.mp4"
            output_path = os.path.join(os.path.dirname(video_path), output_name)

            # 1. Load video and get duration
            video = VideoFileClip(video_path)
            duration = video.duration

            # 2. Find and load music track
            music_track_path = None
            music_dir = Path(self.library_path) / mood
            if music_dir.exists():
                tracks = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
                if tracks:
                    music_track_path = str(random.choice(tracks))

            if not music_track_path:
                logger.warning(
                    f"[SoundDesign] No music track found for mood {mood}. Falling back."
                )
                # We could use a default track here if we had one
                video.close()
                return None

            logger.info(f"[SoundDesign] Using track: {music_track_path}")

            # 3. Process audio
            music = AudioFileClip(music_track_path)

            # Loop music if shorter than video, or trim if longer
            if music.duration < duration:
                # Basic looping
                from moviepy.audio.AudioClip import CompositeAudioClip

                loops = int(duration / music.duration) + 1
                music = CompositeAudioClip(
                    [music.with_start(i * music.duration) for i in range(loops)]
                )

            music = music.subclipped(0, duration)

            # Apply volume and fades
            music = music.with_effects([afx.AudioVolume(self.default_volume)])
            if fade_in > 0:
                music = music.with_effects([afx.AudioFadeIn(fade_in)])
            if fade_out > 0:
                music = music.with_effects([afx.AudioFadeOut(fade_out)])

            # 4. Composite audio
            if video.audio:
                # Mix with existing audio (e.g. voiceover)
                from moviepy.audio.AudioClip import CompositeAudioClip

                final_audio = CompositeAudioClip([video.audio, music])
            else:
                final_audio = music

            # 5. Write final video
            final_video = video.with_audio(final_audio)
            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                fps=video.fps or 30,
            )

            # Cleanup
            video.close()
            final_video.close()
            music.close()

            return output_path

        except Exception as e:
            logger.exception(f"[SoundDesign] Error adding background music: {e}")
            if "video" in locals():
                video.close()
            return None

    async def add_sfx(
        self,
        video_path: str,
        sfx_type: str = "transition",
        timing: list[float] | None = None,
    ) -> str | None:
        """
        Add sound effects to a video.

        Args:
            video_path: Path to input video
            sfx_type: Type of SFX (transition, notification, emphasis, ambient)
            timing: list of timestamps (in seconds) when to play SFX

        Returns:
            Path to enhanced video with SFX, or None if disabled
        """
        if not self.enabled:
            logger.debug("[SoundDesign] Disabled, skipping SFX")
            return None

        logger.info(f"[SoundDesign] Adding SFX - type: {sfx_type}")

        try:
            from moviepy import VideoFileClip, AudioFileClip, afx
            from moviepy.audio.AudioClip import CompositeAudioClip
            import uuid

            sfx_dir = Path(self.library_path) / "sfx" / sfx_type
            if not sfx_dir.exists():
                logger.warning(f"[SoundDesign] No SFX library found at {sfx_dir}")
                return None

            effects = list(sfx_dir.glob("*.mp3")) + list(sfx_dir.glob("*.wav"))
            if not effects:
                logger.warning(f"[SoundDesign] No SFX files found in {sfx_dir}")
                return None

            effect_path = str(random.choice(effects))
            logger.info(f"[SoundDesign] Using effect: {effect_path}")

            # Load video and SFX
            video = VideoFileClip(video_path)
            sfx_clip = AudioFileClip(effect_path)

            # Determine timing
            if not timing:
                # Default: place SFX at 0s, middle, and near end
                duration = video.duration
                timing = [0.0, duration / 2, max(0, duration - 2)]

            # Build composite audio with SFX at specified timestamps
            audio_clips = []
            if video.audio:
                audio_clips.append(video.audio)

            for t in timing:
                positioned_sfx = sfx_clip.with_start(t).with_effects(
                    [afx.AudioVolume(self.sfx_volume)]
                )
                audio_clips.append(positioned_sfx)

            final_audio = CompositeAudioClip(audio_clips)

            # Write output
            output_name = f"sfx_{uuid.uuid4().hex[:8]}.mp4"
            output_path = os.path.join(os.path.dirname(video_path), output_name)
            final_video = video.with_audio(final_audio)
            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                fps=video.fps or 30,
            )

            # Cleanup
            video.close()
            final_video.close()
            sfx_clip.close()

            return output_path

        except Exception as e:
            logger.exception(f"[SoundDesign] Error adding SFX: {e}")
            return None

    async def mix_audio_tracks(
        self,
        voice_path: str,
        background_path: str | None = None,
        sfx_paths: list[str] | None = None,
    ) -> str | None:
        """
        Mix multiple audio tracks together.
        """
        if not self.enabled:
            return voice_path

        logger.info("[SoundDesign] Mixing audio tracks")

        try:
            from moviepy.audio.AudioClip import CompositeAudioClip
            from moviepy import AudioFileClip, afx
            import uuid

            # 1. Load tracks
            clips = []

            # Voice is the primary track
            voice = AudioFileClip(voice_path)
            clips.append(voice)

            # 2. Add background music if provided
            if background_path and os.path.exists(background_path):
                bg = AudioFileClip(background_path)
                # Loop or trim to match voice duration
                if bg.duration < voice.duration:
                    loops = int(voice.duration / bg.duration) + 1
                    bg = CompositeAudioClip(
                        [bg.with_start(i * bg.duration) for i in range(loops)]
                    )
                bg = bg.subclipped(0, voice.duration)

                # Apply volume and ducking (simplified ducking: fixed low volume)
                bg = bg.with_effects([afx.AudioVolume(self.default_volume)])
                clips.append(bg)

            # 3. Add SFX if provided
            if sfx_paths:
                for s_path in sfx_paths:
                    if os.path.exists(s_path):
                        sfx = AudioFileClip(s_path)
                        # SFX usually have their own timing, but for this generic mixer
                        # we'll just add them at the start or random intervals if not specified.
                        # For now, just add them at the start.
                        sfx = sfx.with_effects([afx.AudioVolume(self.sfx_volume)])
                        clips.append(sfx)

            # 4. Mix
            final_audio = CompositeAudioClip(clips)

            # 5. Export
            output_name = f"mixed_{uuid.uuid4().hex[:8]}.mp3"
            output_path = os.path.join(os.path.dirname(voice_path), output_name)
            final_audio.write_audiofile(output_path)

            # Cleanup
            voice.close()
            if "bg" in locals():
                bg.close()
            final_audio.close()

            return output_path

        except Exception as e:
            logger.exception(f"[SoundDesign] Error mixing audio: {e}")
            if "voice" in locals():
                voice.close()
            return voice_path  # Fallback to original voiceover

    def get_available_moods(self) -> list[str]:
        """Get list of available mood categories"""
        return list(
            {mood for moods in self.NICHE_MOOD_MAP.values() for mood in moods}
        )

    def get_available_sfx_types(self) -> list[str]:
        """Get list of available SFX categories"""
        return list(self.SFX_CATEGORIES.keys())


# Global instance
sound_design_service = SoundDesignService()
