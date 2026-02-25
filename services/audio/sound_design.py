"""
Sound Design Service - Optional Tier 3 Enhancement

Adds background music and sound effects to videos.
Disabled by default - enable via ENABLE_SOUND_DESIGN=true
"""

import os
import logging
import random
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SoundDesignService:
    """
    Optional sound design enhancement for video processing.
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
        "default": ["cinematic", "ambient", "modern"]
    }
    
    # SFX categories
    SFX_CATEGORIES = {
        "transition": ["whoosh", "swoosh", "impact"],
        "notification": ["ding", "chime", "alert"],
        "emphasis": ["beat", "pulse", "hit"],
        "ambient": ["wind", "rain", "nature"]
    }
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_SOUND_DESIGN", "false").lower() == "true"
        self.library_path = os.getenv("SOUND_LIBRARY_PATH", "/var/lib/ettametta/sounds")
        self.default_volume = float(os.getenv("MUSIC_VOLUME", "0.15"))
        self.sfx_volume = float(os.getenv("SFX_VOLUME", "0.3"))
        
        logger.info(f"[SoundDesign] Initialized - Enabled: {self.enabled}")
    
    def _get_moods_for_niche(self, niche: str) -> List[str]:
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
        mood: Optional[str] = None,
        fade_in: float = 1.0,
        fade_out: float = 2.0
    ) -> Optional[str]:
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
        
        logger.info(f"[SoundDesign] Adding background music - niche: {niche}, mood: {mood}")
        
        try:
            # Generate unique output path
            output_path = video_path.replace(".mp4", "_with_music.mp4")
            
            # For now, we'll use a placeholder since actual implementation
            # would require either:
            # 1. Local royalty-free music library
            # 2. API integration (Epidemic Sound, Artlist, etc.)
            # 3. ffmpeg with filtered audio
            
            # Check if we have a local library
            music_dir = Path(self.library_path) / mood
            if music_dir.exists():
                # Get random track from mood directory
                tracks = list(music_dir.glob("*.mp3"))
                if tracks:
                    track = random.choice(tracks)
                    logger.info(f"[SoundDesign] Using track: {track.name}")
                    # TODO: Implement actual ffmpeg mixing
                    # For now, return None to indicate enhancement not applied
                    return None
            
            # No music library - return None (graceful degradation)
            logger.warning(f"[SoundDesign] No music library found at {self.library_path}")
            return None
            
        except Exception as e:
            logger.error(f"[SoundDesign] Error adding background music: {e}")
            return None
    
    async def add_sfx(
        self,
        video_path: str,
        sfx_type: str = "transition",
        timing: Optional[List[float]] = None
    ) -> Optional[str]:
        """
        Add sound effects to a video.
        
        Args:
            video_path: Path to input video
            sfx_type: Type of SFX (transition, notification, emphasis, ambient)
            timing: List of timestamps (in seconds) when to play SFX
            
        Returns:
            Path to enhanced video with SFX, or None if disabled
        """
        if not self.enabled:
            logger.debug("[SoundDesign] Disabled, skipping SFX")
            return None
        
        logger.info(f"[SoundDesign] Adding SFX - type: {sfx_type}")
        
        try:
            # Similar to background music - requires local library or API
            output_path = video_path.replace(".mp4", "_with_sfx.mp4")
            
            sfx_dir = Path(self.library_path) / "sfx" / sfx_type
            if sfx_dir.exists():
                effects = list(sfx_dir.glob("*.mp3"))
                if effects:
                    effect = random.choice(effects)
                    logger.info(f"[SoundDesign] Using effect: {effect.name}")
                    return None
            
            logger.warning(f"[SoundDesign] No SFX library found")
            return None
            
        except Exception as e:
            logger.error(f"[SoundDesign] Error adding SFX: {e}")
            return None
    
    async def mix_audio_tracks(
        self,
        voice_path: str,
        background_path: Optional[str] = None,
        sfx_paths: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Mix multiple audio tracks together.
        
        Args:
            voice_path: Path to voiceover audio
            background_path: Path to background music
            sfx_paths: List of SFX audio paths
            
        Returns:
            Path to mixed audio file
        """
        if not self.enabled:
            return voice_path  # Return original if disabled
        
        logger.info("[SoundDesign] Mixing audio tracks")
        
        try:
            # TODO: Implement ffmpeg audio mixing
            # This would layer voice, background music, and SFX
            # with appropriate volume levels
            
            return voice_path  # Placeholder
            
        except Exception as e:
            logger.error(f"[SoundDesign] Error mixing audio: {e}")
            return voice_path  # Fallback to original
    
    def get_available_moods(self) -> List[str]:
        """Get list of available mood categories"""
        return list(set(moods for moods in self.NICHE_MOOD_MAP.values() for _ in (moods := [moods]) if isinstance(moods, list)))
    
    def get_available_sfx_types(self) -> List[str]:
        """Get list of available SFX categories"""
        return list(self.SFX_CATEGORIES.keys())


# Global instance
sound_design_service = SoundDesignService()
