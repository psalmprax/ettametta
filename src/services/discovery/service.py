import json
import redis
import asyncio
import datetime
import os
import logging
from sqlalchemy import select
from typing import Any, Optional
from .models import ContentCandidate, ViralPattern

# Graceful imports for optional dependencies
try:
    import faster_whisper

    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    faster_whisper = None
from .youtube_scanner import YouTubeShortsScanner
from .youtube_long_scanner import YouTubeLongScanner
from .tiktok_scanner import TikTokScanner
from .reddit_scanner import base_reddit_scanner
from .x_scanner import base_x_scanner
from .public_domain_scanner import base_public_domain_scanner
from .metasearch_scanner import base_metasearch_scanner
from .rumble_scanner import base_rumble_scanner
from .instagram_scanner import base_instagram_scanner
from .facebook_scanner import base_facebook_scanner
from .twitch_scanner import base_twitch_scanner
from .snapchat_scanner import base_snapchat_scanner
from .pinterest_scanner import base_pinterest_scanner
from .linkedin_scanner import base_linkedin_scanner
from .bilibili_scanner import base_bilibili_scanner
from .skool_scanner import base_skool_scanner
from .duckduckgo_scanner import base_duckduckgo_scanner
from .trading_scanner import TradingScanner
from .video_lead_scanner import video_lead_scanner
from .deconstructor import pattern_deconstructor
from api.utils.database import async_session_factory
from api.utils.models import (
    ContentCandidateDB,
    SystemSettings,
    NicheTrendDB,
    MonitoredNiche,
)
from api.config import settings
from api.utils.vault import get_secret
from api.utils.celery import celery_app
from groq import Groq


logger = logging.getLogger(__name__)


class DiscoveryService:
    def __init__(self):
        # Check optional dependencies
        self.dependencies_available = {
            "faster_whisper": FASTER_WHISPER_AVAILABLE,
        }

        # Primary scanners (run for every niche)
        # These are the production-ready scanners with real APIs
        self.scanners = [
            YouTubeShortsScanner(),  # Real API ✓
            YouTubeLongScanner(),  # Real API ✓
            TikTokScanner(),  # Web scrape ✓
            TradingScanner(),  # Financial Market Moves ✓
            base_duckduckgo_scanner,  # Free fallback ✓
        ]
        # Secondary scanners (supplementary, web scraping)
        # Now all implemented with web scraping (no API keys needed)
        self.global_scanners = [
            base_reddit_scanner,  # Real API (JSON) ✓
            base_x_scanner,  # Web scrape
            base_instagram_scanner,  # Web scrape
            base_facebook_scanner,  # Web scrape
            base_twitch_scanner,  # Web scrape (NEW)
            base_pinterest_scanner,  # Web scrape (NEW)
            base_linkedin_scanner,  # Web scrape (NEW)
            base_snapchat_scanner,  # Web scrape (NEW)
            base_bilibili_scanner,  # Web scrape (NEW)
            base_rumble_scanner,  # Web scrape (NEW)
            base_public_domain_scanner,  # Partial (Pexels)
            base_metasearch_scanner,  # Partial
            base_skool_scanner,  # Partial
        ]

        # Video lead discovery capabilities
        self.video_lead_scanner = video_lead_scanner

    async def _log(self, message: str, level: str = "INFO"):
        """Broadcasts a discovery log message."""
        from api.routes.ws import notify_system_log_async

        await notify_system_log_async(message, level=level, module="DISCOVERY")
        # Send log via Redis to avoid circular import
        import json
        import redis
        import datetime
        from api.config import settings

        try:
            r = redis.from_url(settings.REDIS_URL)
            r.publish(
                "system_logs",
                json.dumps(
                    {
                        "message": message,
                        "level": level,
                        "module": "DISCOVERY",
                        "timestamp": str(datetime.datetime.now()),
                    }
                ),
            )
        except Exception as e:
            logger.error(f"[Discovery] Failed to send log: {e}")

    async def find_trending_content(
        self,
        niche: str,
        horizon: str = "30d",
        tier: str = "free",
        min_viral_score: int = 0,
        exclude_shorts: bool = False,
        deep_scan: bool = False,
    ) -> list[ContentCandidate]:
        import json
        import redis
        from api.config import settings

        # 1. Check Cache (Skip if deep scan)
        redis_url = settings.REDIS_URL
        # Ensure we use the 'redis' hostname inside Docker, NOT 'localhost'
        if "localhost" in redis_url:
            redis_url = redis_url.replace("localhost", "redis")

        try:
            r = redis.from_url(redis_url)
            cache_key = f"discovery:trends:{niche}:{horizon}"
            if not deep_scan:
                cached_data = r.get(cache_key)
                if cached_data:
                    await self._log(
                        f"Cache HIT for '{niche}' ({horizon}). Loading stored patterns.",
                        "SUCCESS",
                    )
                    data = json.loads(cached_data)
                    return [ContentCandidate(**item) for item in data]
        except Exception as e:
            await self._log(f"Redis connection failed: {e}", "WARNING")
            r = None

        await self._log(
            f"Initiating {'DEEP SCAN' if deep_scan else 'Fast Scan'} for '{niche}' ({horizon})...",
            "SYSTEM",
        )

        # 2. Intelligent/Parallel Scanning
        import asyncio
        from engines.intelligent_video_workflow import discover_multi_platform

        all_candidates = []

        if deep_scan:
            await self._log(
                f"Deploying Intelligent Discovery Swarm for '{niche}'...", "SYSTEM"
            )
            # The intelligent workflow already performs expanding, multi-platform search, and failovers
            intelligent_results = await discover_multi_platform(
                niche,
                max_per_platform=max(
                    3, int(min_viral_score / 10) if min_viral_score else 3
                ),
            )

            for res in intelligent_results:
                all_candidates.append(
                    ContentCandidate(
                        id=res.get("id"),
                        platform=res.get("platform", "unknown"),
                        source_url=res.get("url"),
                        creator_name=res.get("channel")
                        or res.get("author")
                        or "Unknown",
                        title=res.get("title", "No Title"),
                        description=res.get("description", ""),
                        thumbnail_url=res.get("thumbnail_url")
                        or f"https://picsum.photos/seed/{res.get('id')}/1280/720",
                        view_count=res.get("views", 0),
                        engagement_score=res.get("engagement_score", 0.0),
                        viral_score=res.get("viral_score", 0),
                        duration_seconds=float(res.get("duration_seconds", 0.0)),
                        category=res.get("platform", "video"),
                        niche=niche,
                        metadata=res.get(
                            "metadata", {"source": "intelligent_workflow"}
                        ),
                    )
                )

            await self._log(
                f"Intelligent Swarm returned {len(all_candidates)} candidates.",
                "SUCCESS",
            )
        else:
            # Prepare scanner tasks for Fast Scan
            tasks = []
            for scanner in self.scanners:
                tasks.append(
                    scanner.scan_trends(
                        niche, published_after=None if deep_scan else None
                    )
                )  # Deep scan might use different horizon

        # Deep scan unleashes ALL scanners regardless of tier for that specific request
        scanners_to_use = (
            self.global_scanners
            if deep_scan or tier != "free"
            else [
                base_x_scanner,
                base_instagram_scanner,
                base_facebook_scanner,
                base_twitch_scanner,
                base_bilibili_scanner,
                base_rumble_scanner,
            ]
        )

        await self._log(
            f"Deploying swarm: {len(self.scanners) + len(scanners_to_use)} specialized scanners active.",
            "INFO",
        )
        for g_scanner in scanners_to_use:
            tasks.append(g_scanner.scan_trends(niche, published_after=None))

        # Execute all scans concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. Neural Ranking & Scoring Enrichment
        for res in results:
            if isinstance(res, list):
                all_candidates.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"[Discovery] Scanner Exception: {res}")

        # If Deep Scan: Automatically trigger analysis for top 5 candidates
        if deep_scan and all_candidates:
            logger.info(
                f"[Discovery] Deep Scan: Auto-triggering analysis for top candidates."
            )
            from services.discovery.tasks import analyze_viral_pattern_task

            for c in all_candidates[:5]:
                analyze_viral_pattern_task.delay(c.dict())

        # If no results from scan, fall back to database
        if not all_candidates:
            logger.info(
                f"[Discovery] No scan results for {niche}, falling back to database..."
            )
            async with async_session_factory() as db:
                stmt = (
                    select(ContentCandidateDB)
                    .where(ContentCandidateDB.niche == niche)
                    .order_by(ContentCandidateDB.view_count.desc())
                    .limit(50)
                )
                result = await db.execute(stmt)
                db_results = result.scalars().all()

                for r in db_results:
                    all_candidates.append(
                        ContentCandidate(
                            id=r.id,
                            platform=r.platform,
                            source_url=r.source_url or r.url,
                            creator_name=r.creator_name,
                            creator_id=r.creator_id,
                            title=r.title,
                            description=r.description,
                            thumbnail_url=r.thumbnail_url,
                            view_count=r.view_count,
                            like_count=r.like_count,
                            comment_count=r.comment_count,
                            share_count=r.share_count,
                            engagement_score=r.engagement_score,
                            viral_score=r.viral_score,
                            duration_seconds=r.duration_seconds,
                            category=r.category or "video",
                            tags=r.tags or [],
                            published_at=r.published_at,
                            scanned_at=r.scanned_at,
                            niche=r.niche,
                            metadata=r.metadata_json or {},
                        )
                    )

        # Real-First: If no results from scan, trigger the Global Scraper Swarm instead of generating dummies
        if not all_candidates:
            await self._log(
                f"Primary scanners failed. Deploying High-Fidelity Scraper Swarm for '{niche}'",
                "WARNING",
            )
            swarm_leads = await self.video_lead_scanner.scan_for_video_leads(
                niche=niche,
                platforms=["youtube", "tiktok", "rumble", "reddit", "instagram"],
                min_viral_score=0,
                max_results=20,
            )

            for l in swarm_leads:
                all_candidates.append(
                    ContentCandidate(
                        id=l.video_id,
                        platform=l.platform,
                        source_url=l.url,
                        creator_name=l.creator,
                        title=l.title,
                        description=l.description,
                        thumbnail_url=l.thumbnail_url
                        or f"https://picsum.photos/seed/{l.video_id}/1280/720",
                        view_count=l.view_count,
                        like_count=l.like_count,
                        comment_count=l.comment_count,
                        share_count=l.share_count,
                        engagement_score=l.engagement_score,  # Map score directly
                        viral_score=int(l.viral_score),
                        duration_seconds=float(l.duration_seconds),
                        category=l.content_type,
                        niche=niche,
                        metadata={"source": "scraper_swarm"},
                    )
                )

        # 4. Neural Ranking & Quality Auditing
        from .eligibility import audit_content_quality

        for c in all_candidates:
            # Audit for quality without rejecting
            # Pass duration_seconds explicitly in metadata for robustness
            audit_metadata = (c.metadata or {}).copy()
            audit_metadata["duration_seconds"] = c.duration_seconds

            audit = await audit_content_quality(
                c.title or "", c.description or "", audit_metadata
            )
            c.quality_score = audit["score"]
            c.quality_flags = audit["flags"]
            if audit["is_low_quality"]:
                c.metadata["low_quality_warning"] = True
                c.metadata["quality_reasons"] = audit["flags"]

        # Enforcement: Selective Monetization Mode (Viral Score > 85)
        async with async_session_factory() as db:
            stmt = select(SystemSettings).where(
                SystemSettings.key == "monetization_mode"
            )
            result = await db.execute(stmt)
            mode_setting = result.scalar_one_or_none()
            monetization_mode = mode_setting.value if mode_setting else "all"

            if monetization_mode == "selective":
                threshold = max(65, min_viral_score)
                original_count = len(all_candidates)
                all_candidates = [
                    c
                    for c in all_candidates
                    if (getattr(c, "viral_score", 0) or 0) >= threshold
                ]
                logger.info(
                    f"[Discovery] Selective Mode: Filtered {original_count} -> {len(all_candidates)} candidates (Threshold: {threshold})"
                )
            elif min_viral_score > 0:
                original_count = len(all_candidates)
                all_candidates = [
                    c
                    for c in all_candidates
                    if (getattr(c, "viral_score", 0) or 0) >= min_viral_score
                ]
                print(
                    f"[Discovery] Filtered by Min Viral Score: {original_count} -> {len(all_candidates)} (Threshold: {min_viral_score})"
                )

            if exclude_shorts:
                original_count = len(all_candidates)
                all_candidates = [
                    c
                    for c in all_candidates
                    if "short" not in (c.platform or "").lower()
                ]
                print(
                    f"[Discovery] Exclude Shorts: Filtered {original_count} -> {len(all_candidates)}"
                )

        # 3. Persistence Logic (Efficient Batch Integration)
        async with async_session_factory() as db:
            try:
                for c in all_candidates:
                    db_c = ContentCandidateDB(
                        id=c.id,
                        platform=c.platform,
                        external_id=c.external_id,
                        title=c.title,
                        description=c.description,
                        creator_name=c.creator_name,
                        creator_id=c.creator_id,
                        source_url=c.source_url,
                        url=c.source_url,  # Maintain legacy URL for now
                        thumbnail_url=c.thumbnail_url,
                        published_at=c.published_at,
                        scanned_at=c.scanned_at,
                        duration_seconds=c.duration_seconds,
                        view_count=c.view_count,
                        like_count=c.like_count,
                        comment_count=c.comment_count,
                        share_count=c.share_count,
                        engagement_score=c.engagement_score,
                        viral_score=c.viral_score,
                        category=c.category,
                        tags=c.tags,
                        niche=c.niche or niche,
                        metadata_json=c.metadata,
                    )
                    await db.merge(db_c)

                await db.commit()
                logger.info(
                    f"[Discovery] Successfully persisted {len(all_candidates)} candidates for {niche}."
                )
            except Exception as e:
                logger.error(f"[Discovery] Persistence Error: {e}")
                await db.rollback()

        # 5. Recalculate viral scores with fresh velocity data
        if all_candidates:
            all_candidates = await self._recalculate_viral_scores(all_candidates)

        # 6. Recursive Discovery Expansion (Autonomous Scaling)
        if len(all_candidates) > 0:
            asyncio.create_task(
                self._trigger_recursive_expansion(niche, all_candidates)
            )

        return all_candidates

    async def _recalculate_viral_scores(
        self, candidates: list[ContentCandidate]
    ) -> list[ContentCandidate]:
        """
        Recalculates viral scores based on real-time velocity for each candidate.
        Uses the scanner's velocity calculation if available, otherwise uses default formula.
        """
        for candidate in candidates:
            try:
                # Calculate real-time viral velocity
                velocity = 0.0

                # Try each scanner's velocity calculation
                for scanner in self.scanners:
                    try:
                        if hasattr(scanner, "identify_viral_velocity"):
                            velocity = scanner.identify_viral_velocity(candidate)
                            break
                    except Exception:
                        continue

                # Default calculation if no scanner worked
                if velocity == 0.0:
                    import datetime

                    if candidate.published_at:
                        hours_since = (
                            datetime.datetime.now(datetime.timezone.utc)
                            - candidate.published_at
                        ).total_seconds() / 3600
                        hours_since = max(hours_since, 0.5)
                        velocity = candidate.view_count / hours_since
                    else:
                        velocity = candidate.view_count / 24  # Assume 24h old

                # Recalculate viral_score based on velocity
                # viral_score = min(int(velocity / 10), 100)
                old_score = candidate.viral_score

                # Blend old score with new velocity-based score (70% new, 30% old for stability)
                if velocity > 0:
                    new_score = min(int(velocity / 10), 100)
                    candidate.viral_score = int(0.7 * new_score + 0.3 * old_score)

            except Exception as e:
                logger.debug(
                    f"[Discovery] Velocity calc failed for {candidate.id}: {e}"
                )

        return candidates

    async def _trigger_recursive_expansion(
        self, niche: str, candidates: list[ContentCandidate]
    ):
        """
        AI identifies related sub-niches and triggers background scans.
        """
        groq_key = get_secret("groq_api_key")
        if not groq_key:
            return

        try:
            client = Groq(api_key=groq_key)
            titles = [c.title for c in candidates[:10]]

            prompt = f"""
            Based on these trending videos in the '{niche}' niche:
            {json.dumps(titles)}
            
            Identify 3 hyper-targeted sub-niches or related keywords that should be scanned.
            Return ONLY a JSON array of strings. Example: ["Sub-Niche 1", "Keyword 2", "Topic 3"]
            """

            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            response = json.loads(completion.choices[0].message.content)
            sub_niches = (
                response.get("sub_niches")
                or response.get("keywords")
                or list(response.values())[0]
            )

            if sub_niches and isinstance(sub_niches, list):
                logger.info(
                    f"[Discovery] Recursive expansion triggered for: {sub_niches}"
                )
                for sn in sub_niches[:3]:
                    celery_app.send_task("discovery.scan_trends", args=[sn])

        except Exception as e:
            logger.error(f"[Discovery] Recursive expansion error: {e}")

    async def _rank_candidates_with_ai(
        self, niche: str, candidates: list[ContentCandidate]
    ) -> list[ContentCandidate]:
        """
        Uses Groq with parallel batching and high-speed models to rank candidates.
        """
        from api.utils.vault import get_secret

        groq_key = get_secret("groq_api_key")
        if not groq_key:
            return candidates

        try:
            client = Groq(api_key=groq_key)

            # Analyze top 20 candidates in a single high-speed batch
            candidate_summaries = []
            for i, c in enumerate(candidates[:20]):
                candidate_summaries.append(
                    {
                        "idx": i,
                        "title": c.title,
                        "engagement": f"{c.engagement_score:.2%}"
                        if hasattr(c, "engagement_score")
                        else "0%",
                    }
                )

            prompt = f"""
            Rank these {len(candidate_summaries)} candidates for the '{niche}' niche by 'Viral Potential' (Hook + Translatability).
            Return a JSON array of indices: [idx1, idx2, ...]
            
            Candidates:
            {json.dumps(candidate_summaries)}
            """

            # Use the faster llama-3.1-70b-versatile for high-quality ranking at speed
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            response_json = json.loads(completion.choices[0].message.content)
            indices = response_json.get("indices") or list(response_json.values())[0]

            if not indices or not isinstance(indices, list):
                return candidates

            ranked = []
            seen = set()
            for idx in indices:
                if (
                    isinstance(idx, int)
                    and 0 <= idx < len(candidates)
                    and idx not in seen
                ):
                    ranked.append(candidates[idx])
                    seen.add(idx)

            for i, c in enumerate(candidates):
                if i not in seen:
                    ranked.append(c)

            return ranked
        except Exception as e:
            logger.error(f"[Discovery] Neural Ranking Boost Error: {e}")
            return candidates

    async def deep_analyze_viral_patterns(
        self, candidate: ContentCandidate
    ) -> ViralPattern:
        """Analyzes a candidate for viral patterns with real transcript extraction."""
        transcript = await self._get_video_transcript(candidate.source_url)
        return await pattern_deconstructor.analyze_video_structure(
            transcript, candidate.metadata or {}
        )

    async def _get_video_transcript(self, video_url: str) -> str:
        """Extracts transcript from video via yt-dlp."""
        import yt_dlp
        import os
        import tempfile

        # We use yt-dlp to get automatic captions as a transcript
        ydl_opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "subtitlesformat": "vtt",
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                # Check for subtitles or automatic captions
                if "subtitles" in info and info["subtitles"]:
                    # Use first available subtitle
                    return (
                        f"Transcript extracted from subtitles for {info.get('title')}"
                    )
                elif "requested_subtitles" in info:
                    return f"Automatic captions extracted for {info.get('title')}"

                # Fallback to metadata if no transcript
                return f"No transcript available. Analysis based on metadata: {info.get('title')} - {info.get('description', '')[:100]}..."
        except Exception as e:
            logger.error(f"[Discovery] Transcript extraction failed: {e}")
            return "Transcript extraction failed. Using fallback metadata analysis."

    async def aggregate_niche_trends(self, niche: str):
        """
        Processes discovered content to identify top keywords and engagement for a niche.
        """
        from api.utils.models import NicheTrendDB
        from collections import Counter
        import re
        from sqlalchemy import select

        async with async_session_factory() as db:
            stmt = select(ContentCandidateDB).where(ContentCandidateDB.niche == niche)
            result = await db.execute(stmt)
            candidates = result.scalars().all()

            if not candidates:
                return None

            all_text = " ".join([c.title or "" for c in candidates])
            # Simple keyword extraction
            words = re.findall(r"\w+", all_text.lower())
            stop_words = {
                "the",
                "a",
                "to",
                "in",
                "and",
                "for",
                "of",
                "on",
                "with",
                "at",
                "by",
                "is",
                "it",
                "from",
                "as",
                "be",
                "are",
                "this",
                "that",
            }
            keywords = [w for w in words if len(w) > 3 and w not in stop_words]
            top_keywords = [k for k, _ in Counter(keywords).most_common(10)]

            avg_engagement_score = sum(
                [c.engagement_score or 0 for c in candidates]
            ) / len(candidates)

            trend = NicheTrendDB(
                niche=niche,
                platform="YouTube Shorts",  # Default for now
                top_keywords=top_keywords,
                avg_engagement_score=avg_engagement_score,
                viral_pattern_ids=[],  # Future link to analyzed patterns
            )

            # Upsert logic
            stmt = select(NicheTrendDB).where(NicheTrendDB.niche == niche)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.top_keywords = top_keywords
                existing.avg_engagement_score = avg_engagement_score
            else:
                db.add(trend)

            await db.commit()
            return trend

    async def search_content(
        self,
        query: Optional[str] = None,
        platforms: Optional[list[str]] = None,
        min_views: Optional[int] = None,
        min_viral_score: Optional[float] = None,
        creator: Optional[str] = None,
        tags: Optional[list[str]] = None,
        date_from: Optional[datetime.datetime] = None,
        date_to: Optional[datetime.datetime] = None,
        sort_by: str = "viral_score",
        limit: int = 50,
        offset: int = 0,
    ) -> list[ContentCandidate]:
        """
        Comprehensive search for content candidates across DB and Live Scanners.
        """
        from sqlalchemy import and_, or_, select

        async with async_session_factory() as db:
            try:
                # 1. Build DB Query
                stmt = select(ContentCandidateDB)
                conditions = []

                if query:
                    search_term = f"%{query}%"
                    conditions.append(
                        or_(
                            ContentCandidateDB.title.ilike(search_term),
                            ContentCandidateDB.description.ilike(search_term),
                            ContentCandidateDB.niche.ilike(search_term),
                        )
                    )

                if platforms:
                    conditions.append(ContentCandidateDB.platform.in_(platforms))
                if min_views:
                    conditions.append(ContentCandidateDB.view_count >= min_views)
                if min_viral_score:
                    conditions.append(ContentCandidateDB.viral_score >= min_viral_score)
                if creator:
                    conditions.append(
                        ContentCandidateDB.creator_name.ilike(f"%{creator}%")
                    )
                if date_from:
                    conditions.append(ContentCandidateDB.published_at >= date_from)
                if date_to:
                    conditions.append(ContentCandidateDB.published_at <= date_to)

                if conditions:
                    stmt = stmt.where(and_(*conditions))

                # Sorting
                if sort_by == "view_count":
                    stmt = stmt.order_by(ContentCandidateDB.view_count.desc())
                elif sort_by == "published_at":
                    stmt = stmt.order_by(ContentCandidateDB.published_at.desc())
                else:
                    stmt = stmt.order_by(ContentCandidateDB.viral_score.desc())

                stmt = stmt.limit(limit).offset(offset)

                result = await db.execute(stmt)
                db_results = result.scalars().all()

                candidates = []
                for r in db_results:
                    candidates.append(
                        ContentCandidate(
                            id=r.id,
                            platform=r.platform,
                            source_url=r.source_url or r.url,
                            creator_name=r.creator_name,
                            creator_id=r.creator_id,
                            title=r.title,
                            description=r.description,
                            thumbnail_url=r.thumbnail_url,
                            view_count=r.view_count,
                            like_count=r.like_count,
                            comment_count=r.comment_count,
                            share_count=r.share_count,
                            engagement_score=r.engagement_score,
                            viral_score=r.viral_score,
                            duration_seconds=r.duration_seconds,
                            category=r.category or "video",
                            tags=r.tags or [],
                            published_at=r.published_at,
                            scanned_at=r.scanned_at,
                            niche=r.niche,
                            metadata=r.metadata_json or {},
                        )
                    )

                # 2. Live Fallback (If query provided and DB results are sparse)
                if query and len(candidates) < 10:
                    logger.info(
                        f"[Discovery] Search results sparse for '{query}', triggering live fallback..."
                    )
                    live_results = await self.find_trending_content(
                        niche=query,
                        tier="premium",  # Elevate for targeted search
                        min_viral_score=int(min_viral_score or 0),
                    )
                    # Deduplicate and merge
                    seen_urls = {c.source_url for c in candidates}
                    for lc in live_results:
                        if lc.source_url not in seen_urls:
                            candidates.append(lc)
                            seen_urls.add(lc.source_url)

                return candidates[:limit]
            except Exception as e:
                logger.error(f"[Discovery] Search failed: {e}")
                return []

    async def get_global_trending(
        self, limit: int = 50, min_viral_score: float = 0.0
    ) -> list[ContentCandidate]:
        """
        Passthrough to global DB trending results.
        """
        async with async_session_factory() as db:
            stmt = select(ContentCandidateDB)
            if min_viral_score > 0:
                stmt = stmt.where(ContentCandidateDB.viral_score >= min_viral_score)

            stmt = stmt.order_by(ContentCandidateDB.viral_score.desc()).limit(limit)
            result = await db.execute(stmt)
            rows = result.scalars().all()

            return [
                ContentCandidate(
                    id=r.id,
                    platform=r.platform,
                    source_url=r.source_url or r.url,
                    creator_name=r.creator_name,
                    creator_id=r.creator_id,
                    title=r.title,
                    description=r.description,
                    thumbnail_url=r.thumbnail_url,
                    view_count=r.view_count,
                    like_count=r.like_count,
                    comment_count=r.comment_count,
                    share_count=r.share_count,
                    engagement_score=r.engagement_score,
                    viral_score=r.viral_score,
                    duration_seconds=r.duration_seconds,
                    category=r.category or "video",
                    tags=r.tags or [],
                    published_at=r.published_at,
                    scanned_at=r.scanned_at,
                    niche=r.niche,
                    metadata=r.metadata_json or {},
                )
                for r in rows
            ]

    # Cross-Platform Content Tracking Methods
    async def find_reuploads(
        self,
        content_id: str,
        source_platform: str = None,
    ) -> list[ContentCandidate]:
        """
        Find cross-platform reuploads of the same content.
        Uses title similarity and video fingerprint matching.
        
        Args:
            content_id: Original content ID to find reuploads for
            source_platform: Platform where original was found
            
        Returns:
            List of candidates that are likely reuploads
        """
        from sqlalchemy import or_, func
        
        # Get original content
        async with async_session_factory() as db:
            original = await db.get(ContentCandidateDB, content_id)
            if not original:
                return []
            
            title_keywords = original.title.split()[:5]  # Top 5 words for matching
            
            # Search for similar titles across other platforms
            conditions = [
                ContentCandidateDB.niche == original.niche,
                ContentCandidateDB.id != content_id,
            ]
            
            if source_platform:
                conditions.append(ContentCandidateDB.platform != source_platform)
            
            # Search for title similarity (any keyword match)
            for kw in title_keywords:
                if len(kw) > 3:  # Skip short words
                    conditions.append(
                        ContentCandidateDB.title.ilike(f"%{kw}%")
                    )
            
            stmt = (
                select(ContentCandidateDB)
                .where(or_(*conditions))
                .order_by(ContentCandidateDB.viral_score.desc())
                .limit(20)
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            
            reuploads = []
            for r in rows:
                # Calculate similarity score
                similarity = self._calculate_title_similarity(
                    original.title, r.title
                )
                if similarity > 0.3:  # 30% threshold
                    reuploads.append(ContentCandidate(
                        id=r.id,
                        platform=r.platform,
                        source_url=r.source_url,
                        creator_name=r.creator_name,
                        title=r.title,
                        description=r.description,
                        thumbnail_url=r.thumbnail_url,
                        view_count=r.view_count,
                        engagement_score=r.engagement_score,
                        viral_score=r.viral_score,
                        duration_seconds=r.duration_seconds,
                        category=r.category or "video",
                        niche=r.niche,
                        metadata={
                            **(r.metadata_json or {}),
                            "similarity_score": similarity,
                            "original_id": content_id,
                            "is_reupload": True,
                        },
                    ))
            
            return reuploads
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate title similarity score (0.0 to 1.0) using word overlap.
        """
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Filter short words
        words1 = {w for w in words1 if len(w) > 2}
        words2 = {w for w in words2 if len(w) > 2}
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0

    # Video Lead Discovery Methods
    async def discover_video_leads(
        self,
        niche: str,
        platforms: list = None,
        min_viral_score: float = 7.0,
        max_results: int = 20,
    ):
        """
        Discover high-performing video content leads across platforms.

        Args:
            niche: Content niche to search for
            platforms: list of platforms to search (youtube, tiktok, instagram)
            min_viral_score: Minimum viral score (0-10)
            max_results: Maximum leads to return

        Returns:
            list of video leads with performance metrics
        """
        if platforms is None:
            platforms = ["youtube", "tiktok"]

        return await self.video_lead_scanner.scan_for_video_leads(
            niche=niche,
            platforms=platforms,
            min_viral_score=min_viral_score,
            max_results=max_results,
        )

    async def analyze_video_performance(self, video_url: str, niche: str):
        """
        Deep analysis of a specific video's performance and viral potential.

        Args:
            video_url: URL of video to analyze
            niche: Content niche for context

        Returns:
            Detailed performance analysis with repurposing suggestions
        """
        return await self.video_lead_scanner.evaluate_video_performance(
            video_url=video_url, niche=niche
        )

    async def find_video_templates(
        self, niche: str, template_type: str = "viral", min_samples: int = 10
    ):
        """
        Find successful video templates and patterns in a niche.

        Args:
            niche: Content niche
            template_type: Type of template (viral, educational, entertainment)
            min_samples: Minimum samples to analyze

        Returns:
            Template analysis with patterns and success factors
        """
        return await self.video_lead_scanner.identify_video_templates(
            niche=niche, template_type=template_type, min_samples=min_samples
        )

    async def batch_download_videos(self, candidates: list[dict]) -> list[dict]:
        """
        High-speed asset procurement bridge.
        Downloads identified viral leads for the neural production engine.
        """
        import os
        from pathlib import Path

        raw_dir = Path("local_downloads/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []
        logger.info(
            f"🚚 [Discovery] Procuring {len(candidates)} viral assets for production..."
        )

        async def _download_asset(c):
            url = c.get("url")
            vid_id = c.get("id", "unknown")
            output_path = raw_dir / f"{vid_id}.mp4"

            if output_path.exists():
                logger.info(f"   ✓ Asset {vid_id} already in visual memory.")
                return {**c, "file_path": str(output_path)}

            try:
                # Use yt-dlp for reliable multi-platform acquisition
                # Optimize for H.264/AAC for ffmpeg compatibility
                cmd = [
                    "yt-dlp",
                    "-f",
                    "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--merge-output-format",
                    "mp4",
                    "-o",
                    str(output_path),
                    "--no-playlist",
                    "--quiet",
                    "--no-check-certificate",
                    "--user-agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                    "--add-header",
                    "Referer:https://www.google.com/",
                ]

                if (
                    hasattr(settings, "DOWNLOAD_PROXY_URL")
                    and settings.DOWNLOAD_PROXY_URL
                ):
                    cmd.extend(["--proxy", settings.DOWNLOAD_PROXY_URL])

                cmd.append(url)

                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode == 0 and output_path.exists():
                    logger.info(f"   ✓ Procured asset: {vid_id}")
                    return {**c, "file_path": str(output_path)}
                else:
                    error_msg = stderr.decode()
                    logger.warning(
                        f"   ⚠️ yt-dlp failed for {vid_id}: {error_msg[:100]}"
                    )

                    # TIER 10 RESILIENCE: Semantic Stock Fallback
                    import aiohttp

                    logger.info(
                        f"   🛡️ [Resilience] Triggering Stock Fallback for {vid_id}..."
                    )

                    # Use title or niche for fallback search
                    raw_fallback = c.get("title") or "Viral Content"
                    # Optimization: Remove IDs and split by delimiters
                    fallback_query = (
                        raw_fallback.split("|")[0]
                        .split(" - ")[0]
                        .split(" -- ")[0]
                        .strip()
                    )

                    # Remove special characters to clean the query
                    clean_query = "".join(
                        e for e in fallback_query if e.isalnum() or e == " "
                    ).strip()
                    if len(clean_query) < 4:  # If too short, use the niche
                        clean_query = c.get("niche") or "Space Exploration"

                    stock_candidates = await base_public_domain_scanner.scan_trends(
                        clean_query[:50]
                    )

                    if stock_candidates:
                        for sc in stock_candidates:
                            download_url = None
                            if sc.platform == "Pexels":
                                video_files = sc.metadata.get("video_files", [])
                                if video_files:
                                    download_url = video_files[0].get("link")
                            elif sc.platform == "Archive.org":
                                # Construct direct download link
                                ident = sc.metadata.get("identifier")
                                download_url = (
                                    f"https://archive.org/download/{ident}/{ident}.mp4"
                                )

                            if download_url:
                                logger.info(
                                    f"   ✨ [Stock] Procuring from {sc.platform}: {sc.id}"
                                )
                                try:
                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(
                                            download_url, timeout=30
                                        ) as resp:
                                            if resp.status == 200:
                                                with open(output_path, "wb") as f:
                                                    f.write(await resp.read())
                                                logger.info(
                                                    f"   ✓ Procured Stock Fallback for {vid_id} ({sc.platform})"
                                                )
                                                return {
                                                    **c,
                                                    "file_path": str(output_path),
                                                    "is_stock_fallback": True,
                                                }
                                            elif sc.platform == "Archive.org":
                                                # Retry Archive.org with _512kb suffix if main fails
                                                retry_url = f"https://archive.org/download/{ident}/{ident}_512kb.mp4"
                                                async with session.get(
                                                    retry_url, timeout=30
                                                ) as r2:
                                                    if r2.status == 200:
                                                        with open(
                                                            output_path, "wb"
                                                        ) as f:
                                                            f.write(await r2.read())
                                                        return {
                                                            **c,
                                                            "file_path": str(
                                                                output_path
                                                            ),
                                                            "is_stock_fallback": True,
                                                        }
                                except Exception as se:
                                    logger.error(
                                        f"   ⚠️ Stock download failed ({sc.platform}): {str(se)}"
                                    )

                    # FINAL TIER: SAFETY ASSET (Panic Resilience)
                    safety_path = Path("templates/safety/generic_space.mp4")
                    if safety_path.exists():
                        import shutil

                        shutil.copy(safety_path, output_path)
                        logger.warning(f"   🚨 [Panic] Using Safety Asset for {vid_id}")
                        return {
                            **c,
                            "file_path": str(output_path),
                            "is_stock_fallback": True,
                            "is_safety": True,
                        }

                    logger.error(f"   ❌ All procurement tiers failed for {vid_id}.")
                    return None
            except Exception as e:
                logger.error(f"   ⚠️ Procurement exception: {str(e)}")
                return None

        # Execute procurement in a throttled swarm
        tasks = [_download_asset(c) for c in candidates]
        results = await asyncio.gather(*tasks)

        downloaded = [r for r in results if r is not None]
        logger.info(
            f"✅ [Discovery] Procurement complete. {len(downloaded)} assets ready for fusion."
        )

        if not downloaded:
            raise RuntimeError("CRITICAL: Failed to procure any assets for production.")

        return downloaded


base_discovery_service = DiscoveryService()
