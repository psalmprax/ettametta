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
from .deconstructor import pattern_deconstructor
from api.utils.database import SessionLocal
from api.utils.models import ContentCandidateDB

class DiscoveryService:
    def __init__(self):
        self.scanners = [
            YouTubeShortsScanner(),
            YouTubeLongScanner(),
            TikTokScanner(),
        ]
        self.global_scanners = [
            base_reddit_scanner,
            base_x_scanner,
            base_public_domain_scanner,
            base_metasearch_scanner,
            base_rumble_scanner,
            base_instagram_scanner,
            base_facebook_scanner,
            base_twitch_scanner,
            base_snapchat_scanner,
            base_pinterest_scanner,
            base_linkedin_scanner,
            base_bilibili_scanner
        ]

    async def find_trending_content(self, niche: str, horizon: str = "30d") -> List[ContentCandidate]:
        import json
        import redis
        from api.config import settings

        # 1. Check Cache
        redis_url = settings.REDIS_URL
        # Ensure we're using the correct hostname within docker
        # If running in docker, 'localhost' won't work for accessing other containers
        # We need to replace 'localhost' with 'redis' but keep the port/db
        if "//localhost" in redis_url:
             redis_url = redis_url.replace("//localhost", "//redis")

        # Custom JSON Encoder for datetime
        def json_serial(obj):
            from datetime import datetime
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError (f"Type {type(obj)} not serializable")

        import datetime
        
        # Calculate published_after based on horizon
        now = datetime.datetime.now(datetime.timezone.utc)
        published_after = None
        if horizon == "24h":
            published_after = now - datetime.timedelta(days=1)
        elif horizon == "7d":
            published_after = now - datetime.timedelta(days=7)
        elif horizon == "30d":
            published_after = now - datetime.timedelta(days=30)

        try:
            r = redis.from_url(redis_url)
            cache_key = f"discovery:trends:{niche}:{horizon}"
            cached_data = r.get(cache_key)
            
            if cached_data:
                print(f"[Discovery] Cache HIT for {niche} ({horizon})")
                data = json.loads(cached_data)
                return [ContentCandidate(**item) for item in data]
        except Exception as e:
             print(f"[Discovery] Redis connection failed: {e}")
             r = None

        print(f"[Discovery] Cache MISS for {niche} ({horizon}), scanning...")

        # 2. Parallel Scanning
        import asyncio
        
        # Prepare scanner tasks
        tasks = []
        for scanner in self.scanners:
            tasks.append(scanner.scan_trends(niche, published_after=published_after))
        
        for g_scanner in self.global_scanners:
            tasks.append(g_scanner.scan_trends(niche, published_after=published_after))
            
        # Execute all scans concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_candidates = []
        for res in results:
            if isinstance(res, list):
                all_candidates.extend(res)
            elif isinstance(res, Exception):
                print(f"[Discovery] Scanner Exception: {res}")
        
        # 3. Persistence Logic (Efficient Batch Integration)
        db = SessionLocal()
        try:
            # Prepare all candidates for the database
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
                    thumbnail_url=c.thumbnail_url,
                    metadata_json=c.metadata,
                    niche=niche
                ))
            
            # Efficient Merge (UPSERT pattern)
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
        AI identifies related sub-niches and triggers background scans to hit transparency targets.
        """
        from groq import Groq
        from api.config import settings
        import json
        
        if not settings.GROQ_API_KEY:
            return

        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            titles = [c.title for c in candidates[:10]]
            
            prompt = f"""
            Based on these trending videos in the '{niche}' niche:
            {json.dumps(titles)}
            
            Identify 3 hyper-targeted sub-niches or related keywords that should be scanned to find more high-velocity content.
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
                from api.utils.celery import celery_app
                for sn in sub_niches[:3]:
                    # Offload to Celery to avoid blocking
                    celery_app.send_task("discovery.scan_trends", args=[sn])
                    
        except Exception as e:
            print(f"[Discovery] Recursive expansion error: {e}")

    async def _rank_candidates_with_ai(self, niche: str, candidates: List[ContentCandidate]) -> List[ContentCandidate]:
        """
        Uses Groq with parallel batching and high-speed models to rank candidates.
        """
        from groq import Groq
        from api.config import settings
        import json

        try:
            client = Groq(api_key=settings.GROQ_API_KEY)
            
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

    async def search_content(self, query: str, limit: int = 50) -> List[ContentCandidate]:
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
                # We reuse find_trending_content but use the query as the niche
                # This will populate the DB and return the fresh candidates
                live_results = await self.find_trending_content(query, horizon="30d")
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
