"""
Viral Content Discovery to AI Video Generation Pipeline
======================================================

End-to-end workflow that:
1. Discovers trending content via CloakBrowser scanner
2. Analyzes content for viral patterns using AI/NLP service  
3. Generates new AI videos based on discovered insights
4. Optional: Compiles into final video using scene orchestrator

This creates a fully automated content pipeline from discovery to creation.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.services.discovery.cloak_scanner import CloakBrowserScanner
from src.services.discovery.analysis_service import extract_content_patterns
from src.services.video_engine.free_video_providers import free_video_provider
from src.services.video_engine.scene_orchestrator import base_scene_orchestrator_service
from src.shared.state_machine import base_state_machine

logger = logging.getLogger(__name__)


class ViralContentPipeline:
    """
    End-to-end pipeline for viral content discovery → AI analysis → AI video generation.
    
    Workflow:
    1. CloakBrowser discovers trending videos from YouTube/TikTok/etc.
    2. AI Analysis Service extracts niches, sentiment, keywords from discovered content
    3. AI Video Generation creates new videos based on extracted insights
    4. Optional: Scene orchestrator compiles multiple AI-generated clips into final video
    """

    def __init__(self):
        self.cloak_scanner = CloakBrowserScanner()
        self.state_machine = base_state_machine

    async def discover_and_analyze_content(
        self, 
        niche: str, 
        max_results: int = 5,
        region: str = "US"
    ) -> List[Dict[str, Any]]:
        """
        Step 1: Discover trending content via CloakBrowser
        Step 2: Analyze discovered content for viral patterns
        
        Args:
            niche: Content niche to search (e.g., "AI productivity", "fitness tips")
            max_results: Maximum number of videos to discover and analyze
            region: Geographic region for trending content
            
        Returns:
            List of analyzed content with metadata and AI insights
        """
        logger.info(f"Starting content discovery for niche: {niche}")
        
        # Discover trending content via CloakBrowser
        discovered_content = await self.cloak_scanner.scan_trends(
            niche=niche,
            region=region,
            published_after=None  # Get recent trending content
        )
        
        if not discovered_content:
            logger.warning(f"No content discovered for niche: {niche}")
            return []
            
        # Limit results
        discovered_content = discovered_content[:max_results]
        logger.info(f"Discovered {len(discovered_content)} pieces of content")
        
        # Analyze each piece of content for viral patterns
        analyzed_content = []
        for content in discovered_content:
            try:
                # Extract AI-powered insights
                analysis_results = await extract_content_patterns(
                    content_id=content.id,
                    db=None,  # In real implementation, pass DB session
                    force=True  # Force fresh analysis
                )
                
                # Combine discovery data with analysis
                content_with_analysis = {
                    "discovered_content": content.__dict__ if hasattr(content, '__dict__') else content,
                    "analysis": analysis_results,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "pipeline_stage": "discovery_analysis_complete"
                }
                
                analyzed_content.append(content_with_analysis)
                logger.info(f"Analyzed content: {content.title} -> {analysis_results.get('niches', [])}")
                
            except Exception as e:
                logger.exception(f"Failed to analyze content {content.id}: {e}")
                continue
                
        return analyzed_content

    async def generate_ai_video_from_insights(
        self, 
        analyzed_content: Dict[str, Any],
        video_style: str = "cinematic",
        duration: int = 8
    ) -> Optional[Dict[str, Any]]:
        """
        Step 3: Generate AI video based on content analysis insights.
        
        Args:
            analyzed_content: Output from discover_and_analyze_content
            video_style: Style for AI video generation (cinematic, educational, motivational, etc.)
            duration: Target video duration in seconds
            
        Returns:
            Dict containing generated video metadata or None if failed
        """
        try:
            content_data = analyzed_content["discovered_content"]
            analysis_data = analyzed_content["analysis"]
            
            # Extract key insights for video generation
            niches = analysis_data.get("niches", ["entertainment"])
            keywords = analysis_data.get("keywords", [])
            sentiment = analysis_data.get("sentiment", "neutral")
            summary = analysis_data.get("summary", "")
            
            # Build AI video prompt from insights
            primary_niche = niches[0] if niches else "general"
            key_phrase = " ".join(keywords[:3]) if keywords else content_data.title
            
            # Create context-aware prompt based on analysis
            if sentiment == "positive":
                tone_modifier = "uplifting, positive, inspiring"
            elif sentiment == "negative":
                tone_modifier = "thought-provoking, serious, impactful"
            else:
                tone_modifier = "engaging, informative, balanced"
                
            # Construct generation prompt
            video_prompt = f"""
            Create a {video_style} video about {key_phrase} in the {primary_niche} niche.
            Tone: {tone_modifier}
            Summary: {summary}
            Target keywords: {', '.join(keywords[:5])}
            Make it engaging and shareable for social media.
            """.strip()
            
            logger.info(f"Generating AI video with prompt: {video_prompt[:100]}...")
            
            # Generate video using AI providers
            video_result = await free_video_provider.generate_video(
                prompt=video_prompt,
                duration=duration,
                aspect_ratio="9:16",  # Vertical for social media
                style=video_style
            )
            
            if video_result:
                # Enhance result with source metadata
                enhanced_result = {
                    **video_result,
                    "source_content_id": content_data.get("id"),
                    "source_title": content_data.get("title"),
                    "source_platform": content_data.get("platform"),
                    "analysis_insights": analysis_data,
                    "generation_prompt": video_prompt,
                    "pipeline_stage": "ai_video_generation_complete",
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"Successfully generated AI video: {video_result.get('provider', 'unknown')}")
                return enhanced_result
            else:
                logger.warning("AI video generation returned no result")
                return None
                
        except Exception as e:
            logger.exception(f"Failed to generate AI video from insights: {e}")
            return None

    async def discover_and_create_video(
        self,
        niche: str,
        max_discover: int = 3,
        videos_to_generate: int = 2,
        video_style: str = "cinematic"
    ) -> List[Dict[str, Any]]:
        """
        Complete end-to-end pipeline: discovery → analysis → AI video generation.
        
        Args:
            niche: Content niche to explore
            max_discover: Maximum content pieces to discover and analyze
            videos_to_generate: Number of AI videos to generate from top insights
            video_style: Style for AI video generation
            
        Returns:
            List of generated video results with full metadata
        """
        logger.info(f"Starting viral content pipeline for niche: {niche}")
        
        # Step 1-2: Discover and analyze content
        analyzed_content = await self.discover_and_analyze_content(
            niche=niche,
            max_results=max_discover
        )
        
        if not analyzed_content:
            logger.error("No content discovered and analyzed")
            return []
            
        # Sort by viral potential (high to low) to prioritize best content
        def viral_potential_score(item):
            potential = item["analysis"].get("viral_potential", "low")
            score_map = {"high": 3, "medium": 2, "low": 1}
            return score_map.get(potential, 1)
            
        analyzed_content.sort(key=viral_potential_score, reverse=True)
        
        # Step 3: Generate AI videos from top-performing insights
        top_content = analyzed_content[:videos_to_generate]
        generated_videos = []
        
        for i, content in enumerate(top_content):
            logger.info(f"Generating video {i+1}/{len(top_content)} from: {content['discovered_content'].get('title', 'Unknown')}")
            
            video_result = await self.generate_ai_video_from_insights(
                analyzed_content=content,
                video_style=video_style,
                duration=8
            )
            
            if video_result:
                generated_videos.append(video_result)
                
        logger.info(f"Pipeline complete: {len(generated_videos)} AI videos generated from {len(analyzed_content)} analyzed content pieces")
        return generated_videos

    async def create_compiled_video(
        self,
        niche: str,
        max_discover: int = 5,
        video_style: str = "cinematic"
    ) -> Optional[Dict[str, Any]]:
        """
        Advanced pipeline: Discover → Analyze → Generate multiple AI videos → Compile into final video.
        
        Args:
            niche: Content niche to explore
            max_discover: Number of content pieces to discover
            video_style: Style for AI video generation
            
        Returns:
            Dict containing final compiled video metadata or None
        """
        try:
            # Generate multiple AI video clips
            video_clips = await self.discover_and_create_video(
                niche=niche,
                max_discover=max_discover,
                videos_to_generate=3,  # Generate 3 clips to compile
                video_style=video_style
            )
            
            if not video_clips or len(video_clips) < 2:
                logger.warning("Insufficient video clips generated for compilation")
                return video_clips[0] if video_clips else None  # Return single clip if only one
                
            # Prepare clips for scene orchestrator
            clips_for_orchestration = []
            for clip in video_clips:
                # Extract video URI from AI generation result
                video_uri = clip.get("video_uri") or clip.get("content") or clip.get("video_path")
                if video_uri:
                    clips_for_orchestration.append({
                        "url": video_uri,
                        "duration_in_frames": 240  # 8 seconds at 30fps
                    })
                    
            if len(clips_for_orchestration) < 2:
                logger.warning("Not enough valid video clips for orchestration")
                return video_clips[0] if video_clips else None
                
            # Use scene orchestrator to compile clips into final video
            logger.info(f"Compiling {len(clips_for_orchestration)} AI video clips into final video")
            
            compilation_result = await base_scene_orchestrator_service.produce_scene_based_video(
                scenes=[{"url": clip["url"], "duration": clip["duration_in_frames"]//30} for clip in clips_for_orchestration],
                niche=niche,
                target_duration=8,  # 8 seconds per clip, so 24 seconds total for 3 clips
                audio_script=f"Engaging {niche} content compilation",
                output_filename=f"viral_compilation_{niche}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            )
            
            if compilation_result.get("success"):
                logger.info(f"Successfully compiled video: {compilation_result.get('video_path')}")
                return {
                    **compilation_result,
                    "source_clips": video_clips,
                    "pipeline_stage": "final_compilation_complete",
                    "compiled_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                logger.error(f"Video compilation failed: {compilation_result.get('error')}")
                # Fallback: return first generated clip
                return video_clips[0] if video_clips else None
                
        except Exception as e:
            logger.exception(f"Failed to create compiled video: {e}")
            return None


# Singleton instance
viral_content_pipeline = ViralContentPipeline()

# Convenience functions for external use
async def discover_analyze_and_generate(
    niche: str,
    max_discover: int = 3,
    videos_to_generate: int = 2
) -> List[Dict[str, Any]]:
    """
    Convenience function: Discover content → Analyze → Generate AI videos.
    
    Args:
        niche: Content niche to explore
        max_discover: Max content pieces to discover
        videos_to_generate: Number of AI videos to generate
        
    Returns:
        List of generated video results
    """
    return await viral_content_pipeline.discover_and_create_video(
        niche=niche,
        max_discover=max_discover,
        videos_to_generate=videos_to_generate
    )


async def discover_analyze_generate_compile(
    niche: str,
    max_discover: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Convenience function: Full pipeline discovery → analysis → generation → compilation.
    
    Args:
        niche: Content niche to explore
        max_discover: Max content pieces to discover for clip generation
        
    Returns:
        Dict containing final compiled video metadata or None
    """
    return await viral_content_pipeline.create_compiled_video(
        niche=niche,
        max_discover=max_discover
    )