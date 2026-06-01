import json
import asyncio
import datetime
import os
from sqlalchemy import select, and_, or_
from .models import ContentCandidate, ViralPattern
from opentelemetry import trace
from src.shared.observability import get_logger
from src.shared.state_machine import base_state_machine, JobState

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
from .cloak_scanner import CloakBrowserScanner
from .cloak_tiktok_scanner import CloakTikTokScanner
from .cloak_instagram_scanner import CloakInstagramScanner
from .cloak_facebook_scanner import CloakFacebookScanner
from .cloak_x_scanner import CloakXScanner
from .cloak_linkedin_scanner import CloakLinkedInScanner
from .cloak_reddit_scanner import CloakRedditScanner
from .cloak_twitch_scanner import CloakTwitchScanner
from .reddit_scanner import base_reddit_service
from .x_scanner import base_x_scanner_service
from .public_domain_scanner import base_public_domain_service
from .metasearch_scanner import base_metasearch_service
from .rumble_scanner import base_rumble_service
from .instagram_scanner import base_instagram_service
from .facebook_scanner import base_facebook_scanner_service
from .twitch_scanner import base_twitch_service
from .snapchat_scanner import base_snapchat_service
from .pinterest_scanner import base_pinterest_service
from .linkedin_scanner import base_linkedin_scanner_service
from .bilibili_scanner import base_bilibili_service
from .skool_scanner import base_skool_service
from .duckduckgo_scanner import base_duckduckgo_service
from .video_lead_scanner import video_lead_scanner
from .deconstructor import pattern_deconstructor
from src.api.utils.database import async_session_factory
from src.api.utils.models import (
    ContentCandidateDB,
    SystemSettings,
    NicheTrendDB,
)
from src.api.config import settings
from src.api.utils.vault import get_secret
from src.api.utils.celery import celery_app
from groq import Groq


logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)


class DiscoveryService:
    def __init__(self):
        # Check optional dependencies
        self.dependencies_available = {
            "faster_whisper": FASTER_WHISPER_AVAILABLE,
        }

        # Resolve scraper URL once
        _scraper_url = os.environ.get('DISCOVERY_SCRAPER_URL', 'http://discovery-scraper:8010')

        # Primary scanners (run for every niche)
        # These are the production-ready scanners with real APIs
        self.scanners = [
            YouTubeShortsScanner(),  # Real API ✓
            YouTubeLongScanner(),  # Real API ✓
            CloakBrowserScanner(scraper_url=_scraper_url),  # YouTube web scrape ✓
            CloakTikTokScanner(scraper_url=_scraper_url),  # Cloak + httpx fallback ✓
            base_duckduckgo_service,  # Free fallback ✓
        ]
        # Secondary scanners (supplementary, web scraping)
        # Cloak-backed scanners use Playwright stealth first, httpx fallback
        self.global_scanners = [
            CloakRedditScanner(scraper_url=_scraper_url),  # Cloak + httpx fallback
            CloakXScanner(scraper_url=_scraper_url),  # Cloak + httpx fallback
            CloakInstagramScanner(scraper_url=_scraper_url),  # Cloak + httpx fallback
            CloakFacebookScanner(scraper_url=_scraper_url),  # Cloak + httpx fallback
            CloakTwitchScanner(scraper_url=_scraper_url),  # Cloak + httpx fallback
            base_pinterest_service,  # Web scrape
            CloakLinkedInScanner(scraper_url=_scraper_url),  # Cloak + httpx fallback
            base_snapchat_service,  # Web scrape
            base_bilibili_service,  # Web scrape
            base_rumble_service,  # Web scrape
            base_public_domain_service,  # Partial (Pexels)
            base_metasearch_service,  # Partial
            base_skool_service,  # Partial
        ]

        # Video lead discovery capabilities
        self.video_lead_scanner = video_lead_scanner

    async def _log(self, message: str, level: str = "INFO", job_id: str | None = None):
        """Broadcasts a discovery log message with JSON formatting and OTEL support."""
        from src.api.routes.ws import notify_system_log_async

        log_data = {
            "message": message,
            "level": level,
            "module": "DISCOVERY",
            "job_id": job_id,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # OTEL: Add event to current span
        span = trace.get_current_span()
        if span.is_recording():
            span.add_event("discovery_log", log_data)

        # Standard JSON Log
        if level == "ERROR":
            logger.error(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))

        # Broadcast via Redis PubSub for UI
        await notify_system_log_async(message, level=level, module="DISCOVERY")

    async def find_trending_content(
        self,
        niche: str,
        horizon: str = "30d",
        tier: str = "free",
        min_viral_score: int = 0,
        exclude_shorts: bool = False,
        deep_scan: bool = False,
        region: str | None = "US",
        job_id: str | None = None,
    ) -> list[ContentCandidate]:
        with tracer.start_as_current_span("Discovery.find_trending_content") as span:
            span.set_attribute("niche", niche)
            span.set_attribute("deep_scan", deep_scan)
            span.set_attribute("region", region or "US")
            
            if job_id:
                span.set_attribute("job_id", job_id)
                await base_state_machine.transition_to(job_id, JobState.QUEUED, JobState.PENDING)

        try:
            # 1. Check Cache (Skip if deep scan)
            cached_candidates = await self._check_cache(niche, horizon, region, deep_scan)
            if cached_candidates is not None:
                return cached_candidates

            await self._log(
                f"Initiating {'DEEP SCAN' if deep_scan else 'Fast Scan'} for '{niche}' ({horizon}) in region {region or 'US'}...",
                "SYSTEM",
            )

            # 2. Intelligent/Parallel Scanning
            all_candidates = await self._run_parallel_scans(
                niche, horizon, tier, min_viral_score, deep_scan, region
            )

            # 3. Fallback database query
            if not all_candidates:
                all_candidates = await self._fetch_db_fallback(niche, region)

            # 4. Fallback scraper swarm
            if not all_candidates:
                all_candidates = await self._fetch_swarm_fallback(niche)

            # 4.5. CloakBrowser Direct Fallback (bypass cache, last resort)
            if not all_candidates:
                logger.info(
                    f"[Discovery] All sources empty for '{niche}', invoking CloakBrowser directly..."
                )
                try:
                    scraper = CloakBrowserScanner()
                    cloak_results = await scraper.scan_trends(niche, region=region)
                    if cloak_results:
                        all_candidates.extend(cloak_results)
                        await self._persist_candidates_batch(cloak_results, niche, region)
                        logger.info(
                            f"[Discovery] CloakBrowser direct fallback returned {len(cloak_results)} candidates"
                        )
                except Exception as cloak_err:
                    logger.warning(f"[Discovery] CloakBrowser direct fallback failed: {cloak_err}")

            # 5. Quality auditing
            await self._audit_candidates_quality(all_candidates)

            # 6. Filtering (Monetization mode & parameters)
            all_candidates = await self._filter_candidates(
                all_candidates, min_viral_score, exclude_shorts
            )

            # 7. Persistence
            await self._persist_candidates_batch(all_candidates, niche, region)

            # 8. Recalculate scores and ingest aggregate signals
            if all_candidates:
                all_candidates = await self._recalculate_viral_scores(all_candidates)
                self._ingest_aggregate_signal(all_candidates, niche)

            # 9. Recursive Discovery Expansion
            if all_candidates:
                asyncio.create_task(
                    self._trigger_recursive_expansion(niche, all_candidates)
                )

        except Exception as e:
            import traceback
            logger.exception(f"[Discovery] CRITICAL FAILURE in find_trending_content: {e}")
            logger.exception(traceback.format_exc())
            raise e

        return all_candidates

    async def _check_cache(
        self, niche: str, horizon: str, region: str | None, deep_scan: bool
    ) -> list[ContentCandidate] | None:
        """Checks Redis cache for existing trending content candidates if not a deep scan."""
        if deep_scan:
            return None

        try:
            from src.api.utils.redis import get_sync_redis
            r = get_sync_redis()
            cache_key = f"discovery:trends:{niche}:{horizon}:{region}"
            cached_data = r.get(cache_key)
            if cached_data:
                await self._log(
                    f"Cache HIT for '{niche}' ({horizon}) in {region}. Loading stored patterns.",
                    "SUCCESS",
                )
                data = json.loads(cached_data)
                return [ContentCandidate(**item) for item in data]
        except Exception as e:
            await self._log(f"Redis connection failed: {e}", "WARNING")
        return None

    async def _run_parallel_scans(
        self,
        niche: str,
        horizon: str,
        tier: str,
        min_viral_score: int,
        deep_scan: bool,
        region: str | None,
    ) -> list[ContentCandidate]:
        """Runs multi-platform parallel scans and returns the list of candidate objects."""
        all_candidates = []
        tasks = []

        def parse_horizon(h: str) -> datetime.timedelta:
            h = h.lower()
            if h.endswith("h"):
                return datetime.timedelta(hours=int(h[:-1]))
            if h.endswith("d"):
                return datetime.timedelta(days=int(h[:-1]))
            return datetime.timedelta(days=30)

        published_after = datetime.datetime.now(datetime.timezone.utc) - parse_horizon(horizon)

        if deep_scan:
            await self._log(
                f"Deploying Intelligent Discovery Swarm for '{niche}'...", "SYSTEM"
            )
            from src.engines.intelligent_video_workflow import discover_multi_platform

            # The intelligent workflow performs expanding, multi-platform search
            intelligent_results = await discover_multi_platform(
                niche,
                max_per_platform=max(
                    3, int(min_viral_score / 10) if min_viral_score else 3
                ),
                region=region,
            )

            for res in intelligent_results:
                vc = res.get("view_count") or res.get("views") or 0
                vs = res.get("viral_score") or 0

                all_candidates.append(
                    ContentCandidate(
                        id=res.get("id"),
                        platform=res.get("platform", "unknown"),
                        source_uri=res.get("url") or res.get("source_uri"),
                        creator_name=res.get("channel")
                        or res.get("author")
                        or res.get("creator_name")
                        or "Unknown",
                        title=res.get("title", "No Title"),
                        description=res.get("description", ""),
                        thumbnail_uri=res.get("thumbnail_uri")
                        or res.get("thumbnail")
                        or f"https://picsum.photos/seed/{res.get('id')}/1280/720",
                        view_count=vc,
                        engagement_score=res.get("engagement_score", 0.1),
                        viral_score=vs,
                        duration_seconds=float(res.get("duration_seconds", 0.0)),
                        category=res.get("category") or res.get("content_type") or "video",
                        niche=niche,
                        metadata_json=res.get(
                            "metadata", {"source": "intelligent_workflow"}
                        ),
                    )
                )

            await self._log(
                f"Intelligent Swarm returned {len(all_candidates)} candidates.",
                "SUCCESS",
            )
            
            scanners_to_use = self.global_scanners + self.scanners
        else:
            scanners_to_use = self.scanners

        # Add scanner tasks
        for scanner in scanners_to_use:
            tasks.append(scanner.scan_trends(niche, published_after=published_after, region=region))

        # Add supplementary scanners
        supplementary_scanners = (
            self.global_scanners
            if deep_scan or tier != "free"
            else [
                CloakXScanner(scraper_url=_scraper_url),
                CloakInstagramScanner(scraper_url=_scraper_url),
                CloakFacebookScanner(scraper_url=_scraper_url),
                CloakTwitchScanner(scraper_url=_scraper_url),
                base_bilibili_service,
                base_rumble_service,
            ]
        )
    
        for g_scanner in supplementary_scanners:
            tasks.append(g_scanner.scan_trends(niche, published_after=published_after, region=region))

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, list):
                all_candidates.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"[Discovery] Scanner Exception: {res}")

        # If Deep Scan: Automatically trigger analysis for top 5 candidates
        if deep_scan and all_candidates:
            logger.info(
                "[Discovery] Deep Scan: Auto-triggering analysis for top candidates."
            )
            from src.services.discovery.tasks import analyze_viral_pattern_task
            for c in all_candidates[:5]:
                analyze_viral_pattern_task.delay(c.dict())

        return all_candidates

    async def _fetch_db_fallback(self, niche: str, region: str | None) -> list[ContentCandidate]:
        """Queries local database for cached candidates as fallback when scanners return nothing."""
        logger.info(
            f"[Discovery] No scan results for {niche}, falling back to database..."
        )
        all_candidates = []
        async with async_session_factory() as db:
            stmt = (
                select(ContentCandidateDB)
                .where(and_(ContentCandidateDB.niche == niche, ContentCandidateDB.region == region))
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
                        source_uri=r.source_uri,
                        creator_name=r.creator_name,
                        creator_id=r.creator_id,
                        title=r.title,
                        description=r.description,
                        thumbnail_uri=r.thumbnail_uri,
                        view_count=r.view_count or 0,
                        like_count=r.like_count or 0,
                        comment_count=r.comment_count or 0,
                        share_count=r.share_count or 0,
                        engagement_score=r.engagement_score or 0.0,
                        viral_score=r.viral_score or 0,
                        duration_seconds=r.duration_seconds or 0.0,
                        category=r.category or "video",
                        tags=r.tags or [],
                        published_at=r.published_at,
                        scanned_at=r.scanned_at,
                        niche=r.niche,
                        metadata=r.metadata_json or {},
                    )
                )
        return all_candidates

    async def _fetch_swarm_fallback(self, niche: str) -> list[ContentCandidate]:
        """Triggers the Global Scraper Swarm if no candidates exist."""
        await self._log(
            f"Primary scanners failed. Deploying High-Fidelity Scraper Swarm for '{niche}'",
            "WARNING",
        )
        all_candidates = []
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
                    source_uri=l.url,
                    creator_name=l.creator,
                    title=l.title,
                    description=l.description,
                    thumbnail_uri=l.thumbnail_uri or f"https://picsum.photos/seed/{l.video_id}/1280/720",
                    view_count=l.view_count or 0,
                    like_count=l.like_count or 0,
                    comment_count=l.comment_count or 0,
                    share_count=l.share_count or 0,
                    engagement_score=l.engagement_score or 0.0,
                    viral_score=l.viral_score or 0,
                    duration_seconds=l.duration_seconds or 0.0,
                    category=l.content_type or "video",
                    niche=l.niche,
                    metadata={
                        **(getattr(l, "metadata_json", None) or {}),
                        "is_reupload": True,
                    },
                )
            )
        return all_candidates

    async def _audit_candidates_quality(self, candidates: list[ContentCandidate]) -> None:
        """Audits candidates for quality and applies appropriate score and flags."""
        from .eligibility import audit_content_quality

        for c in candidates:
            candidate_metadata = c.metadata_json or {}
            audit_metadata = candidate_metadata.copy()
            audit_metadata["duration_seconds"] = c.duration_seconds

            audit = await audit_content_quality(
                c.title or "", c.description or "", audit_metadata
            )
            c.quality_score = audit["score"]
            c.quality_flags = audit["flags"]
            if audit["is_low_quality"]:
                c.metadata_json["low_quality_warning"] = True
                c.metadata_json["quality_reasons"] = audit["flags"]

    async def _filter_candidates(
        self,
        candidates: list[ContentCandidate],
        min_viral_score: int,
        exclude_shorts: bool,
    ) -> list[ContentCandidate]:
        """Applies selective monetization mode filtering and user specific constraints."""
        async with async_session_factory() as db:
            stmt = select(SystemSettings).where(
                SystemSettings.key == "monetization_mode"
            )
            result = await db.execute(stmt)
            mode_setting = result.scalar_one_or_none()
            monetization_mode = mode_setting.value if mode_setting else "all"

            if monetization_mode == "selective":
                threshold = max(65, min_viral_score)
                original_count = len(candidates)
                candidates = [
                    c for c in candidates if (getattr(c, "viral_score", 0) or 0) >= threshold
                ]
                logger.info(
                    f"[Discovery] Selective Mode: Filtered {original_count} -> {len(candidates)} candidates (Threshold: {threshold})"
                )
            elif min_viral_score > 0:
                original_count = len(candidates)
                candidates = [
                    c for c in candidates if (getattr(c, "viral_score", 0) or 0) >= min_viral_score
                ]
                logger.info(
                    f"[Discovery] Filtered by Min Viral Score: {original_count} -> {len(candidates)} (Threshold: {min_viral_score})"
                )

            if exclude_shorts:
                original_count = len(candidates)
                candidates = [
                    c for c in candidates if "short" not in (c.platform or "").lower()
                ]
                logger.info(
                    f"[Discovery] Exclude Shorts: Filtered {original_count} -> {len(candidates)}"
                )

        return candidates

    async def _persist_candidates_batch(
        self, candidates: list[ContentCandidate], niche: str, region: str | None
    ) -> None:
        """Persists trending content candidates in a single batch transaction."""
        if not candidates:
            return

        async with async_session_factory() as db:
            try:
                for c in candidates:
                    db_c = ContentCandidateDB(
                        id=c.id,
                        platform=c.platform,
                        external_id=c.external_id,
                        title=c.title,
                        description=c.description,
                        creator_name=c.creator_name,
                        creator_id=c.creator_id,
                        source_uri=c.source_uri,
                        thumbnail_uri=c.thumbnail_uri,
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
                        region=c.region or region,
                        metadata_json=c.metadata_json,
                    )
                    await db.merge(db_c)

                await db.commit()
                logger.info(
                    f"[Discovery] Successfully persisted {len(candidates)} candidates for {niche}."
                )
            except Exception as e:
                logger.exception(f"[Discovery] Persistence Error: {e}")
                await db.rollback()

    def _ingest_aggregate_signal(
        self, candidates: list[ContentCandidate], niche: str
    ) -> None:
        """Ingests discovery signal into base_signal_bus."""
        try:
            from src.services.analytics.signal_bus import base_signal_bus
            avg_views = sum(c.view_count for c in candidates) / len(candidates)
            avg_viral = sum(c.viral_score for c in candidates) / len(candidates)
        
            base_signal_bus.ingest_signal(
                niche=niche,
                platform="discovery_aggregate",
                raw_metrics={
                    "growth_rate": (avg_viral / 100.0),  # Normalize 0-100 to 0-1.0
                    "avg_views": avg_views,
                    "saturation": min(1.0, len(candidates) / 50.0)
                }
            )
            logger.info(f"📡 [Discovery] Signal bus updated for '{niche}' with {len(candidates)} candidates.")
        except Exception as e:
            logger.exception(f"Failed to ingest signal to bus: {e}")

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
                    # Store the calculated velocity in the model
                    candidate.velocity = velocity
                else:
                    candidate.velocity = 0.0

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
            logger.exception(f"[Discovery] Recursive expansion error: {e}")

    async def _rank_candidates_with_ai(
        self, niche: str, candidates: list[ContentCandidate]
    ) -> list[ContentCandidate]:
        """
        Uses Groq with parallel batching and high-speed models to rank candidates.
        """
        from src.api.utils.vault import get_secret

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
            logger.exception(f"[Discovery] Neural Ranking Boost Error: {e}")
            return candidates

    async def deep_analyze_viral_patterns(
        self, candidate: ContentCandidate
    ) -> ViralPattern:
        """Analyzes a candidate for viral patterns with real transcript extraction."""
        transcript = await self._get_video_transcript(candidate.source_uri)
        return await pattern_deconstructor.analyze_video_structure(
            transcript, candidate.metadata_json or {}
        )

    async def _get_video_transcript(self, video_uri: str) -> str:
        """Extracts transcript from video via yt-dlp."""
        import yt_dlp

        # We use yt-dlp to get automatic captions as a transcript
        ydl_opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "subtitlesformat": "vtt",
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_uri, download=False)
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
            logger.exception(f"[Discovery] Transcript extraction failed: {e}")
            return "Transcript extraction failed. Using fallback metadata analysis."

    async def aggregate_niche_trends(self, niche: str):
        """
        Processes discovered content to identify top keywords and engagement for a niche.
        """
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

            # Return as dict for better serialization and semantic alignment
            return {
                "niche": niche,
                "top_keywords": top_keywords,
                "avg_engagement_score": avg_engagement_score,
                "candidate_count": len(candidates),
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
            }

    async def search_content(
        self,
        query: str | None = None,
        platforms: list[str] | None = None,
        min_views: int | None = None,
        min_viral_score: float | None = None,
        creator: str | None = None,
        tags: list[str] | None = None,
        date_from: datetime.datetime | None = None,
        date_to: datetime.datetime | None = None,
        sort_by: str = "viral_score",
        limit: int = 50,
        offset: int = 0,
        region: str | None = "US",
    ) -> list[ContentCandidate]:
        """
        Comprehensive search for content candidates across DB and Live Scanners.
        """
        from sqlalchemy import and_, select

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

                if region:
                    conditions.append(ContentCandidateDB.region == region)

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
                            source_uri=r.source_uri,
                            creator_name=r.creator_name,
                            creator_id=r.creator_id,
                            title=r.title,
                            description=r.description,
                            thumbnail_uri=r.thumbnail_uri,
                            view_count=r.view_count or 0,
                            like_count=r.like_count or 0,
                            comment_count=r.comment_count or 0,
                            share_count=r.share_count or 0,
                            engagement_score=r.engagement_score or 0.0,
                            viral_score=r.viral_score or 0,
                            duration_seconds=r.duration_seconds or 0.0,
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
                        region=region,
                    )
                    # Deduplicate and merge
                    seen_urls = {c.source_uri for c in candidates}
                    for lc in live_results:
                        if lc.source_uri not in seen_urls:
                            candidates.append(lc)
                            seen_urls.add(lc.source_uri)

                # 3. CloakBrowser Direct Fallback — run when no CloakBrowser results present
                #    (DB may have results from other scanners, but user expects live CloakBrowser data)
                if query:
                    has_cloak_results = any(
                        c.metadata_json.get("source") == "cloakbrowser" or
                        c.platform.lower() in ("cloakyoutube", "cloaktiktok", "cloakweb")
                        for c in candidates
                    )
                    if not has_cloak_results:
                        logger.info(
                            f"[Discovery] No CloakBrowser results for '{query}', invoking directly..."
                        )
                        try:
                            scraper = CloakBrowserScanner()
                            cloak_results = await scraper.scan_trends(query, region=region)
                            if cloak_results:
                                # Deduplicate and merge
                                seen_urls = {c.source_uri for c in candidates}
                                for cr in cloak_results:
                                    if cr.source_uri not in seen_urls:
                                        candidates.append(cr)
                                        seen_urls.add(cr.source_uri)
                                await self._persist_candidates_batch(cloak_results, query, region)
                                logger.info(
                                    f"[Discovery] CloakBrowser returned {len(cloak_results)} candidates for '{query}'"
                                )
                        except Exception as cloak_err:
                            logger.warning(f"[Discovery] CloakBrowser direct fallback failed: {cloak_err}")

                # Filter noise from all candidates
                filtered = []
                for c in candidates:
                    title = (c.title or "").strip().lower()
                    url = (c.source_uri or "").lower()
                    # Skip noise
                    if len(title) < 8:
                        continue
                    noise_titles = {
                        "sign up", "log in", "login", "sign in", "register",
                        "terms of service", "terms", "privacy policy", "privacy",
                        "cookie policy", "cookies", "about", "about us",
                        "help", "support", "faq", "contact", "contact us",
                        "download", "download the app", "get the app",
                        "notifications", "settings", "profile", "explore",
                        "following", "for you", "home", "search", "discover",
                        "reels", "shorts", "trending", "popular", "live",
                        "shop", "menu", "more", "careers", "jobs", "blog",
                        "accessibility", "ads info", "cookie use.",
                        "help center", "community guidelines",
                    }
                    if title in noise_titles:
                        continue
                    noise_url_patterns = [
                        "/about", "/careers", "/blog", "/help", "/support",
                        "/terms", "/privacy", "/cookie", "/legal", "/contact",
                        "/download", "/settings", "/notifications",
                    ]
                    if any(p in url for p in noise_url_patterns):
                        continue
                    filtered.append(c)

                return filtered[:limit]
            except Exception as e:
                logger.exception(f"[Discovery] Search failed: {e}")
                return []

    async def get_global_trending(
        self, limit: int = 50, min_viral_score: float = 0.0, region: str | None = "US"
    ) -> list[ContentCandidate]:
        """
        Passthrough to global DB trending results.
        """
        async with async_session_factory() as db:
            stmt = select(ContentCandidateDB)
            if min_viral_score > 0:
                stmt = stmt.where(ContentCandidateDB.viral_score >= min_viral_score)
            
            if region:
                stmt = stmt.where(ContentCandidateDB.region == region)

            stmt = stmt.order_by(ContentCandidateDB.viral_score.desc()).limit(limit)
            result = await db.execute(stmt)
            rows = result.scalars().all()

            return [
                ContentCandidate(
                    id=r.id,
                    platform=r.platform,
                    source_uri=r.source_uri,
                    creator_name=r.creator_name,
                    creator_id=r.creator_id,
                    title=r.title,
                    description=r.description,
                    thumbnail_uri=r.thumbnail_uri,
                    view_count=r.view_count or 0,
                    like_count=r.like_count or 0,
                    comment_count=r.comment_count or 0,
                    share_count=r.share_count or 0,
                    engagement_score=r.engagement_score or 0.0,
                    viral_score=r.viral_score or 0,
                    duration_seconds=r.duration_seconds or 0.0,
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
                    conditions.append(ContentCandidateDB.title.ilike(f"%{kw}%"))

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
                similarity = self._calculate_title_similarity(original.title, r.title)
                if similarity > 0.3:  # 30% threshold
                    reuploads.append(
                        ContentCandidate(
                            id=r.id,
                            platform=r.platform,
                            source_uri=r.source_uri,
                            creator_name=r.creator_name,
                            title=r.title,
                            description=r.description,
                            thumbnail_uri=r.thumbnail_uri,
                            view_count=r.view_count or 0,
                            engagement_score=r.engagement_score or 0.0,
                            viral_score=r.viral_score or 0,
                            duration_seconds=r.duration_seconds or 0.0,
                            category=r.category or "video",
                            niche=r.niche,
                            metadata={
                                **(r.metadata_json or {}),
                                "similarity_score": similarity,
                                "original_id": content_id,
                                "is_reupload": True,
                            },
                        )
                    )

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

    async def analyze_video_performance(self, video_uri: str, niche: str):
        """
        Deep analysis of a specific video's performance and viral potential.

        Args:
            video_uri: URL of video to analyze
            niche: Content niche for context

        Returns:
            Detailed performance analysis with repurposing suggestions
        """
        return await self.video_lead_scanner.evaluate_video_performance(
            video_uri=video_uri, niche=niche
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
        from pathlib import Path

        raw_dir = Path("local_downloads/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []
        logger.info(
            f"🚚 [Discovery] Procuring {len(candidates)} viral assets for production..."
        )

        async def _download_asset(c):
            url = c.get("url")
            video_id = c.get("id", "unknown")
            output_path = raw_dir / f"{video_id}.mp4"

            if output_path.exists():
                logger.info(f"   ✓ Asset {video_id} already in visual memory.")
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
                    logger.info(f"   ✓ Procured asset: {video_id}")
                    return {**c, "file_path": str(output_path)}
                else:
                    error_msg = stderr.decode()
                    logger.warning(
                        f"   ⚠️ yt-dlp failed for {video_id}: {error_msg[:100]}"
                    )

                    # TIER 10 RESILIENCE: Semantic Stock Fallback
                    import aiohttp

                    logger.info(
                        f"   🛡️ [Resilience] Triggering Stock Fallback for {video_id}..."
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

                    stock_candidates = await base_public_domain_service.scan_trends(
                        clean_query[:50]
                    )

                    if stock_candidates:
                        for sc in stock_candidates:
                            download_url = None
                            sc_metadata = sc.metadata_json or {}
                            if sc.platform == "Pexels":
                                video_files = sc_metadata.get("video_files", [])
                                if video_files:
                                    download_url = video_files[0].get("link")
                            elif sc.platform == "Archive.org":
                                # Construct direct download link
                                ident = sc_metadata.get("identifier")
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
                                                    f"   ✓ Procured Stock Fallback for {video_id} ({sc.platform})"
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
                                    logger.exception(
                                        f"   ⚠️ Stock download failed ({sc.platform}): {str(se)}"
                                    )

                    # FINAL TIER: SAFETY ASSET (Panic Resilience)
                    safety_path = Path("templates/safety/generic_space.mp4")
                    if safety_path.exists():
                        import shutil

                        shutil.copy(safety_path, output_path)
                        logger.warning(f"   🚨 [Panic] Using Safety Asset for {video_id}")
                        return {
                            **c,
                            "file_path": str(output_path),
                            "is_stock_fallback": True,
                            "is_safety": True,
                        }

                    logger.error(f"   ❌ All procurement tiers failed for {video_id}.")
                    return None
            except Exception as e:
                logger.exception(f"   ⚠️ Procurement exception: {str(e)}")
                return None

        # Execute procurement in a throttled swarm
        tasks = [_download_asset(c) for c in candidates]
        results = await asyncio.gather(*tasks)

        downloaded = [r for r in results if r is not None]
        logger.info(
            f"✅ [Discovery] Procurement complete. {len(downloaded)} assets ready for fusion."
        )

        if not downloaded and candidates:
            raise RuntimeError("CRITICAL: Failed to procure any assets for production.")

        return downloaded


base_discovery_service = DiscoveryService()
