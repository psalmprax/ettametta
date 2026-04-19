"""
Video Lead Discovery Service
============================
Advanced video content discovery and analysis for viral content creation.
Finds trending videos, analyzes performance patterns, and identifies repurposing opportunities.
"""

import logging
import asyncio
import httpx
from typing import Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import json

from api.utils.vault import get_secret
from api.config import settings
from groq import Groq

logger = logging.getLogger(__name__)


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
    thumbnail_url: str
    description: str
    tags: list[str]
    engagement_score: float
    viral_score: float
    niche: str
    content_type: str  # 'educational', 'entertainment', 'tutorial', etc.
    monetization_potential: str  # 'high', 'medium', 'low'


class VideoLeadScanner:
    """Advanced video content discovery and analysis service with fallback to non-ML methods"""

    def __init__(self):
        self.youtube_api_key = get_secret("youtube_api_key")
        self.tiktok_api_key = get_secret("tiktok_api_key")
        self.groq_client = (
            Groq(api_key=get_secret("groq_api_key"))
            if get_secret("groq_api_key")
            else None
        )

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

        Args:
            niche: Content niche to search for
            platforms: list of platforms to search (youtube, tiktok, instagram)
            min_viral_score: Minimum viral score (0-10)
            max_results: Maximum leads to return

        Returns:
            list of VideoLead objects sorted by viral score
        """
        if platforms is None:
            platforms = ["youtube", "tiktok"]

        all_leads = []

        # Search each platform concurrently
        tasks = []
        for platform in platforms:
            if hasattr(self, f"_scan_{platform}"):
                tasks.append(getattr(self, f"_scan_{platform}")(niche))

        if tasks:
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in platform_results:
                if isinstance(result, list):
                    all_leads.extend(result)

        self.logger.info(f"Scan complete. Leads found so far: {len(all_leads)}")

        # ---------------------------------------------------------
        # FALLBACK: If we have no leads (e.g. Quota Exceeded), try DuckDuckGo Scraping
        # ---------------------------------------------------------
        if not all_leads:
            self.logger.info(
                "NO LEADS FOUND. Failing back to DuckDuckGo search (Quota/Network issue)"
            )
            try:
                from .duckduckgo_scanner import base_duckduckgo_scanner

                ddg_candidates = await base_duckduckgo_scanner.scan_trends(niche)
                self.logger.info(f"DuckDuckGo found {len(ddg_candidates)} candidates")

                for c in ddg_candidates:
                    if c.category == "video":
                        lead = VideoLead(
                            video_id=c.id,
                            platform=c.platform.lower(),
                            title=c.title,
                            creator=c.creator_name or "Unknown",
                            url=c.source_url,
                            view_count=c.view_count,
                            like_count=0,
                            comment_count=0,
                            share_count=0,
                            duration_seconds=30,
                            published_at=c.discovery_date,
                            thumbnail_url="",
                            description=c.description,
                            tags=c.tags,
                            engagement_score=c.engagement_score,
                            viral_score=c.viral_score / 10.0
                            if c.viral_score > 10
                            else c.viral_score,
                            niche=niche,
                            content_type="general",
                            monetization_potential="medium",
                        )
                        all_leads.append(lead)
                        print(f"DEBUG: Added DDG lead: {lead.title}")
            except Exception as fe:
                self.logger.error(f"DuckDuckGo fallback failed: {fe}")

        # Filter and rank leads
        filtered_leads = [
            lead for lead in all_leads if lead.viral_score >= min_viral_score
        ]

        # Sort by viral score descending
        filtered_leads.sort(key=lambda x: x.viral_score, reverse=True)

        return filtered_leads[:max_results]

    async def evaluate_video_performance(
        self, video_url: str, niche: str
    ) -> dict[str, Any]:
        """
        Deep analysis of a specific video's performance and viral potential.

        Args:
            video_url: URL of video to analyze
            niche: Content niche for context

        Returns:
            Detailed performance analysis
        """
        # Extract video ID and platform
        platform, video_id = self._parse_video_url(video_url)

        # Get basic video data
        video_data = await self._get_video_data(platform, video_id)

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
            "success_factors": self._extract_success_factors(leads[:min_samples]),
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
                    print(
                        f"DEBUG: YouTube API Error: {search_data.get('error', {}).get('message', 'Unknown')}. Falling back to scraper."
                    )
                    return await self._scan_youtube_scraper(niche)
                else:
                    print(
                        f"DEBUG: YouTube Search found {len(search_data.get('items', []))} items"
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
                        lead = await self._create_youtube_lead(item, niche)
                        if lead:
                            leads.append(lead)

        except Exception as e:
            logger.error(f"YouTube scanning error: {e}")

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
            "how to",
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

        # Extract specific terms (nouns, proper names)
        text = f"{description} {visual_prompt}"
        words = text.split()

        # Look for capitalized words (potential proper names)
        for word in words:
            if len(word) > 3 and word[0].isupper():
                keywords.append(word.lower())

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
        all_videos = []

        # Create search query from keywords
        search_query = " ".join(keywords[:3])  # Use top 3 keywords

        # Search each platform
        for platform in platforms:
            if hasattr(self, f"_scan_{platform}"):
                try:
                    platform_videos = await getattr(self, f"_scan_{platform}")(
                        search_query
                    )
                    all_videos.extend(platform_videos)
                except Exception as e:
                    self.logger.warning(f"Failed to search {platform}: {e}")

        # ---------------------------------------------------------
        # FALLBACK: If we have no videos (e.g. Quota Exceeded), try DuckDuckGo
        # ---------------------------------------------------------
        if not all_videos:
            print(
                f"DEBUG: Falling back to DuckDuckGo search for keywords: {search_query}"
            )
            from .duckduckgo_scanner import base_duckduckgo_scanner

            ddg_candidates = await base_duckduckgo_scanner.scan_trends(search_query)
            print(f"DEBUG: DuckDuckGo found {len(ddg_candidates)} candidates")

            for c in ddg_candidates:
                if c.category == "video":
                    print(f"DEBUG: Mapping DDG video: {c.title}")
                    all_videos.append(
                        VideoLead(
                            video_id=c.id,
                            platform=c.platform.lower(),
                            title=c.title,
                            creator=c.creator_name or "Unknown",
                            url=c.source_url,
                            view_count=c.view_count,
                            like_count=0,
                            comment_count=0,
                            share_count=0,
                            duration_seconds=30,
                            published_at=c.discovery_date,
                            thumbnail_url="",
                            description=c.description,
                            tags=c.tags,
                            engagement_score=c.engagement_score,
                            viral_score=c.viral_score / 10.0
                            if c.viral_score > 10
                            else c.viral_score,
                            niche=keywords[0] if keywords else "general",
                            content_type="general",
                            monetization_potential="medium",
                        )
                    )

        # Filter by quality
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
        upload_specs = self._create_upload_specifications(fusion_plan, audio_plan)

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

        for i, (scene_key, videos) in enumerate(scene_videos.items()):
            if videos:
                best_video = videos[0]  # Use highest-ranked video
                segment_duration = min(
                    best_video.duration_seconds, target_duration // len(scene_videos)
                )

                fusion_segments.append(
                    {
                        "scene": scene_key,
                        "type": scenes[i].get("type", "content")
                        if i < len(scenes)
                        else "content",
                        "video_id": best_video.video_id,
                        "platform": best_video.platform,
                        "duration": segment_duration,
                        "start_time": total_duration,
                        "transition": self._get_transition_for_type(
                            scenes[i].get("type", "content")
                        )
                        if i < len(scenes)
                        else "fade",
                    }
                )

                total_duration += segment_duration

        return {
            "segments": fusion_segments,
            "total_duration": total_duration,
            "transitions": ["fade", "slide", "crossfade"],
            "effects": ["color_grading", "text_overlays"],
            "output_format": "mp4",
            "resolution": "1920x1080",
            "frame_rate": 30,
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
                        if len(audio_script.split()) > segment_words
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

    def _create_upload_specifications(
        self, fusion_plan: dict[str, Any], audio_plan: dict[str, Any]
    ) -> dict[str, Any]:
        """Create upload specifications for various platforms"""
        return {
            "platforms": {
                "youtube": {
                    "format": "mp4",
                    "resolution": "1920x1080",
                    "max_size": "2GB",
                    "codecs": "H.264/AAC",
                    "aspect_ratio": "16:9",
                },
                "tiktok": {
                    "format": "mp4",
                    "resolution": "1080x1920",
                    "max_duration": "180s",
                    "codecs": "H.264/AAC",
                    "aspect_ratio": "9:16",
                },
                "instagram": {
                    "format": "mp4",
                    "resolution": "1080x1080",
                    "max_duration": "90s",
                    "codecs": "H.264/AAC",
                    "aspect_ratio": "1:1",
                },
            },
            "seo_tags": self._generate_seo_tags(fusion_plan),
            "thumbnails": {"count": 3, "specs": "1280x720, JPG, <2MB"},
            "metadata": {
                "title_template": "{niche} - {key_benefits}",
                "description_template": "Learn about {niche} with this comprehensive guide...",
                "hashtags": self._generate_hashtags(fusion_plan),
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

    def _generate_seo_tags(self, fusion_plan: dict[str, Any]) -> list[str]:
        """Generate SEO tags for the video"""
        return ["viral", "content", "tutorial", "guide", "tips", "howto"]

    def _generate_hashtags(self, fusion_plan: dict[str, Any]) -> list[str]:
        """Generate relevant hashtags"""
        return ["#viral", "#content", "#tutorial", "#guide", "#tips"]

    async def _scan_tiktok(self, niche: str) -> list[VideoLead]:
        """Scan TikTok for video leads"""
        # TikTok scanning would require their API
        # For now, return empty list with note
        logger.info("TikTok scanning requires API integration")
        return []

    async def _scan_with_ytdlp(
        self, query: str, platform: str, max_results: int = 5
    ) -> list[VideoLead]:
        """Generic yt-dlp scraper for multi-platform support."""
        self.logger.info(f"Scraping {platform} for: {query}")
        leads = []

        # Mapping platforms to yt-dlp search prefixes
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
        sep = "##SEP##"

        cmd = [
            "yt-dlp",
            "--print",
            f"%(id)s{sep}%(title)s{sep}%(uploader)s{sep}%(view_count)s{sep}%(webpage_url)s{sep}%(duration)s{sep}%(upload_date)s{sep}%(description)s",
            "--flat-playlist",
            "--no-download",
            f"{prefix}{query}",
        ]

        try:
            import asyncio

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                self.logger.error(f"ytdlp {platform} search failed: {stderr.decode()}")
                return []

            output = stdout.decode().strip()
            if not output:
                return []

            for line in output.split("\n"):
                if sep not in line:
                    continue
                parts = line.split(sep)
                if len(parts) >= 5:
                    v_id, v_title, v_uploader, v_views, v_url = parts[:5]
                    v_dur_val = parts[5].strip() if len(parts) > 5 else "30"
                    v_dur = (
                        float(v_dur_val) if v_dur_val and v_dur_val != "None" else 30.0
                    )
                    v_date_str = (
                        parts[6].strip()
                        if len(parts) > 6
                        else datetime.now().strftime("%Y%m%d")
                    )
                    v_desc = parts[7] if len(parts) > 7 else ""

                    try:
                        v_date = datetime.strptime(v_date_str, "%Y%m%d")
                    except:
                        v_date = datetime.now()

                    views = int(v_views) if v_views and v_views.isdigit() else 10000

                    leads.append(
                        VideoLead(
                            video_id=v_id,
                            platform=platform,
                            title=v_title,
                            creator=v_uploader or "Unknown",
                            url=v_url,
                            view_count=views,
                            like_count=int(views * 0.05),
                            comment_count=int(views * 0.01),
                            share_count=int(views * 0.005),
                            duration_seconds=int(v_dur),
                            published_at=v_date,
                            thumbnail_url="",
                            description=v_desc,
                            tags=[],
                            engagement_score=0.065,
                            viral_score=float(
                                self._calculate_viral_score(views, 0.065)
                            ),
                            niche=query,
                            content_type="video",
                            monetization_potential="high",
                        )
                    )
        except Exception as e:
            self.logger.error(f"ytdlp {platform} scraper exception: {e}")

        return leads

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

    async def _create_youtube_lead(
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
                thumbnail_url=snippet.get("thumbnails", {})
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

        except Exception as e:
            logger.error(f"Error creating YouTube lead: {e}")
            return None

    def _calculate_viral_score(self, views: int, engagement_score: float) -> float:
        """Calculate viral potential score (0-10)"""
        # Base score from views (logarithmic scaling)
        view_score = min(10, (views / 1000000) * 5)  # 1M views = 5 points

        # Engagement bonus
        engagement_bonus = min(5, engagement_score / 2)  # 10% engagement = 5 points

        return view_score + engagement_bonus

    def _classify_content_type(self, title: str) -> str:
        """Classify video content type based on title"""
        title_lower = title.lower()

        if any(
            word in title_lower for word in ["tutorial", "how to", "guide", "learn"]
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
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )

            return {
                "ai_analysis": response.choices[0].message.content,
                "avg_duration": sum(l.duration_seconds for l in leads) / len(leads),
                "avg_engagement_score": sum(l.engagement_score for l in leads) / len(leads),
                "content_types": self._count_content_types(leads),
            }
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            return {}

    def _count_content_types(self, leads: list[VideoLead]) -> dict[str, int]:
        """Count occurrences of each content type"""
        counts = {}
        for lead in leads:
            counts[lead.content_type] = counts.get(lead.content_type, 0) + 1
        return counts

    def _parse_video_url(self, url: str) -> tuple[str, str]:
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

    async def _get_video_data(self, platform: str, video_id: str) -> dict[str, Any]:
        """Get detailed video data from platform API"""
        # Implementation would call platform APIs
        return {}

    def _analyze_engagement_patterns(self, video_data: dict) -> dict[str, Any]:
        """Analyze engagement patterns over time"""
        return {}

    async def _identify_viral_factors(self, video_data: dict, niche: str) -> list[str]:
        """Identify factors that made this video viral"""
        return []

    async def _generate_repurposing_suggestions(
        self, video_data: dict, niche: str
    ) -> list[str]:
        """Generate suggestions for repurposing this content"""
        return []

    def _extract_content_template(self, video_data: dict) -> dict[str, Any]:
        """Extract reusable content template"""
        return {}

    def _extract_success_factors(self, leads: list[VideoLead]) -> list[str]:
        """Extract common success factors"""
        return []

    def _generate_recommended_structure(self, patterns: dict) -> dict[str, Any]:
        """Generate recommended video structure"""
        return {}

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
        except:
            return datetime.now()


# Global instance
video_lead_scanner = VideoLeadScanner()
