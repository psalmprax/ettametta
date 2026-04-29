"""
Scanner service orchestrator for content discovery.

This module provides the main entry point for periodic trending content scanning.
It orchestrates the various platform scanners and persists results to the database.

Exports:
    scan_trending_content: Celery task for periodic content scanning
"""

import asyncio
import logging
from datetime import datetime


from src.api.utils.celery import celery_app
from src.api.utils.database import async_session_factory
from src.api.utils.models import ContentCandidateDB, MonitoredNiche
from src.api.utils.vault import get_secret

from .youtube_scanner import YouTubeShortsScanner
from .youtube_long_scanner import YouTubeLongScanner
from .tiktok_scanner import TikTokScanner
from .models import ContentCandidate

logger = logging.getLogger(__name__)


class ScannerService:
    """
    Orchestrates content discovery from multiple platforms.
    Handles duplicate detection by external_id and database persistence.
    """

    def __init__(self):
        # Initialize platform scanners
        self.scanners = [
            YouTubeShortsScanner(),
            YouTubeLongScanner(),
            TikTokScanner(),
        ]

    async def scan_all_platforms(self, niche: str) -> list[ContentCandidate]:
        """
        Scan all configured platforms for trending content in a niche.

        Args:
            niche: Content niche/category to scan for

        Returns:
            List of discovered content candidates
        """
        all_candidates = []

        # Run all scanners concurrently
        tasks = [scanner.scan_trends(niche) for scanner in self.scanners]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_candidates.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Scanner error: {result}")

        return all_candidates

    async def save_to_database(self, candidates: list[ContentCandidate]) -> int:
        """
        Save content candidates to database, handling duplicates by external_id.

        Args:
            candidates: List of content candidates to persist

        Returns:
            Number of new records saved
        """
        saved_count = 0

        async with async_session_factory() as db:
            for candidate in candidates:
                try:
                    # Use metadata_json field consistently (aliased as 'metadata' in Pydantic)
                    candidate_metadata = candidate.metadata_json or {}

                    # Check for existing record by external_id
                    external_id = (
                        candidate_metadata.get("video_id")
                        if candidate_metadata
                        else None
                    )

                    if external_id:
                        # Check if this content already exists
                        from sqlalchemy import select

                        stmt = select(ContentCandidateDB).where(
                            ContentCandidateDB.external_id == external_id,
                            ContentCandidateDB.platform == candidate.platform,
                        )
                        result = await db.execute(stmt)
                        existing = result.scalar_one_or_none()

                        if existing:
                            # Update existing record with fresh metrics
                            existing.view_count = candidate.view_count
                            existing.engagement_score = candidate.engagement_score
                            existing.viral_score = candidate.viral_score
                            existing.scanned_at = datetime.utcnow()
                        else:
                            # Create new record
                            db_candidate = ContentCandidateDB(
                                id=candidate.id,
                                platform=candidate.platform,
                                external_id=external_id,
                                title=candidate.title,
                                description=candidate.description,
                                creator_name=candidate.creator_name,
                                source_uri=candidate.source_uri,
                                url=candidate.source_uri,  # Legacy field maintenance
                                thumbnail_uri=candidate.thumbnail_uri,
                                duration_seconds=candidate.duration_seconds,
                                view_count=candidate.view_count,
                                like_count=candidate.like_count,
                                comment_count=candidate.comment_count,
                                share_count=candidate.share_count,
                                engagement_score=candidate.engagement_score,
                                viral_score=candidate.viral_score,
                                category=candidate.category,
                                tags=candidate_metadata.get("tags"),
                                metadata_json=candidate_metadata,
                                niche=candidate_metadata.get("niche"),
                                published_at=candidate_metadata.get("published_at"),
                            )
                            db.add(db_candidate)
                            saved_count += 1

                    await db.commit()

                except Exception as e:
                    logger.error(f"Failed to save candidate {candidate.id}: {e}")
                    await db.rollback()

        return saved_count


# Global service instance
_scanner_service: ScannerService | None = None


def get_scanner_service() -> ScannerService:
    """Get or create the global scanner service instance."""
    global _scanner_service
    if _scanner_service is None:
        _scanner_service = ScannerService()
    return _scanner_service


@celery_app.task(name="services.discovery.scanner_service.scan_trending_content")
def scan_trending_content():
    """
    Periodic Celery task for scanning trending content.
    Runs every 2 hours via Celery Beat.

    Scans all active niches and persists discovered content to the database.
    """
    from sqlalchemy import select

    async def run_scan():
        logger.info("[Scanner] Starting periodic trending content scan...")

        # Get all active niches to scan
        async with async_session_factory() as db:
            stmt = select(MonitoredNiche).where(MonitoredNiche.is_active == True)
            result = await db.execute(stmt)
            niches = result.scalars().all()

            if not niches:
                # If no active niches, scan default categories
                niches_to_scan = ["trending", "viral", "popular"]
            else:
                niches_to_scan = [n.niche for n in niches]

        total_new_content = 0

        service = get_scanner_service()

        for niche in niches_to_scan:
            try:
                # Scan all platforms for this niche
                candidates = await service.scan_all_platforms(niche)

                if candidates:
                    # Save to database (handles duplicates)
                    new_count = await service.save_to_database(candidates)
                    total_new_content += new_count

                    logger.info(
                        f"[Scanner] Found {len(candidates)} candidates for '{niche}', saved {new_count} new"
                    )
                else:
                    logger.info(f"[Scanner] No candidates found for '{niche}'")

            except Exception as e:
                logger.error(f"[Scanner] Error scanning niche '{niche}': {e}")

        # Update last scanned time for all niches
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
        result = asyncio.run(run_scan())
        return result
    except Exception as e:
        logger.error(f"[Scanner] Scan failed: {e}")
        return {"status": "error", "error": str(e)}


# Export for plan verification
__all__ = ["scan_trending_content", "get_scanner_service", "ScannerService"]
