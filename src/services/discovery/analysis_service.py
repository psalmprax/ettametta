"""
Content analysis service for viral pattern detection.
Provides AI-powered analysis of content to extract topics, sentiment, viral potential, and keywords.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.utils.models import ContentCandidateDB


async def extract_content_patterns(
    content_id: str,
    db: AsyncSession,
    force: bool = False,
) -> dict[str, Any]:
    """
    Analyze content for viral patterns and insights.

    Args:
        content_id: The ID of the content to analyze
        db: Database session
        force: Force re-analysis even if already analyzed

    Returns:
        Analysis results dict with niches, sentiment, viral_potential, keywords
    """
    # Fetch content record
    stmt = select(ContentCandidateDB).filter(ContentCandidateDB.id == content_id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()

    if not content:
        raise ValueError(f"Content not found: {content_id}")

    # Return existing analysis if present and not forcing re-analysis
    if content.analysis_results and content.analyzed_at and not force:
        return content.analysis_results

    # Perform text analysis on title + description
    text_to_analyze = ""
    if content.title:
        text_to_analyze += content.title + " "
    if content.description:
        text_to_analyze += content.description

    # Basic text analysis (placeholder for full AI integration)
    # In production, this would call an LLM or NLP service
    analysis_results = _perform_pattern_analysis(text_to_analyze, content)

    # Update content with analysis results
    content.analysis_results = analysis_results
    content.analyzed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(content)

    return analysis_results


def _perform_pattern_analysis(text: str, content: ContentCandidateDB) -> dict[str, Any]:
    """
    Perform text analysis to extract niches, sentiment, viral potential, and keywords.

    This is a basic implementation. In production, replace with actual AI/NLP service.
    """
    text_lower = text.lower()

    # Basic keyword extraction (in production, use NLP/embedding-based extraction)
    all_keywords = []

    # Common viral content keywords
    viral_keywords = [
        "viral",
        "trend",
        "trending",
        "popular",
        "hit",
        "explode",
        "gone viral",
        "million",
        "billion",
        "views",
        "breaking",
        "news",
        "update",
        "reveal",
    ]
    for kw in viral_keywords:
        if kw in text_lower:
            all_keywords.append(kw)

    # Niche categorization (basic keyword matching)
    niches = []
    niche_keywords = {
        "entertainment": ["funny", "comedy", "laugh", "meme", "humor", "joke", "fail"],
        "education": [
            "learn",
            "tutorial",
            "how to",
            "guide",
            "explain",
            "teach",
            "course",
        ],
        "motivation": [
            "motivation",
            "inspire",
            "success",
            "mindset",
            "goal",
            "dream",
            "never give up",
        ],
        "gaming": [
            "game",
            "gaming",
            "play",
            "player",
            "level",
            "win",
            "lose",
            "stream",
        ],
        "tech": ["tech", "ai", "app", "software", "code", "programming", "computer"],
        "music": ["music", "song", "beat", "artist", "band", "album", "listen"],
        "sports": ["sport", "game", "team", "player", "win", "score", "match"],
        "fashion": ["fashion", "style", "clothes", "wear", "outfit", "trend"],
        "food": ["food", "recipe", "cook", "eat", "taste", "delicious", "homemade"],
        "news": ["news", "update", "breaking", "report", "story", "announce"],
    }
    for niche, keywords in niche_keywords.items():
        if any(kw in text_lower for kw in keywords):
            niches.append(niche)

    # Default to "entertainment" if no niches found
    if not niches:
        niches = ["entertainment"]

    # Sentiment analysis (basic rule-based)
    positive_words = [
        "amazing",
        "awesome",
        "great",
        "best",
        "love",
        "good",
        "perfect",
        "incredible",
    ]
    negative_words = [
        "bad",
        "terrible",
        "worst",
        "hate",
        "awful",
        "horrible",
        "fail",
        "loss",
    ]

    sentiment = "neutral"
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"

    # Viral potential estimation (based on engagement metrics)
    viral_potential = "low"
    if content.viral_score and content.viral_score >= 80:
        viral_potential = "high"
    elif content.viral_score and content.viral_score >= 50:
        viral_potential = "medium"
    elif content.engagement_score and content.engagement_score >= 5.0:
        viral_potential = "medium"

    # If content has significant view count, boost potential
    if content.view_count and content.view_count > 100000:
        viral_potential = "high"
    elif content.view_count and content.view_count > 10000:
        if viral_potential == "low":
            viral_potential = "medium"

    return {
        "niches": niches,
        "sentiment": sentiment,
        "viral_potential": viral_potential,
        "keywords": all_keywords[:10] if all_keywords else ["viral", "content"],
    }


async def get_persisted_analysis_report(
    content_id: str,
    db: AsyncSession,
) -> dict[str, Any] | None:
    """
    Retrieve existing analysis for content without performing new analysis.

    Args:
        content_id: The ID of the content
        db: Database session

    Returns:
        Analysis results dict or None if not yet analyzed
    """
    stmt = select(ContentCandidateDB).filter(ContentCandidateDB.id == content_id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()

    if not content:
        raise ValueError(f"Content not found: {content_id}")

    return content.analysis_results
