"""
Scanner service orchestrator for content discovery.

This module provides the main entry point for periodic trending content scanning.
It orchestrates the various platform scanners and persists results to the database.
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from src.api.utils.celery import celery_app
from src.api.utils.database import async_session_factory
from src.api.utils.models import ContentCandidateDB, MonitoredNiche
from src.api.config import settings
from src.api.utils.resilience import CircuitBreaker

from .youtube_scanner import YouTubeShortsScanner
from .youtube_long_scanner import YouTubeLongScanner
from .tiktok_scanner import TikTokScanner
from .instagram_scanner import InstagramScanner
from .x_scanner import XScanner
from .models import ContentCandidate

logger = logging.getLogger(__name__)


class ScannerService:
    """
    Orchestrates content discovery from multiple platforms.
    Handles duplicate detection and database persistence with resilience.
    """

    def __init__(self):
        # Initialize platform scanners
        self.scanners = {
            "youtube_shorts": YouTubeShortsScanner(),
            "youtube_long": YouTubeLongScanner(),
            "tiktok": TikTokScanner(),
            "instagram": InstagramScanner(),
            "x": XScanner()
        }
        
        # Per-platform circuit breakers to prevent cascading failures
        self.breakers = {
            name: CircuitBreaker(name=f"Scanner_{name}", failure_threshold=3, recovery_timeout=600)
            for name in self.scanners.keys()
        }

    async def scan_all_platforms(self, niche: str) -> List[ContentCandidate]:
        """
        Scan all configured platforms for trending content in parallel.
        """
        all_candidates = []
        
        async def run_scanner(name: str, scanner: any) -> List[ContentCandidate]:
            breaker = self.breakers[name]
            
            if breaker.is_open():
                logger.warning(f"[Scanner] Circuit for {name} is OPEN. Skipping.")
                return []
                
            try:
                # Use settings-based timeout for scanning (Scraping can be slow)
                timeout = settings.LLM_TIMEOUT * 2 
                
                logger.info(f"[Scanner] Running {name} for niche: {niche}")
                result = await asyncio.wait_for(
                    scanner.scan_trends(niche),
                    timeout=timeout
                )
                breaker.record_success()
                return result if isinstance(result, list) else []
            except asyncio.TimeoutExpired:
                logger.error(f"[Scanner] {name} TIMEOUT after {timeout}s")
                breaker.record_failure()
                return []
            except Exception as e:
                logger.error(f"[Scanner] {name} FAILED: {e}")
                breaker.record_failure()
                return []

        # Run all scanners concurrently
        tasks = [run_scanner(name, scanner) for name, scanner in self.scanners.items()]
        results = await asyncio.gather(*tasks)

        for result in results:
            all_candidates.extend(result)

        return all_candidates

    async def save_to_database(self, candidates: List[ContentCandidate]) -> int:
        """
        Save content candidates to database, handling duplicates by external_id.
        """
        saved_count = 0

        async with async_session_factory() as db:
            for candidate in candidates:
                try:
                    # Clean up ID and extract external_id
                    # Standard candidate IDs are "platform_externalid"
                    ext_id = candidate.id.split('_', 1)[1] if '_' in candidate.id else candidate.id
                    
                    # Check if this content already exists
                    from sqlalchemy import select
                    stmt = select(ContentCandidateDB).where(
                        ContentCandidateDB.external_id == ext_id,
                        ContentCandidateDB.platform == candidate.platform,
                    )
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()

                    if existing:
                        # Update metrics
                        existing.view_count = candidate.view_count
                        existing.engagement_score = candidate.engagement_score
                        existing.viral_score = candidate.viral_score
                        existing.scanned_at = datetime.utcnow()
                    else:
                        # Create new record
                        db_candidate = ContentCandidateDB(
                            id=candidate.id,
                            platform=candidate.platform,
                            external_id=ext_id,
                            title=candidate.title,
                            description=candidate.description,
                            creator_name=candidate.creator_name,
                            source_uri=candidate.source_uri,
                            thumbnail_uri=candidate.thumbnail_uri,
                            duration_seconds=candidate.duration_seconds,
                            view_count=candidate.view_count,
                            like_count=candidate.like_count,
                            comment_count=candidate.comment_count,
                            share_count=candidate.share_count,
                            engagement_score=candidate.engagement_score,
                            viral_score=candidate.viral_score,
                            category=candidate.category,
                            metadata_json=candidate.metadata_json or {},
                            niche=candidate.niche,
                            published_at=candidate.published_at,
                        )
                        db.add(db_candidate)
                        saved_count += 1

                    # Commit periodically to avoid large transaction locks
                    if saved_count % 10 == 0:
                        await db.commit()

                except Exception as e:
                    logger.error(f"Failed to save candidate {candidate.id}: {e}")
                    await db.rollback()
            
            await db.commit()

        return saved_count


# Global service instance
_scanner_service: ScannerService | None = None

def get_scanner_service() -> ScannerService:
    global _scanner_service
    if _scanner_service is None:
        _scanner_service = ScannerService()
    return _scanner_service


@celery_app.task(name="services.discovery.scanner_service.scan_trending_content")
def scan_trending_content():
    """Periodic Celery task for scanning trending content."""
    from sqlalchemy import select

    async def run_scan():
        logger.info("[Scanner] Starting parallel trending content scan...")

        async with async_session_factory() as db:
            stmt = select(MonitoredNiche).where(MonitoredNiche.is_active == True)
            result = await db.execute(stmt)
            niches = result.scalars().all()

            if not niches:
                niches_to_scan = ["trending", "viral", "AI automation"]
            else:
                niches_to_scan = [n.niche for n in niches]

        total_new_content = 0
        service = get_scanner_service()

        for niche in niches_to_scan:
            try:
                candidates = await service.scan_all_platforms(niche)
                if candidates:
                    new_count = await service.save_to_database(candidates)
                    total_new_content += new_count
                    logger.info(f"[Scanner] Found {len(candidates)} candidates for '{niche}', saved {new_count} new")

            except Exception as e:
                logger.error(f"[Scanner] Error scanning niche '{niche}': {e}")

        # Update timestamps
        async with async_session_factory() as db:
            for niche in niches_to_scan:
                stmt = select(MonitoredNiche).where(MonitoredNiche.niche == niche)
                result = await db.execute(stmt)
                db_niche = result.scalar_one_or_none()
                if db_niche:
                    db_niche.last_scanned_at = datetime.utcnow()
            await db.commit()

        return {
            "status": "success",
            "niches_scanned": len(niches_to_scan),
            "new_content_saved": total_new_content,
        }

    try:
        return asyncio.run(run_scan())
    except Exception as e:
        logger.error(f"[Scanner] Scan failed: {e}")
        return {"status": "error", "error": str(e)}

__all__ = ["scan_trending_content", "get_scanner_service", "ScannerService"]
