"""
Video Lead Discovery Service
============================
Advanced video content discovery and analysis for viral content creation.
Finds trending videos, analyzes performance patterns, and identifies repurposing opportunities.
"""

import logging
import asyncio
from collections import defaultdict
import httpx
from typing import Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re
import json
import random

from src.api.utils.vault import get_secret
from groq import Groq
logger = logging.getLogger(__name__)

DEFAULT_VIDEO_CODEC = "H.264/AAC"
JSON_MARKDOWN_BLOCK = "```json"
MARKDOWN_BLOCK = "```"
HOW_TO_LITERAL = "how to"


@dataclass
class VideoLead:
    """Represents a discovered video lead with performance metrics"""

    video_id: str
    platform: str
    title: str
    creator: str
    url: str
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    duration_seconds: int  # seconds
    published_at: datetime
    thumbnail_uri: str
    description: str
    tags: list[str]
    engagement_score: float
    viral_score: float
    niche: str
    content_type: str  # 'educational', 'entertainment', 'tutorial', etc.
    monetization_potential: str  # 'high', 'medium', 'low'
    relevance_score: float = 0.0


class VideoLeadScanner:
    """Advanced video content discovery and analysis service with fallback to non-ML methods"""

    def __init__(self):
        self.youtube_api_key = get_secret("youtube_api_key")
        self.tiktok_api_key = get_secret("tiktok_api_key")
        groq_api_key = get_secret("groq_api_key")
        if groq_api_key:
            try:
                import httpx
                # Explicitly create client to avoid 'proxies' keyword bug in some groq/httpx versions
                http_client = httpx.Client(timeout=60.0)
                self.groq_client = Groq(api_key=groq_api_key, http_client=http_client)
            except Exception:
                logger.exception("Failed to initialize Groq client")
                self.groq_client = None
        else:
            self.groq_client = None

        # Platform-specific configurations
        self.platform_configs = {
            "youtube": {
                "base_url": "https://www.googleapis.com/youtube/v3",
                "max_results": 50,
                "viral_threshold": 100000,  # views for viral consideration
            },
            "tiktok": {
                "base_url": "https://open-api.tiktok.com",
                "max_results": 30,
                "viral_threshold": 50000,
            },
            "instagram": {
                "max_results": 30,
                "viral_threshold": 25000,
            },
        }

        # Check available capabilities
        self.ai_available = self.groq_client is not None
        self.logger = logging.getLogger(__name__)
        self.process_semaphore = asyncio.Semaphore(5)
        self._rate_limit_delay = 1.0  # Minimum seconds between yt-dlp requests
        self._last_request_time = 0.0

        if not self.ai_available:
            self.logger.info(
                "AI services not available - using keyword-based content matching"
            )

    async def scan_for_video_leads(
        self,
        niche: str,
        platforms: list[str] = None,
        min_viral_score: float = 7.0,
        max_results: int = 20,
    ) -> list[VideoLead]:
        """
        Discover high-performing video content leads across platforms.
        """
        if platforms is None:
            platforms = ["youtube", "tiktok"]

        try:
            # 1. Primary Concurrent Scan
            all_leads = await self._gather_platform_leads(niche, platforms)
            self.logger.info(f"Primary scan complete. Leads found: {len(all_leads)}")

            # 2. Fallback if primary scanners failed or returned nothing
            if not all_leads:
                all_leads = await self._run_fallback_scan(niche, niche)

            # 2.5 Canonical Deduplication
            all_leads = self._deduplicate_leads(all_leads)

            # 3. Filter and Rank
            filtered_leads = [
                lead for lead in all_leads if lead.viral_score >= min_viral_score
            ]
            filtered_leads.sort(key=lambda x: x.viral_score, reverse=True)

            return filtered_leads[:max_results]
        except asyncio.CancelledError:
            self.logger.warning("scan_for_video_leads execution cancelled")
            raise

    def _deduplicate_leads(self, leads: list[VideoLead]) -> list[VideoLead]:
        """Deduplicate gathered platform leads based on canonical video ID and URL keys."""
        seen_ids = set()
        seen_urls = set()
        deduped = []
        for lead in leads:
            clean_url = lead.url.strip().lower() if lead.url else ""
            if lead.video_id and lead.video_id in seen_ids:
                continue
            if clean_url and clean_url in seen_urls:
                continue
            if lead.video_id:
                seen_ids.add(lead.video_id)
            if clean_url:
                seen_urls.add(clean_url)
            deduped.append(lead)
        return deduped

    async def _gather_platform_leads(self, niche: str, platforms: list[str]) -> list[VideoLead]:
        """Orchestrate concurrent scans across specified platforms."""
        tasks = []
        for platform in platforms:
            method_name = f"_scan_{platform}"
            if hasattr(self, method_name):
                tasks.append(getattr(self, method_name)(niche))

        if not tasks:
            return []

        platform_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_leads = []
        for result in platform_results:
            if isinstance(result, list):
                all_leads.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Platform scan task failed: {result}")

        return all_leads

    async def _run_fallback_scan(self, query: str, niche: str) -> list[VideoLead]:
        """DuckDuckGo scraping fallback for when primary APIs are down or capped."""
        self.logger.info(f"Failing back to DuckDuckGo search for: {query}")
        try:
            from .duckduckgo_scanner import base_duckduckgo_service
            ddg_candidates = await base_duckduckgo_service.scan_trends(query)

            leads = []
            for c in ddg_candidates:
                # Some scanners return 'general' category, we want videos
                if getattr(c, "category", "video") == "video":
                    lead = self._map_candidate_to_lead(c, niche)
                    leads.append(lead)

            self.logger.info(f"DuckDuckGo fallback found {len(leads)} leads")
            return leads
        except Exception:
            self.logger.exception("DuckDuckGo fallback failed")
            return []

    def _map_candidate_to_lead(self, c: Any, niche: str) -> VideoLead:
        """Map a generic ContentCandidate to a specialized VideoLead."""
        # Normalize viral score to 0-10 range if it comes in raw (0-100)
        v_score = c.viral_score / 10.0 if c.viral_score > 10 else c.viral_score

        return VideoLead(
            video_id=c.id,
            platform=c.platform.lower(),
            title=c.title,
            creator=getattr(c, "creator_name", "Unknown"),
            url=c.source_uri,
            view_count=c.view_count,
            like_count=0,
            comment_count=0,
            share_count=0,
            duration_seconds=30,
            published_at=c.discovery_date,
            thumbnail_uri="",
            description=c.description,
            tags=c.tags,
            engagement_score=c.engagement_score,
            viral_score=v_score,
            niche=niche,
            content_type="general",
            monetization_potential="medium",
        )

    async def evaluate_video_performance(
        self, video_uri: str, niche: str
    ) -> dict[str, Any]:
        """
        Deep analysis of a specific video's performance and viral potential.

        Args:
            video_uri: URL of video to analyze
            niche: Content niche for context

        Returns:
            Detailed performance analysis
        """
        # Extract video ID and platform
        platform, video_id = self._parse_video_uri(video_uri)

        # Get basic video data
        video_data = await self._get_video_data(platform, video_id, video_uri)

        # Analyze engagement patterns
        engagement_analysis = self._analyze_engagement_patterns(video_data)

        # Identify viral factors
        viral_factors = await self._identify_viral_factors(video_data, niche)

        # Generate repurposing suggestions
        repurposing_suggestions = await self._generate_repurposing_suggestions(
            video_data, niche
        )

        return {
            "video_data": video_data,
            "engagement_analysis": engagement_analysis,
            "viral_factors": viral_factors,
            "repurposing_suggestions": repurposing_suggestions,
            "monetization_opportunities": self._assess_monetization_potential(
                video_data
            ),
            "content_template": self._extract_content_template(video_data),
        }

    async def identify_video_templates(
        self, niche: str, template_type: str = "viral", min_samples: int = 10
    ) -> dict[str, Any]:
        """
        Find successful video templates and patterns in a niche.

        Args:
            niche: Content niche
            template_type: Type of template (viral, educational, entertainment)
            min_samples: Minimum samples to analyze

        Returns:
            Template analysis with patterns and success factors
        """
        # Get high-performing videos in niche
        leads = await self.scan_for_video_leads(
            niche=niche, min_viral_score=8.0, max_results=min_samples * 2
        )

        # Analyze common patterns
        patterns = await self._analyze_video_patterns(leads[:min_samples])

        return {
            "niche": niche,
            "template_type": template_type,
            "sample_size": len(leads[:min_samples]),
            "common_patterns": patterns,
            "success_factors": self._extract_success_factors(),
            "recommended_structure": self._generate_recommended_structure(patterns),
        }

    async def _scan_youtube(self, niche: str) -> list[VideoLead]:
        """Scan YouTube for video leads"""
        if not self.youtube_api_key:
            logger.warning("YouTube API key not configured")
            return []

        leads = []

        try:
            async with httpx.AsyncClient() as client:
                # Search for trending videos in niche
                search_url = f"{self.platform_configs['youtube']['base_url']}/search"
                params = {
                    "key": self.youtube_api_key,
                    "q": f"{niche} viral trending",
                    "part": "snippet",
                    "maxResults": 25,
                    "order": "viewCount",
                    "type": "video",
                    "videoDuration": "short",  # Focus on shorts for viral potential
                }

                response = await client.get(search_url, params=params)
                search_data = response.json()

                if response.status_code != 200:
                    logger.error(
                        f"YouTube Search API Error {response.status_code}: {search_data}"
                    )
                    self.logger.debug(
                        f"YouTube API Error: {search_data.get('error', {}).get('message', 'Unknown')}. Falling back to scraper."
                    )
                    return await self._scan_youtube_scraper(niche)
                else:
                    self.logger.debug(
                        f"YouTube Search found {len(search_data.get('items', []))} items"
                    )

                video_ids = [
                    item["id"]["videoId"]
                    for item in search_data.get("items", [])
                    if "videoId" in item["id"]
                ]

                if video_ids:
                    # Get detailed stats for videos
                    stats_url = f"{self.platform_configs['youtube']['base_url']}/videos"
                    stats_params = {
                        "key": self.youtube_api_key,
                        "id": ",".join(video_ids[:10]),  # Limit to 10 for efficiency
                        "part": "statistics,contentDetails,snippet",
                    }

                    stats_response = await client.get(stats_url, params=stats_params)
                    stats_data = stats_response.json()

                    for item in stats_data.get("items", []):
                        lead = self._create_youtube_lead(item, niche)
                        if lead:
                            leads.append(lead)

        except Exception:
            self.logger.exception("YouTube scanning error")

        return leads

    async def find_videos_for_scenes(
        self,
        scenes: list[dict[str, Any]],
        niche: str,
        platforms: list[str] = None,
        quality_threshold: int = 7,
    ) -> dict[str, list[VideoLead]]:
        """
        Find high-quality videos for each scene based on content analysis.
        Works with or without AI models using keyword-based matching.

        Args:
            scenes: list of scene dictionaries with 'description', 'visual_prompt', etc.
            niche: Content niche for context
            platforms: Platforms to search (youtube, tiktok, etc.)
            quality_threshold: Minimum quality score (1-10)

        Returns:
            Dictionary mapping scene index to list of matching video leads
        """
        if platforms is None:
            platforms = ["youtube"]

        scene_videos = {}

        for i, scene in enumerate(scenes):
            self.logger.info(
                f"Searching videos for scene {i + 1}: {scene.get('description', '')[:50]}..."
            )

            # Extract search keywords from scene
            search_keywords = self._extract_scene_keywords(scene, niche)

            # Find videos matching these keywords
            matching_videos = await self._find_videos_by_keywords(
                search_keywords, platforms=platforms, min_quality=quality_threshold
            )

            # Filter and rank videos for this specific scene
            scene_matches = self._rank_videos_for_scene(matching_videos, scene)

            scene_videos[f"scene_{i + 1}"] = scene_matches[
                :5
            ]  # Top 5 matches per scene

            self.logger.info(
                f"Found {len(scene_matches)} video matches for scene {i + 1}"
            )

        return scene_videos

    def _extract_scene_keywords(self, scene: dict[str, Any], niche: str) -> list[str]:
        """Extract search keywords from scene description and visual prompts"""
        keywords = []

        # Add niche as base keyword
        keywords.append(niche.lower())

        # Extract from scene description
        description = scene.get("description", "").lower()
        visual_prompt = scene.get("visual_prompt", "").lower()

        # Common content keywords
        content_keywords = [
            "tutorial",
            "guide",
            HOW_TO_LITERAL,
            "tips",
            "tricks",
            "review",
            "demo",
            "showcase",
            "example",
            "case study",
            "interview",
            "story",
            "narrative",
            "journey",
            "experience",
            "lifestyle",
            "business",
            "entrepreneur",
            "startup",
            "technology",
            "innovation",
            "education",
            "learning",
            "skill",
            "knowledge",
            "expert",
            "professional",
            "career",
            "success",
            "achievement",
            "goal",
        ]

        # Extract matching keywords from description
        for keyword in content_keywords:
            if keyword in description or keyword in visual_prompt:
                keywords.append(keyword)

        # Extract specific terms (nouns, proper names) from raw (non-lowercased) text
        raw_description = scene.get("description", "")
        raw_visual_prompt = scene.get("visual_prompt", "")
        text = f"{raw_description} {raw_visual_prompt}"
        words = text.split()

        # Look for capitalized words (potential proper names)
        for word in words:
            word_clean = re.sub(r"[^\w]", "", word)
            if len(word_clean) > 3 and word_clean[0].isupper():
                keywords.append(word_clean.lower())

        # Add visual keywords
        visual_keywords = [
            "animation",
            "motion graphics",
            "text overlay",
            "infographic",
            "interview",
            "testimonial",
            "product demo",
            "software",
            "app",
            "website",
            "dashboard",
            "interface",
            "design",
        ]

        for keyword in visual_keywords:
            if keyword in visual_prompt:
                keywords.append(keyword)

        # Remove duplicates and return
        return list(set(keywords))[:10]  # Limit to 10 keywords

    async def _find_videos_by_keywords(
        self, keywords: list[str], platforms: list[str], min_quality: int = 7
    ) -> list[VideoLead]:
        """Find videos matching keywords across platforms"""
        # Create search query from keywords
        search_query = " ".join(keywords[:3])  # Use top 3 keywords
        niche = keywords[0] if keywords else "general"

        # 1. Primary Concurrent Scan
        all_videos = await self._gather_platform_leads(search_query, platforms)

        # 2. Fallback
        if not all_videos:
            all_videos = await self._run_fallback_scan(search_query, niche)

        # 3. Filter by quality
        quality_videos = [
            video
            for video in all_videos
            if self._calculate_viral_score(video.view_count, video.engagement_score)
            >= min_quality
        ]

        return quality_videos

    def _rank_videos_for_scene(
        self, videos: list[VideoLead], scene: dict[str, Any]
    ) -> list[VideoLead]:
        """Rank videos by relevance to specific scene"""
        if not videos:
            return []

        scene_keywords = self._extract_scene_keywords(scene, "")

        ranked_videos = []
        for video in videos:
            relevance_score = self._calculate_scene_relevance(video, scene_keywords)
            video.relevance_score = relevance_score
            ranked_videos.append(video)

        # Sort by relevance score descending
        ranked_videos.sort(key=lambda x: getattr(x, "relevance_score", 0), reverse=True)

        return ranked_videos

    def _calculate_scene_relevance(
        self, video: VideoLead, scene_keywords: list[str]
    ) -> float:
        """Calculate how relevant a video is to a scene"""
        relevance = 0.0

        # Check title relevance
        title_lower = video.title.lower()
        for keyword in scene_keywords:
            if keyword in title_lower:
                relevance += 0.3

        # Check description relevance
        desc_lower = video.description.lower()
        for keyword in scene_keywords:
            if keyword in desc_lower:
                relevance += 0.2

        # Check tags relevance
        for tag in video.tags:
            tag_lower = tag.lower()
            for keyword in scene_keywords:
                if keyword in tag_lower:
                    relevance += 0.4

        # Quality bonus
        quality_score = self._calculate_viral_score(
            video.view_count, video.engagement_score
        )
        relevance += (quality_score / 10) * 0.1  # 10% weight for quality

        return min(relevance, 1.0)  # Cap at 1.0

    async def create_scene_based_video(
        self,
        scenes: list[dict[str, Any]],
        niche: str,
        target_duration: int = 60,
        audio_script: str = None,
    ) -> dict[str, Any]:
        """
        Create a complete video production plan with scene-matched videos.
        Includes fusion strategy and upload specifications.
        """
        # Find videos for each scene
        scene_videos = await self.find_videos_for_scenes(
            scenes=scenes, niche=niche, quality_threshold=7
        )

        # Create fusion strategy
        fusion_plan = self._create_fusion_strategy(
            scene_videos, target_duration, scenes
        )

        # Add audio overlay plan
        audio_plan = self._create_audio_overlay_plan(audio_script, fusion_plan)

        # Create upload specifications
        upload_specs = self._create_upload_specifications()

        return {
            "scenes": scenes,
            "scene_videos": scene_videos,
            "fusion_plan": fusion_plan,
            "audio_plan": audio_plan,
            "upload_specs": upload_specs,
            "estimated_duration": fusion_plan.get("total_duration", 0),
            "quality_score": self._calculate_overall_quality(scene_videos, fusion_plan),
            "production_ready": len(scene_videos) > 0,
        }

    def _create_fusion_strategy(
        self,
        scene_videos: dict[str, list[VideoLead]],
        target_duration: int,
        scenes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create video fusion strategy from scene videos"""
        total_duration = 0
        fusion_segments = []

        num_scenes = len(scene_videos)
        for i, (scene_key, videos) in enumerate(scene_videos.items()):
            scene_data = scenes[i] if i < len(scenes) else {}

            # Skip if we have no media sources for this scene
            if not (scene_data.get("video_path") or scene_data.get("source_uri") or videos):
                continue

            segment = self._create_fusion_segment(
                i, scene_key, videos, scene_data, target_duration, num_scenes, total_duration
            )
            fusion_segments.append(segment)
            total_duration += segment["duration"]

        return {
            "segments": fusion_segments,
            "total_duration": total_duration,
            "transitions": ["fade", "slide", "crossfade"],
            "effects": ["color_grading", "text_overlays"],
            "output_format": "mp4",
            "resolution": "1920x1080",
            "frame_rate": 30,
        }

    def _create_fusion_segment(
        self,
        index: int,
        scene_key: str,
        videos: list[VideoLead],
        scene_data: dict[str, Any],
        target_duration: int,
        num_scenes: int,
        current_total_duration: int
    ) -> dict[str, Any]:
        """Create a single fusion segment with calculated timing and source data."""
        best_video = videos[0] if videos else None

        # Determine segment duration
        duration = scene_data.get("duration")
        if not duration:
            # Fallback: Use video duration or proportional split
            duration = best_video.duration_seconds if best_video else target_duration // max(1, num_scenes)

        return {
            "scene": scene_key,
            "type": scene_data.get("type", "content"),
            "video_id": best_video.video_id if best_video else f"custom_{index}",
            "platform": best_video.platform if best_video else "custom",
            "url": scene_data.get("source_uri") or (best_video.url if best_video else None),
            "video_path": scene_data.get("video_path"),
            "duration": duration,
            "start_time": current_total_duration,
            "visual_prompt": scene_data.get("visual_prompt"),
            "transition": self._get_transition_for_type(
                scene_data.get("type", "content")
            )
        }

    def _create_audio_overlay_plan(
        self, audio_script: str, fusion_plan: dict[str, Any]
    ) -> dict[str, Any]:
        """Create audio overlay plan for the video"""
        segments = fusion_plan.get("segments", [])

        audio_segments = []
        current_time = 0

        if audio_script:
            # Estimate timing based on script length and segments
            script_words = len(audio_script.split())
            words_per_minute = 150  # Average speaking rate

            for segment in segments:
                segment_duration = segment["duration"]
                segment_words = int((segment_duration / 60) * words_per_minute)

                audio_segments.append(
                    {
                        "start_time": current_time,
                        "duration": segment_duration,
                        "text": audio_script[:segment_words]
                        if script_words > segment_words
                        else audio_script,
                        "voice_type": "professional_female",
                        "background_music": "uplifting_corporate",
                    }
                )

                current_time += segment_duration

        return {
            "audio_segments": audio_segments,
            "background_music": "corporate_uplifting",
            "voice_over": bool(audio_script),
            "total_audio_duration": current_time,
            "format": "aac",
            "bitrate": "128k",
        }

    def _create_upload_specifications(self) -> dict[str, Any]:
        """Create upload specifications for various platforms"""
        return {
            "platforms": {
                "youtube": {
                    "format": "mp4",
                    "resolution": "1920x1080",
                    "max_size": "2GB",
                    "codecs": DEFAULT_VIDEO_CODEC,
                    "aspect_ratio": "16:9",
                },
                "tiktok": {
                    "format": "mp4",
                    "resolution": "1080x1920",
                    "max_duration": "180s",
                    "codecs": DEFAULT_VIDEO_CODEC,
                    "aspect_ratio": "9:16",
                },
                "instagram": {
                    "format": "mp4",
                    "resolution": "1080x1080",
                    "max_duration": "90s",
                    "codecs": DEFAULT_VIDEO_CODEC,
                    "aspect_ratio": "1:1",
                },
            },
            "seo_tags": self._generate_seo_tags(),
            "thumbnails": {"count": 3, "specs": "1280x720, JPG, <2MB"},
            "metadata": {
                "title_template": "{niche} - {key_benefits}",
                "description_template": "Learn about {niche} with this comprehensive guide...",
                "hashtags": self._generate_hashtags(),
            },
        }

    def _calculate_overall_quality(
        self, scene_videos: dict[str, list[VideoLead]], fusion_plan: dict[str, Any]
    ) -> float:
        """Calculate overall production quality score"""
        if not scene_videos:
            return 0.0

        # Average quality of selected videos
        total_quality = 0
        total_videos = 0

        for videos in scene_videos.values():
            if videos:
                best_video = videos[0]
                quality = self._calculate_viral_score(
                    best_video.view_count, best_video.engagement_score
                )
                total_quality += quality
                total_videos += 1

        avg_video_quality = total_quality / total_videos if total_videos > 0 else 0

        # Fusion plan quality (based on completeness)
        fusion_completeness = (
            len(fusion_plan.get("segments", [])) / len(scene_videos)
            if scene_videos
            else 0
        )

        # Overall score (70% video quality, 30% production planning)
        overall_score = (avg_video_quality * 0.7) + (fusion_completeness * 10 * 0.3)

        return min(overall_score, 10.0)

    def _generate_seo_tags(self) -> list[str]:
        """Generate SEO tags for the video"""
        return ["viral", "content", "tutorial", "guide", "tips", "howto"]

    def _generate_hashtags(self) -> list[str]:
        """Generate relevant hashtags"""
        return ["#viral", "#content", "#tutorial", "#guide", "#tips"]

    async def _scan_tiktok(self, _niche: str) -> list[VideoLead]:
        """Scan TikTok for video leads"""
        # TikTok scanning would require their API
        # For now, return empty list with note
        await asyncio.sleep(0)
        logger.info("TikTok scanning requires API integration")
        return []

    async def _scan_with_ytdlp(
        self, query: str, platform: str, max_results: int = 5
    ) -> list[VideoLead]:
        """Generic yt-dlp scraper for multi-platform support."""
        # 1. Sanitize query to prevent command injection / shell exploits
        clean_query = re.sub(r"[^a-zA-Z0-9\s\-_.,!?]", "", query)[:200]
        self.logger.info(f"Scraping {platform} for: {clean_query}")

        cmd = self._build_ytdlp_command(clean_query, platform, max_results)
        output = await self._execute_ytdlp_process(cmd, platform)

        if not output:
            return []

        leads = []
        for line in output.split("\n"):
            lead = self._parse_ytdlp_output_line(line, platform, clean_query)
            if lead:
                leads.append(lead)
        return leads

    def _build_ytdlp_command(
        self, query: str, platform: str, max_results: int
    ) -> list[str]:
        """Build the yt-dlp command for searching with structured JSON output"""
        search_prefixes = {
            "youtube": f"ytsearch{max_results}:",
            "tiktok": f"ytsearch{max_results}:tiktok ",
            "reddit": f"ytsearch{max_results}:reddit ",
            "rumble": f"ytsearch{max_results}:rumble ",
            "bilibili": f"ytsearch{max_results}:bilibili ",
            "instagram": f"ytsearch{max_results}:instagram reel ",
            "facebook": f"ytsearch{max_results}:facebook ",
            "twitch": f"ytsearch{max_results}:twitch ",
            "pinterest": f"ytsearch{max_results}:pinterest ",
            "trends": f"ytsearch{max_results}:trending {datetime.now().year} ",
        }
        prefix = search_prefixes.get(platform, f"ytsearch{max_results}:")

        return [
            "yt-dlp",
            "-j",
            "--flat-playlist",
            "--no-download",
            f"{prefix}{query}",
        ]

    async def _execute_ytdlp_process(self, cmd: list[str], platform: str) -> str:
        """Execute yt-dlp command and return stdout with leaky bucket rate limiting + jitter"""
        # Leaky bucket rate limiter with jitter to prevent thundering herd
        now = asyncio.get_running_loop().time()
        elapsed = now - self._last_request_time
        min_interval = self._rate_limit_delay  # seconds
        if elapsed < min_interval:
            jitter = 0.5  # randomness to prevent sync issues
            wait_time = min_interval - elapsed + (jitter * (2 * __import__("random").random() - 1))
            if wait_time > 0:
                self.logger.info(f"Rate limiting: sleeping for {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        self._last_request_time = asyncio.get_running_loop().time()

        async with self.process_semaphore:
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    self.logger.error(f"ytdlp {platform} process timed out after 30s")
                    return ""

                if process.returncode != 0:
                    self.logger.error(f"ytdlp {platform} search failed: {stderr.decode()}")
                    return ""

                return stdout.decode().strip()
            except OSError as e:
                self.logger.error(f"ytdlp system execution error: {e}")
                return ""
            except Exception:
                self.logger.exception(f"ytdlp {platform} execution failed due to an unexpected error")
                return ""

    def _parse_ytdlp_output_line(
        self, line: str, platform: str, query: str
    ) -> Optional[VideoLead]:
        """Parse a single line of structured JSON yt-dlp output into a VideoLead"""
        if not line or not line.strip():
            return None

        try:
            data = json.loads(line)
            v_id = data.get("id") or ""
            v_title = data.get("title") or "Unknown Title"
            v_uploader = data.get("uploader") or "Unknown"
            v_views = data.get("view_count")
            v_url = data.get("webpage_url") or data.get("url") or f"https://www.youtube.com/watch?v={v_id}"

            # Duration parsing
            v_dur_val = data.get("duration")
            v_dur = float(v_dur_val) if v_dur_val is not None else 30.0

            # Upload date extraction
            v_date_str = data.get("upload_date")
            try:
                v_date = datetime.strptime(v_date_str, "%Y%m%d") if v_date_str else datetime.now()
            except Exception:
                v_date = datetime.now()

            v_desc = data.get("description") or ""
            views = int(v_views) if v_views is not None else 10000

            return VideoLead(
                video_id=v_id,
                platform=platform,
                title=v_title,
                creator=v_uploader,
                url=v_url,
                view_count=views,
                like_count=int(views * 0.05),
                comment_count=int(views * 0.01),
                share_count=int(views * 0.005),
                duration_seconds=int(v_dur),
                published_at=v_date,
                thumbnail_uri="",
                description=v_desc,
                tags=[],
                engagement_score=0.065,
                viral_score=float(self._calculate_viral_score(views, 0.065)),
                niche=query,
                content_type="video",
                monetization_potential="high",
            )
        except Exception as e:
            self.logger.warning(f"Failed to parse structured JSON yt-dlp line: {e}")
            return None

    async def _scan_youtube_scraper(self, niche: str) -> list[VideoLead]:
        return await self._scan_with_ytdlp(niche, "youtube")

    async def _scan_tiktok_scraper(self, niche: str) -> list[VideoLead]:
        return await self._scan_with_ytdlp(niche, "tiktok")

    async def _scan_rumble_scraper(self, niche: str) -> list[VideoLead]:
        return await self._scan_with_ytdlp(niche, "rumble")

    async def _scan_reddit_scraper(self, niche: str) -> list[VideoLead]:
        return await self._scan_with_ytdlp(niche, "reddit")

    async def _scan_instagram_scraper(self, niche: str) -> list[VideoLead]:
        return await self._scan_with_ytdlp(niche, "instagram")

    def _create_youtube_lead(
        self, video_data: dict, niche: str
    ) -> VideoLead | None:
        """Create VideoLead from YouTube API data"""
        try:
            stats = video_data.get("statistics", {})
            snippet = video_data.get("snippet", {})
            content_details = video_data.get("contentDetails", {})

            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))

            # Calculate engagement rate
            engagement_score = (likes + comments) / max(views, 1) * 100

            # Calculate viral score (0-10)
            viral_score = min(self._calculate_viral_score(views, engagement_score), 10.0)

            # Parse duration (PT1M30S -> 90 seconds)
            duration_str = content_details.get("duration", "PT0S")
            duration = self._parse_youtube_duration(duration_str)

            return VideoLead(
                video_id=video_data["id"],
                platform="youtube",
                title=snippet.get("title", ""),
                creator=snippet.get("channelTitle", ""),
                url=f"https://youtube.com/watch?v={video_data['id']}",
                view_count=views,
                like_count=likes,
                comment_count=comments,
                share_count=0,  # YouTube API doesn't provide shares
                duration_seconds=duration,
                published_at=self._parse_youtube_date(snippet.get("publishedAt", "")),
                thumbnail_uri=snippet.get("thumbnails", {})
                .get("high", {})
                .get("url", ""),
                description=snippet.get("description", ""),
                tags=snippet.get("tags", []),
                engagement_score=engagement_score,
                viral_score=viral_score,
                niche=niche,
                content_type=self._classify_content_type(snippet.get("title", "")),
                monetization_potential=self._assess_monetization(
                    views, engagement_score
                ),
            )

        except Exception:
            logger.exception("Error creating YouTube lead")
            return None

    def _calculate_viral_score(self, views: int, engagement_score: float) -> float:
        """
        Calculate viral potential score (0-10) using robust logarithmic view scaling
        and engagement-to-views ratio weights to give credit to highly engaging small creators.
        """
        import math
        if views <= 0:
            return 0.0

        # Adaptive logarithmic view score (log10 scaling, 1k views = 0, 10M = 5)
        # Uses same scaling as base scanner for consistency
        log_views = math.log10(views)
        view_score = min(5.0, max(0.0, (log_views - 3.0) * 1.25))

        # Engagement bonus with standardized ratio weighting (same as base scanner)
        # Normalize engagement_score to ratio (e.g. 0.065 = 6.5%)
        raw_engagement = (
            engagement_score / 100.0 if engagement_score > 1.0 else engagement_score
        )
        # High engagement bonus (up to 5.0 points): 6.5% engagement = ~2.5 points, 20%+ = 5 points
        engagement_bonus = min(5.0, raw_engagement * 25.0) if raw_engagement else 0.0

        # Final score, capped at 10.0
        return min(10.0, view_score + engagement_bonus)

    def _classify_content_type(self, title: str) -> str:
        """Classify video content type based on title"""
        title_lower = title.lower()

        if any(
            word in title_lower for word in ["tutorial", HOW_TO_LITERAL, "guide", "learn"]
        ):
            return "educational"
        elif any(
            word in title_lower for word in ["funny", "lol", "hilarious", "comedy"]
        ):
            return "entertainment"
        elif any(word in title_lower for word in ["review", "unboxing", "vs"]):
            return "review"
        elif any(word in title_lower for word in ["top 10", "best", "ranking"]):
            return "list"
        else:
            return "general"

    def _assess_monetization(self, views: int, engagement_score: float) -> str:
        """Assess monetization potential"""
        if views > 500000 and engagement_score > 5:
            return "high"
        elif views > 100000 and engagement_score > 2:
            return "medium"
        else:
            return "low"

    def _assess_monetization_potential(self, _video_data: dict) -> list[str]:
        """Assess monetization potential for the video"""
        return []

    def _get_transition_for_type(self, scene_type: str) -> str:
        """Get best transition for a given scene type"""
        transitions = {
            "intro": "fade",
            "hook": "crossfade",
            "content": "crossfade",
            "cta": "fade",
            "conclusion": "fade",
        }
        return transitions.get(scene_type, "crossfade")

    async def _analyze_video_patterns(
        self, leads: list[VideoLead]
    ) -> list[dict[str, Any]]:
        """Analyze common patterns in successful videos"""
        await asyncio.sleep(0)
        if not leads:
            return {}

        # Analyze titles for patterns
        titles = [lead.title for lead in leads]

        # Use AI to analyze patterns
        prompt = f"""
        Analyze these successful video titles and identify common patterns:

        {titles[:10]}

        Identify:
        1. Common title structures
        2. Emotional triggers used
        3. Clickbait elements
        4. Content hooks

        Provide structured analysis.
        """

        try:
            async with asyncio.timeout(30.0):
                response = await asyncio.to_thread(
                    self.groq_client.chat.completions.create,
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                )

            return {
                "ai_analysis": response.choices[0].message.content,
                "avg_duration": sum(lead.duration_seconds for lead in leads) / len(leads),
                "avg_engagement_score": sum(lead.engagement_score for lead in leads) / len(leads),
                "content_types": self._count_content_types(leads),
            }
        except asyncio.TimeoutError:
            self.logger.error("Groq AI pattern analysis timed out after 30s")
            return {}
        except Exception:
            logger.exception("Pattern analysis error")
            return {}

    def _count_content_types(self, leads: list[VideoLead]) -> dict[str, int]:
        """Count occurrences of each content type"""
        counts = {}
        for lead in leads:
            counts[lead.content_type] = counts.get(lead.content_type, 0) + 1
        return counts

    def _parse_video_uri(self, url: str) -> tuple[str, str]:
        """Parse video URL to extract platform and video ID"""
        if "youtube.com" in url or "youtu.be" in url:
            platform = "youtube"
            # Extract video ID from various YouTube URL formats
            patterns = [
                r"youtube\.com/watch\?v=([^&]+)",
                r"youtu\.be/([^?]+)",
                r"youtube\.com/embed/([^?]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return platform, match.group(1)
        elif "tiktok.com" in url:
            platform = "tiktok"
            # Extract video ID from TikTok URL
            match = re.search(r"tiktok\.com/@[^/]+/video/(\d+)", url)
            if match:
                return platform, match.group(1)

        return "unknown", ""

    async def _get_video_data(self, platform: str, video_id: str = "", video_uri: str = "") -> dict[str, Any]:
        """Get detailed video data from platform API or via yt-dlp scraping"""
        url = video_uri
        if not url and video_id:
            if platform == "youtube":
                url = f"https://www.youtube.com/watch?v={video_id}"
            elif platform == "tiktok":
                url = f"https://www.tiktok.com/embed/v2/{video_id}"

        if not url:
            return {}

        self.logger.info(f"Extracting video data for {platform} video: {url}")
        sep = "##SEP##"
        cmd = [
            "yt-dlp",
            "--print",
            f"%(id)s{sep}%(title)s{sep}%(uploader)s{sep}%(view_count)s{sep}%(like_count)s{sep}%(comment_count)s{sep}%(duration)s{sep}%(upload_date)s{sep}%(description)s",
            "--no-download",
            url
        ]

        output = await self._execute_ytdlp_process(cmd, platform)
        if not output:
            return {
                "id": video_id,
                "url": url,
                "platform": platform,
                "title": "Unknown Title",
                "creator": "Unknown Creator",
                "view_count": 0,
                "like_count": 0,
                "comment_count": 0,
                "duration": 0,
                "description": "",
                "upload_date": datetime.now().strftime("%Y%m%d")
            }

        parts = output.split(sep)
        if len(parts) < 9:
            return {
                "id": video_id,
                "url": url,
                "platform": platform,
                "title": "Unknown Title",
                "creator": "Unknown Creator",
                "view_count": 0,
                "like_count": 0,
                "comment_count": 0,
                "duration": 0,
                "description": "",
                "upload_date": datetime.now().strftime("%Y%m%d")
            }

        v_id, v_title, v_uploader, v_views, v_likes, v_comments, v_duration, v_upload_date, v_description = parts[:9]

        def safe_int(val, default=0):
            try:
                return int(val) if val and val != "None" else default
            except ValueError:
                return default

        return {
            "id": v_id,
            "url": url,
            "platform": platform,
            "title": v_title,
            "creator": v_uploader,
            "view_count": safe_int(v_views),
            "like_count": safe_int(v_likes),
            "comment_count": safe_int(v_comments),
            "duration": safe_int(v_duration),
            "description": v_description,
            "upload_date": v_upload_date
        }

    def _analyze_engagement_patterns(self, video_data: dict) -> dict[str, Any]:
        """Analyze engagement patterns over time"""
        views = video_data.get("view_count", 0)
        likes = video_data.get("like_count", 0)
        comments = video_data.get("comment_count", 0)

        engagement_score = 0.0
        like_ratio = 0.0
        comment_ratio = 0.0

        if views > 0:
            like_ratio = (likes / views) * 100
            comment_ratio = (comments / views) * 100
            engagement_score = like_ratio + (comment_ratio * 2.0)

        comments_density = "low"
        if comment_ratio > 0.5:
            comments_density = "high"
        elif comment_ratio > 0.1:
            comments_density = "medium"

        return {
            "engagement_score": round(engagement_score, 2),
            "like_ratio": round(like_ratio, 2),
            "comment_ratio": round(comment_ratio, 2),
            "views_to_likes_factor": round(views / max(1, likes), 1),
            "comments_density": comments_density
        }

    def _parse_list(self, text: str) -> Optional[list[str]]:
        """Helper to safely decode a JSON array of strings."""
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [str(item) for item in data]
        except json.JSONDecodeError:
            pass
        return None

    def _extract_json_array(self, content: str) -> list[str]:
        """
        Robustly extracts a JSON array of strings from a string.
        Handles markdown blocks, malformed wrapping, conversational prefixes, and bullet points.
        """
        content = content.strip()

        # Try direct parsing first
        parsed = self._parse_list(content)
        if parsed is not None:
            return parsed

        # Try matching ```json ... ``` blocks
        json_block_match = re.search(r"```(?:json)?\s*(\[[^\]]*\])\s*```", content, re.DOTALL)
        if json_block_match:
            parsed = self._parse_list(json_block_match.group(1))
            if parsed is not None:
                return parsed

        # Try searching for any array-like structure [ ... ] in the text
        array_match = re.search(r"(\[[^\]]*\])", content, re.DOTALL)
        if array_match:
            parsed = self._parse_list(array_match.group(1))
            if parsed is not None:
                return parsed

        # Last resort fallback: split by lines and clean up bullet point markings
        lines = content.split('\n')
        cleaned_items = []
        for line in lines:
            cleaned = re.sub(r"^[\s\-\*\d\.\"\']+", "", line).strip()
            cleaned = re.sub(r"[\"\',\]\[]+$", "", cleaned).strip()
            if cleaned:
                cleaned_items.append(cleaned)
        if cleaned_items:
            return cleaned_items

        raise ValueError("Could not extract a valid list from LLM response")

    async def _identify_viral_factors(self, video_data: dict, _niche: str) -> list[str]:
        """Identify factors that made this video viral using LLM or rule-based analysis"""
        title = video_data.get("title", "")
        description = video_data.get("description", "")
        views = video_data.get("view_count", 0)
        likes = video_data.get("like_count", 0)

        if self.groq_client:
            try:
                prompt = (
                    f"Analyze this viral video in the '{_niche}' niche and identify 3-5 specific success factors "
                    "(hooks, emotional triggers, visual style, or messaging strategy) that made it go viral.\n"
                    f"Title: {title}\n"
                    f"Views: {views}\n"
                    f"Likes: {likes}\n"
                    f"Description: {description[:500]}\n"
                    "Respond with a plain JSON list of strings."
                )

                async with asyncio.timeout(30.0):
                    chat_completion = await asyncio.to_thread(
                        self.groq_client.chat.completions.create,
                        messages=[
                            {"role": "system", "content": "You are a social media viral expert. Return only a JSON array of strings."},
                            {"role": "user", "content": prompt}
                        ],
                        model="llama3-8b-8192",
                        temperature=0.2
                    )

                content = chat_completion.choices[0].message.content
                return self._extract_json_array(content)
            except asyncio.TimeoutError:
                self.logger.error("Groq AI identify viral factors analysis timed out after 30s")
            except Exception:
                logger.exception("Failed to analyze viral factors via LLM, falling back to rule-based analysis")

        # Fallback rule-based triggers
        factors = ["High Pacing and Hook Retention"]
        title_lower = title.lower()
        if any(w in title_lower for w in ["secret", "reveal", "hide", "truth", "shock"]):
            factors.append("Curiosity Gap Trigger")
        if any(w in title_lower for w in [HOW_TO_LITERAL, "guide", "tutorial", "learn"]):
            factors.append("High Practical Utility")
        if any(w in title_lower for w in ["easy", "fast", "quick", "simple"]):
            factors.append("Frictionless Solution Hook")
        if likes > 50000:
            factors.append("Social Proof Bias")

        return factors

    async def _generate_repurposing_suggestions(
        self, video_data: dict, _niche: str
    ) -> list[str]:
        """Generate suggestions for repurposing this content"""
        title = video_data.get("title", "")

        if self.groq_client:
            try:
                prompt = (
                    "Generate 3 creative, highly actionable suggestions for a content creator to repurpose or remix "
                    f"this successful video format for their own channel in the '{_niche}' niche.\n"
                    f"Original Title: {title}\n"
                    "Respond with a plain JSON list of strings."
                )

                async with asyncio.timeout(30.0):
                    chat_completion = await asyncio.to_thread(
                        self.groq_client.chat.completions.create,
                        messages=[
                            {"role": "system", "content": "You are a content strategy consultant. Return only a JSON array of strings."},
                            {"role": "user", "content": prompt}
                        ],
                        model="llama3-8b-8192",
                        temperature=0.7
                    )

                content = chat_completion.choices[0].message.content
                return self._extract_json_array(content)
            except asyncio.TimeoutError:
                self.logger.error("Groq AI generate repurposing suggestions timed out after 30s")
            except Exception:
                logger.exception("Failed to generate repurposing suggestions via LLM, falling back")

        # Fallback suggestions
        return [
            f"Stitch the original hook and react with your own contrarian viewpoint for the '{_niche}' niche.",
            "Create a 15-second high-energy summary of the main point using sleek Outfit caption styling.",
            "Rewrite this format as a standard 'Top 3 Secrets' list video."
        ]

    def _extract_content_template(self, video_data: dict) -> dict[str, Any]:
        """Extract reusable content template"""
        duration = video_data.get("duration", 30)
        return {
            "hook_duration_seconds": min(3, max(1, int(duration * 0.1))),
            "body_duration_seconds": int(duration * 0.8),
            "cta_duration_seconds": min(5, max(2, int(duration * 0.1))),
            "visual_style": "high_contrast_aesthetic",
            "pacing_style": "fast_tempo"
        }

    def _extract_success_factors(self) -> list[str]:
        """Extract common success factors"""
        return [
            "Strong Curiosity Hook in first 3 seconds",
            "Sleek and minimalist caption animations",
            "Relatable real-world pain point presentation",
            "Clear and direct call-to-action"
        ]

    def _generate_recommended_structure(self, _patterns: dict) -> dict[str, Any]:
        """Generate recommended video structure"""
        return {
            "intro": "Bold statement hook (0-3s)",
            "body": "3 key supporting arguments with high-tempo visual pacing (3-25s)",
            "outro": "Value CTA with subscriber incentive (25-30s)"
        }

    def _parse_youtube_duration(self, duration_str: str) -> int:
        """Parse YouTube duration string (PT1M30S, PT2H10M5S) to seconds"""
        hours = re.search(r"(\d+)H", duration_str)
        minutes = re.search(r"(\d+)M", duration_str)
        seconds = re.search(r"(\d+)S", duration_str)

        total_seconds = 0
        if hours:
            total_seconds += int(hours.group(1)) * 3600
        if minutes:
            total_seconds += int(minutes.group(1)) * 60
        if seconds:
            total_seconds += int(seconds.group(1))

        return total_seconds

    def _parse_youtube_date(self, date_str: str) -> datetime:
        """Parse YouTube ISO date string"""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.now()


# Global instance
video_lead_scanner = VideoLeadScanner()
