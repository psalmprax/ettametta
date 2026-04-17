"""
Content Discovery Search Service
Provides advanced search and filtering for content candidates.
"""

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.utils.models import ContentCandidateDB
from src.api.utils.database import async_session_factory


async def search_content(
    query: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    min_views: Optional[int] = None,
    min_viral_score: Optional[float] = None,
    creator: Optional[str] = None,
    tags: Optional[List[str]] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = "viral_score",
    limit: int = 50,
    offset: int = 0,
) -> List[dict]:
    """
    Search content candidates with advanced filtering and sorting.

    Args:
        query: Text search in title, description, or niche
        platforms: List of platform names to filter by
        min_views: Minimum view count
        min_viral_score: Minimum viral score
        creator: Creator name or ID to filter by
        tags: List of tags to match (any match)
        date_from: Filter content published after this date
        date_to: Filter content published before this date
        sort_by: Field to sort by - "viral_score", "published_at", "view_count"
        limit: Maximum number of results to return
        offset: Number of results to skip for pagination

    Returns:
        List of content candidate dictionaries with all fields
    """
    logger = logging.getLogger(__name__)

    async with async_session_factory() as db:
        try:
            # Build query with filters
            stmt = select(ContentCandidateDB)

            # Apply filters
            conditions = []

            # Text search
            if query and query.strip():
                search_term = f"%{query.strip()}%"
                conditions.append(
                    or_(
                        ContentCandidateDB.title.ilike(search_term),
                        ContentCandidateDB.description.ilike(search_term),
                        ContentCandidateDB.niche.ilike(search_term),
                        ContentCandidateDB.creator_name.ilike(search_term),
                    )
                )

            # Platform filter
            if platforms:
                conditions.append(ContentCandidateDB.platform.in_(platforms))

            # Minimum views filter
            if min_views is not None:
                conditions.append(ContentCandidateDB.view_count >= min_views)

            # Minimum viral score filter
            if min_viral_score is not None:
                conditions.append(ContentCandidateDB.viral_score >= min_viral_score)

            # Creator filter
            if creator and creator.strip():
                creator_search = f"%{creator.strip()}%"
                conditions.append(
                    or_(
                        ContentCandidateDB.creator_name.ilike(creator_search),
                        ContentCandidateDB.creator_id == creator.strip(),
                    )
                )

            # Tags filter - tags stored as JSON array
            if tags:
                # Match any of the provided tags (OR condition)
                tag_conditions = []
                for tag in tags:
                    tag_pattern = f'%"{tag}"%'
                    tag_conditions.append(
                        ContentCandidateDB.tags.astext.like(tag_pattern)
                    )
                if tag_conditions:
                    conditions.append(or_(*tag_conditions))

            # Date range filter
            if date_from:
                conditions.append(ContentCandidateDB.published_at >= date_from)
            if date_to:
                conditions.append(ContentCandidateDB.published_at <= date_to)

            # Combine all conditions
            if conditions:
                stmt = stmt.where(and_(*conditions))

            # Apply sorting
            sort_field = sort_by.lower()
            if sort_field == "viral_score":
                stmt = stmt.order_by(ContentCandidateDB.viral_score.desc())
            elif sort_field == "published_at":
                stmt = stmt.order_by(ContentCandidateDB.published_at.desc())
            elif sort_field == "view_count":
                stmt = stmt.order_by(ContentCandidateDB.view_count.desc())
            else:
                stmt = stmt.order_by(ContentCandidateDB.viral_score.desc())

            # Apply pagination
            stmt = stmt.limit(limit).offset(offset)

            # Execute query
            result = await db.execute(stmt)
            rows = result.scalars().all()

            # Convert to dictionaries
            results = []
            for row in rows:
                results.append(
                    {
                        "id": row.id,
                        "platform": row.platform,
                        "external_id": row.external_id,
                        "title": row.title,
                        "description": row.description,
                        "creator_name": row.creator_name,
                        "creator_id": row.creator_id,
                        "url": row.url,
                        "thumbnail_url": row.thumbnail_url,
                        "published_at": row.published_at,
                        "scanned_at": row.scanned_at,
                        "duration_seconds": row.duration_seconds,
                        "view_count": row.view_count,
                        "like_count": row.like_count,
                        "comment_count": row.comment_count,
                        "share_count": row.share_count,
                        "engagement_score": row.engagement_score,
                        "viral_score": row.viral_score,
                        "category": row.category,
                        "tags": row.tags or [],
                        "niche": row.niche,
                        "metadata": row.metadata_json or {},
                    }
                )

            logger.info(
                f"[Search] Returned {len(results)} results (offset={offset}, limit={limit})"
            )
            return results

        except Exception as e:
            logger.error(f"[Search] Query failed: {e}")
            raise


async def get_trending(
    limit: int = 50,
    min_viral_score: Optional[float] = None,
    niche: Optional[str] = None,
) -> List[dict]:
    """
    Get trending content sorted by viral score.

    Args:
        limit: Maximum number of results
        min_viral_score: Minimum viral score filter
        niche: Optional niche filter

    Returns:
        List of trending content candidates
    """
    logger = logging.getLogger(__name__)

    async with async_session_factory() as db:
        try:
            stmt = select(ContentCandidateDB)

            # Apply minimum viral score filter
            if min_viral_score is not None:
                stmt = stmt.where(ContentCandidateDB.viral_score >= min_viral_score)

            # Apply niche filter if provided
            if niche:
                stmt = stmt.where(ContentCandidateDB.niche == niche)

            # Order by viral score descending
            stmt = stmt.order_by(ContentCandidateDB.viral_score.desc()).limit(limit)

            result = await db.execute(stmt)
            rows = result.scalars().all()

            # Convert to dictionaries
            results = []
            for row in rows:
                results.append(
                    {
                        "id": row.id,
                        "platform": row.platform,
                        "external_id": row.external_id,
                        "title": row.title,
                        "description": row.description,
                        "creator_name": row.creator_name,
                        "creator_id": row.creator_id,
                        "url": row.url,
                        "thumbnail_url": row.thumbnail_url,
                        "published_at": row.published_at,
                        "scanned_at": row.scanned_at,
                        "duration_seconds": row.duration_seconds,
                        "view_count": row.view_count,
                        "like_count": row.like_count,
                        "comment_count": row.comment_count,
                        "share_count": row.share_count,
                        "engagement_score": row.engagement_score,
                        "viral_score": row.viral_score,
                        "category": row.category,
                        "tags": row.tags or [],
                        "niche": row.niche,
                        "metadata": row.metadata_json or {},
                    }
                )

            logger.info(f"[Trending] Returned {len(results)} trending items")
            return results

        except Exception as e:
            logger.error(f"[Trending] Query failed: {e}")
            raise
