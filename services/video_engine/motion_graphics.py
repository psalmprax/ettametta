"""
Motion Graphics Service - Optional Tier 3 Enhancement

Adds text animations, overlays, and motion graphics to videos.
Disabled by default - enable via ENABLE_MOTION_GRAPHICS=true
"""

import os
import logging
import random
from typing import Optional, List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class MotionGraphicsService:
    """
    Optional motion graphics enhancement for video processing.
    Adds animated text overlays, titles, and motion graphics.
    """
    
    # Text animation styles
    ANIMATION_STYLES = [
        "fade_in",
        "slide_up", 
        "scale_in",
        "typewriter",
        "bounce",
        "glitch"
    ]
    
    # Title templates by niche
    NICHE_TITLE_STYLES = {
        "finance": ["professional", "elegant", "minimal"],
        "crypto": ["modern", "digital", "glitch"],
        "motivation": ["epic", "bold", "inspirational"],
        "tech": ["futuristic", "clean", "digital"],
        "luxury": ["elegant", "sophisticated", "gold"],
        "news": ["breaking", "professional", "bold"],
        "default": ["cinematic", "modern", "clean"]
    }
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_MOTION_GRAPHICS", "false").lower() == "true"
        self.engine = os.getenv("MOTION_GRAPHICS_ENGINE", "local")
        
        logger.info(f"[MotionGraphics] Initialized - Enabled: {self.enabled}, Engine: {self.engine}")
    
    def _get_title_style_for_niche(self, niche: str) -> str:
        """Get appropriate title style for a given niche"""
        niche_lower = niche.lower()
        
        for key, styles in self.NICHE_TITLE_STYLES.items():
            if key in niche_lower:
                return random.choice(styles)
        
        return random.choice(self.NICHE_TITLE_STYLES["default"])
    
    async def add_title_sequence(
        self,
        video_path: str,
        title: str,
        subtitle: Optional[str] = None,
        style: Optional[str] = None,
        duration: float = 3.0,
        position: str = "center"  # center, top, bottom
    ) -> Optional[str]:
        """
        Add animated title sequence to video.
        
        Args:
            video_path: Path to input video
            title: Main title text
            subtitle: Optional subtitle
            style: Animation style (auto-selected if not provided)
            duration: Title display duration in seconds
            position: Title position on screen
            
        Returns:
            Path to enhanced video with title, or None if disabled
        """
        if not self.enabled:
            logger.debug("[MotionGraphics] Disabled, skipping title sequence")
            return None
        
        if not style:
            # Extract niche from video path or use default
            style = self._get_title_style_for_niche("default")
        
        logger.info(f"[MotionGraphics] Adding title - title: {title}, style: {style}")
        
        try:
            output_path = video_path.replace(".mp4", "_with_title.mp4")
            
            # Implementation would use:
            # 1. MoviePy TextClip with animation
            # 2. FFmpeg with libass for subtitles
            # 3. Template-based rendering (After Effects MOGRT)
            
            # For now, return None (graceful degradation)
            logger.warning(f"[MotionGraphics] Title sequence not implemented - requires template library")
            return None
            
        except Exception as e:
            logger.error(f"[MotionGraphics] Error adding title sequence: {e}")
            return None
    
    async def add_animated_overlay(
        self,
        video_path: str,
        text: str,
        animation_style: str = "fade_in",
        position: str = "bottom",
        timing: Optional[List[float]] = None
    ) -> Optional[str]:
        """
        Add animated text overlay at specific timestamps.
        
        Args:
            video_path: Path to input video
            text: Overlay text
            animation_style: Type of animation
            position: Screen position (top, bottom, center)
            timing: List of timestamps when to show overlay
            
        Returns:
            Path to enhanced video with overlay, or None if disabled
        """
        if not self.enabled:
            logger.debug("[MotionGraphics] Disabled, skipping overlay")
            return None
        
        logger.info(f"[MotionGraphics] Adding overlay - text: {text}, style: {animation_style}")
        
        try:
            output_path = video_path.replace(".mp4", "_with_overlay.mp4")
            
            # Implementation would use FFmpeg with complex filters
            # or moviepy TextClip compositing
            
            logger.warning(f"[MotionGraphics] Animated overlay not implemented")
            return None
            
        except Exception as e:
            logger.error(f"[MotionGraphics] Error adding overlay: {e}")
            return None
    
    async def add_watermark(
        self,
        video_path: str,
        watermark_text: str = "Created with ettametta",
        opacity: float = 0.3,
        position: str = "bottom_right"
    ) -> Optional[str]:
        """
        Add watermark to video.
        
        Args:
            video_path: Path to input video
            watermark_text: Watermark text
            opacity: Watermark opacity (0.0 - 1.0)
            position: Screen position
            
        Returns:
            Path to enhanced video with watermark
        """
        if not self.enabled:
            return video_path  # Return original if disabled
        
        logger.info(f"[MotionGraphics] Adding watermark")
        
        try:
            # Simple FFmpeg watermark implementation
            # This could be done even when service is disabled
            
            return video_path  # Placeholder
            
        except Exception as e:
            logger.error(f"[MotionGraphics] Error adding watermark: {e}")
            return video_path
    
    def get_available_styles(self) -> List[str]:
        """Get list of available animation styles"""
        return self.ANIMATION_STYLES.copy()
    
    def get_niche_styles(self, niche: str) -> List[str]:
        """Get available styles for a specific niche"""
        niche_lower = niche.lower()
        
        for key, styles in self.NICHE_TITLE_STYLES.items():
            if key in niche_lower:
                return styles
        
        return self.NICHE_TITLE_STYLES["default"]


# Global instance
motion_graphics_service = MotionGraphicsService()
