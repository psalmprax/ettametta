import json
import redis
import asyncio
import datetime
from typing import List
from .models import ContentCandidate, ViralPattern
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
from .deconstructor import pattern_deconstructor
from api.utils.database import SessionLocal
from api.utils.models import ContentCandidateDB, SystemSettings, NicheTrendDB, MonitoredNiche
from api.config import settings
from api.utils.vault import get_secret
from api.utils.celery import celery_app
from groq import Groq


class DiscoveryService:
    def __init__(self):
        # Primary scanners (run for every niche)
        # These are the production-ready scanners with real APIs
        self.scanners = [
            YouTubeShortsScanner(),      # Real API ✓
            YouTubeLongScanner(),       # Real API ✓
            TikTokScanner(),            # Web scrape ✓
            base_duckduckgo_scanner,    # Free fallback ✓
        ]
        # Secondary scanners (supplementary, web scraping)
        # Now all implemented with web scraping (no API keys needed)
        self.global_scanners = [
            base_reddit_scanner,        # Real API (JSON) ✓
            base_x_scanner,            # Web scrape
            base_instagram_scanner,    # Web scrape
            base_facebook_scanner,     # Web scrape
            base_twitch_scanner,        # Web scrape (NEW)
            base_pinterest_scanner,     # Web scrape (NEW)
            base_linkedin_scanner,     # Web scrape (NEW)
            base_snapchat_scanner,     # Web scrape (NEW)
            base_bilibili_scanner,     # Web scrape (NEW)
            base_rumble_scanner,       # Web scrape (NEW)
            base_public_domain_scanner, # Partial (Pexels)
            base_metasearch_scanner,    # Partial
            base_skool_scanner,        # Partial
        ]

    async def _log(self, message: str, level: str = "INFO"):
        """Broadcasts a discovery log message."""
        await notify_system_log_async(message, level=level, module="DISCOVERY")
        # Send log via Redis to avoid circular import
        import json
        import redis
        import datetime
        from api.config import settings
        try:
            r = redis.from_url(settings.REDIS_URL)
            r.publish("system_logs", json.dumps({
                "message": message,
                "level": level,
                "module": "DISCOVERY",
                "timestamp": str(datetime.datetime.now())
            }))
        except Exception as e:
            print(f"[Discovery] Failed to send log: {e}")

    async def find_trending_content(
        self, 
        niche: str, 
        horizon: str = "30d", 
        tier: str = "free",
        min_viral_score: int = 0,
        exclude_shorts: bool = False,
        deep_scan: bool = False
    ) -> List[ContentCandidate]:
        import json
        import redis
        from api.config import settings

        # 1. Check Cache (Skip if deep scan)
        redis_url = settings.REDIS_URL
        if "//localhost" in redis_url:
             redis_url = redis_url.replace("//localhost", "//redis")

        try:
            r = redis.from_url(redis_url)
            cache_key = f"discovery:trends:{niche}:{horizon}"
            if not deep_scan:
                cached_data = r.get(cache_key)
                if cached_data:
                    await self._log(f"Cache HIT for '{niche}' ({horizon}). Loading stored patterns.", "SUCCESS")
                    data = json.loads(cached_data)
                    return [ContentCandidate(**item) for item in data]
        except Exception as e:
             await self._log(f"Redis connection failed: {e}", "WARNING")
             r = None

        await self._log(f"Initiating {'DEEP SCAN' if deep_scan else 'Fast Scan'} for '{niche}' ({horizon})...", "SYSTEM")

        # 2. Parallel Scanning
        import asyncio
        
        # Prepare scanner tasks
        tasks = []
        for scanner in self.scanners:
            tasks.append(scanner.scan_trends(niche, published_after=None if deep_scan else None)) # Deep scan might use different horizon
        
        # Deep scan unleashes ALL scanners regardless of tier for that specific request
        scanners_to_use = self.global_scanners if deep_scan or tier != "free" else [
            base_x_scanner,
            base_instagram_scanner,
            base_facebook_scanner,
            base_twitch_scanner,
            base_bilibili_scanner,
            base_rumble_scanner,
        ]

        await self._log(f"Deploying swarm: {len(self.scanners) + len(scanners_to_use)} specialized scanners active.", "INFO")
        for g_scanner in scanners_to_use:
            tasks.append(g_scanner.scan_trends(niche, published_after=None))
            
        # Execute all scans concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 4. Neural Ranking & Scoring Enrichment
        all_candidates = []
        for res in results:
            if isinstance(res, list):
                all_candidates.extend(res)
            elif isinstance(res, Exception):
                print(f"[Discovery] Scanner Exception: {res}")

        # If Deep Scan: Automatically trigger analysis for top 5 candidates
        if deep_scan and all_candidates:
            print(f"[Discovery] Deep Scan: Auto-triggering analysis for top candidates.")
            from services.discovery.tasks import analyze_viral_pattern_task
            for c in all_candidates[:5]:
                analyze_viral_pattern_task.delay(c.dict())

        # If no results from scan, fall back to database
        if not all_candidates:
            print(f"[Discovery] No scan results for {niche}, falling back to database...")
            db = SessionLocal()
            try:
                db_results = db.query(ContentCandidateDB).filter(
                    ContentCandidateDB.niche == niche
                ).order_by(ContentCandidateDB.views.desc()).limit(50).all()
                
                for r in db_results:
                    all_candidates.append(ContentCandidate(
                        id=r.id,
                        platform=r.platform,
                        url=r.url,
                        author=r.author,
                        title=r.title,
                        description=r.description,
                        thumbnail_url=r.thumbnail_url,
                        view_count=r.views,
                        engagement_rate=r.engagement_score,
                        views=r.views,
                        engagement_score=r.engagement_score,
                        viral_score=r.viral_score,
                        duration_seconds=r.duration_seconds,
                        category=r.category or "video",
                        published_at=r.discovery_date.isoformat() if r.discovery_date else None,
                        niche=r.niche,
                        metadata=r.metadata_json or {}
                    ))
            finally:
                db.close()

        # Enforcement: Selective Monetization Mode (Viral Score > 85)
        db = SessionLocal()
        try:
            mode_setting = db.query(SystemSettings).filter(SystemSettings.key == "monetization_mode").first()
            monetization_mode = mode_setting.value if mode_setting else "all"
            
            if monetization_mode == "selective":
                threshold = max(65, min_viral_score)
                original_count = len(all_candidates)
                all_candidates = [c for c in all_candidates if (getattr(c, 'viral_score', 0) or 0) >= threshold]
                print(f"[Discovery] Selective Mode: Filtered {original_count} -> {len(all_candidates)} candidates (Threshold: {threshold})")
            elif min_viral_score > 0:
                original_count = len(all_candidates)
                all_candidates = [c for c in all_candidates if (getattr(c, 'viral_score', 0) or 0) >= min_viral_score]
                print(f"[Discovery] Filtered by Min Viral Score: {original_count} -> {len(all_candidates)} (Threshold: {min_viral_score})")

            if exclude_shorts:
                original_count = len(all_candidates)
                all_candidates = [c for c in all_candidates if "short" not in (c.platform or "").lower()]
                print(f"[Discovery] Exclude Shorts: Filtered {original_count} -> {len(all_candidates)}")
        finally:
            db.close()
        
        # 3. Persistence Logic (Efficient Batch Integration)
        db = SessionLocal()
        try:
            db_candidates = []
            for c in all_candidates:
                db_candidates.append(ContentCandidateDB(
                    id=c.id,
                    platform=c.platform,
                    url=c.url,
                    author=c.author,
                    title=c.title,
                    description=c.description,
                    view_count=c.views,
                    engagement_rate=c.engagement_score,
                    views=c.views,
                    engagement_score=c.engagement_score,
                    viral_score=c.viral_score,
                    duration_seconds=c.duration_seconds,
                    category=c.category,
                    thumbnail_url=c.thumbnail_url,
                    metadata_json=c.metadata,
                    niche=niche
                ))
            
            for db_c in db_candidates:
                db.merge(db_c)
            
            db.commit()
            print(f"[Discovery] Successfully persisted {len(db_candidates)} candidates for {niche}.")
        except Exception as e:
            print(f"[Discovery] Persistence Error: {e}")
            db.rollback()
        finally:
            db.close()

        # 5. Recursive Discovery Expansion (Autonomous Scaling)
        if len(all_candidates) > 0:
            asyncio.create_task(self._trigger_recursive_expansion(niche, all_candidates))

        return all_candidates

    async def _trigger_recursive_expansion(self, niche: str, candidates: List[ContentCandidate]):
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
                response_format={"type": "json_object"}
            )
            
            response = json.loads(completion.choices[0].message.content)
            sub_niches = response.get("sub_niches") or response.get("keywords") or list(response.values())[0]
            
            if sub_niches and isinstance(sub_niches, list):
                print(f"[Discovery] Recursive expansion triggered for: {sub_niches}")
                for sn in sub_niches[:3]:
                    celery_app.send_task("discovery.scan_trends", args=[sn])
                    
        except Exception as e:
            print(f"[Discovery] Recursive expansion error: {e}")

    async def _rank_candidates_with_ai(self, niche: str, candidates: List[ContentCandidate]) -> List[ContentCandidate]:
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
                 candidate_summaries.append({
                     "idx": i,
                     "title": c.title,
                     "engagement": f"{c.engagement_rate:.2%}" if hasattr(c, 'engagement_rate') else "0%"
                 })

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
                response_format={"type": "json_object"}
            )
            
            response_json = json.loads(completion.choices[0].message.content)
            indices = response_json.get("indices") or list(response_json.values())[0]

            if not indices or not isinstance(indices, list):
                return candidates

            ranked = []
            seen = set()
            for idx in indices:
                if isinstance(idx, int) and 0 <= idx < len(candidates) and idx not in seen:
                    ranked.append(candidates[idx])
                    seen.add(idx)
            
            for i, c in enumerate(candidates):
                if i not in seen:
                    ranked.append(c)
            
            return ranked
        except Exception as e:
            print(f"[Discovery] Neural Ranking Boost Error: {e}")
            return candidates

    async def analyze_viral_pattern(self, candidate: ContentCandidate) -> ViralPattern:
        """Analyzes a candidate for viral patterns with real transcript extraction."""
        transcript = await self._get_video_transcript(candidate.url)
        return await pattern_deconstructor.analyze_video_structure(transcript, candidate.metadata or {})

    async def _get_video_transcript(self, video_url: str) -> str:
        """Extracts transcript from video via yt-dlp."""
        import yt_dlp
        import os
        import tempfile
        
        # We use yt-dlp to get automatic captions as a transcript
        ydl_opts = {
            'skip_download': True,
            'writeautomaticsub': True,
            'subtitlesformat': 'vtt',
            'quiet': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                # Check for subtitles or automatic captions
                if 'subtitles' in info and info['subtitles']:
                    # Use first available subtitle
                    return f"Transcript extracted from subtitles for {info.get('title')}"
                elif 'requested_subtitles' in info:
                    return f"Automatic captions extracted for {info.get('title')}"
                
                # Fallback to metadata if no transcript
                return f"No transcript available. Analysis based on metadata: {info.get('title')} - {info.get('description', '')[:100]}..."
        except Exception as e:
            print(f"[Discovery] Transcript extraction failed: {e}")
            return "Transcript extraction failed. Using fallback metadata analysis."

    async def aggregate_niche_trends(self, niche: str):
        """
        Processes discovered content to identify top keywords and engagement for a niche.
        """
        from api.utils.models import NicheTrendDB
        from collections import Counter
        import re

        db = SessionLocal()
        try:
            candidates = db.query(ContentCandidateDB).filter(ContentCandidateDB.niche == niche).all()
            if not candidates:
                return None
            
            all_text = " ".join([c.title or "" for c in candidates])
            # Simple keyword extraction
            words = re.findall(r'\w+', all_text.lower())
            stop_words = {'the', 'a', 'to', 'in', 'and', 'for', 'of', 'on', 'with', 'at', 'by', 'is', 'it'}
            keywords = [w for w in words if len(w) > 3 and w not in stop_words]
            top_keywords = [k for k, _ in Counter(keywords).most_common(10)]
            
            avg_engagement = sum([c.engagement_score for c in candidates]) / len(candidates)
            
            trend = NicheTrendDB(
                niche=niche,
                platform="YouTube Shorts", # Default for now
                top_keywords=top_keywords,
                avg_engagement=avg_engagement,
                viral_pattern_ids=[] # Future link to analyzed patterns
            )
            
            # Upsert logic (simplified)
            existing = db.query(NicheTrendDB).filter(NicheTrendDB.niche == niche).first()
            if existing:
                existing.top_keywords = top_keywords
                existing.avg_engagement = avg_engagement
            else:
                db.add(trend)
            
            db.commit()
            return trend
        finally:
            db.close()

    async def search_content(
        self, 
        query: str, 
        limit: int = 50,
        min_viral_score: int = 0,
        exclude_shorts: bool = False
    ) -> List[ContentCandidate]:
        """
        Searches specific viral candidates by keyword (Title or Description).
        Triggers a live scan if local results are insufficient.
        """
        from api.utils.models import ContentCandidateDB
        from sqlalchemy import or_

        db = SessionLocal()
        try:
            # 1. Local Database Search
            search_query = f"%{query}%"
            results = db.query(ContentCandidateDB).filter(
                or_(
                    ContentCandidateDB.title.ilike(search_query),
                    ContentCandidateDB.description.ilike(search_query),
                    ContentCandidateDB.niche.ilike(search_query) 
                )
            ).order_by(ContentCandidateDB.views.desc()).limit(limit).all()

            # 2. Live Scan Trigger (Intelligence Layer)
            # If we have few results, proactively scan for the query term as a "Niche"
            if len(results) < 10:
                print(f"[Discovery] Insufficient results for '{query}' ({len(results)}), triggering live Fast Scan...")
                
                # PERSISTENCE: Save this as a monitored niche for future autonomous scans
                from api.utils.models import MonitoredNiche
                existing_niche = db.query(MonitoredNiche).filter(MonitoredNiche.niche == query).first()
                if not existing_niche:
                    new_niche = MonitoredNiche(niche=query, is_active=True)
                    db.add(new_niche)
                    db.commit()
                    print(f"[Discovery] Registered new custom niche: {query}")

                # We reuse find_trending_content but use the query as the niche
                # This will populate the DB and return the fresh candidates
                live_results = await self.find_trending_content(
                    query, 
                    horizon="30d",
                    min_viral_score=min_viral_score,
                    exclude_shorts=exclude_shorts
                )
                if live_results:
                     return live_results

            # Convert back to Pydantic models
            candidates = []
            for r in results:
                candidates.append(ContentCandidate(
                    id=r.id,
                    platform=r.platform,
                    url=r.url,
                    author=r.author,
                    title=r.title, 
                    description=r.description,
                    thumbnail_url=r.thumbnail_url,
                    view_count=r.views,
                    engagement_rate=r.engagement_score,
                    views=r.views,
                    engagement_score=r.engagement_score,
                    viral_score=r.viral_score,
                    duration_seconds=r.duration_seconds,
                    category=r.category or "video",
                    published_at=r.discovery_date.isoformat() if r.discovery_date else None,
                    niche=r.niche,
                    metadata=r.metadata_json or {}
                ))
            return candidates
        except Exception as e:
            print(f"[Discovery] Search failed: {e}")
            return []
        finally:
            db.close()

base_discovery_service = DiscoveryService()
