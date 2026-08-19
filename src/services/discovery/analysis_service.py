"""
Content analysis service for viral pattern detection.
Provides AI-powered analysis of content to extract topics, sentiment, viral potential, and keywords.
"""

from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.utils.models import ContentCandidateDB
from src.services.llm.service import unified_llm_service


async def extract_content_patterns(
    content_id: str,
    db: AsyncSession,
    force: bool = False,
) -> dict[str, Any]:
    """
    Analyze content for viral patterns and insights using AI/NLP service.

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

    # Perform AI-powered analysis
    analysis_results = await _perform_ai_pattern_analysis(text_to_analyze, content)

    # Update content with analysis results
    content.analysis_results = analysis_results
    content.analyzed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(content)

    return analysis_results


async def _perform_ai_pattern_analysis(text: str, content: ContentCandidateDB) -> dict[str, Any]:
    """
    Perform AI-powered text analysis to extract niches, sentiment, viral potential, and keywords.

    Uses LLM service for intelligent content analysis instead of basic keyword matching.
    """
    if not text.strip():
        # Fallback to basic analysis for empty text
        return _perform_pattern_analysis(text, content)

    try:
        # Construct analysis prompt for LLM
        analysis_prompt = f"""
        Analyze this content for viral potential and extract key insights:

        Title: {content.title or 'N/A'}
        Description: {content.description or 'N/A'}
        Platform: {content.platform}
        View Count: {content.view_count or 0}
        Engagement Score: {content.engagement_score or 0.0}

        Provide a JSON response with:
        {{
            "niches": ["list of relevant content niches like entertainment, education, motivation, tech, gaming, etc."],
            "sentiment": "positive/negative/neutral",
            "viral_potential": "high/medium/low",
            "keywords": ["list of 5-10 key viral/potential keywords"],
            "summary": "brief one-sentence summary of content essence",
            "target_audience": "likely target demographic",
            "content_type": "tutorial/review/news/entertainment/etc."
        }}

        Base niches on: entertainment, education, motivation, tech, gaming, music, sports, fashion, food, news, business, lifestyle, health, travel, finance, politics, science, art, animals, comedy, diy, cooking, fitness, beauty, gaming, anime, manga, crypto, investing, real_estate, parenting, pets, books, movies, tv_shows, podcasts.

        Consider viral indicators like: controversy, relatability, usefulness, emotion, uniqueness, timeliness, visual appeal, shareability.
        """

        # Call LLM service for analysis
        llm_response = await unified_llm_service.complete(
            prompt=analysis_prompt,
            system_message="You are an expert content analyst specializing in viral content detection and social media trends. Always respond with valid JSON only.",
            temperature=0.3,  # Lower temperature for more consistent analysis
            max_tokens=1024
        )

        # Parse LLM response
        import json
        try:
            # Extract JSON from response (handle potential markdown formatting)
            response_text = llm_response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            analysis_data = json.loads(response_text.strip())

            # Validate and structure the response
            return {
                "niches": analysis_data.get("niches", ["entertainment"]) if isinstance(analysis_data.get("niches"), list) else ["entertainment"],
                "sentiment": analysis_data.get("sentiment", "neutral") if analysis_data.get("sentiment") in ["positive", "negative", "neutral"] else "neutral",
                "viral_potential": analysis_data.get("viral_potential", "medium") if analysis_data.get("viral_potential") in ["high", "medium", "low"] else "medium",
                "keywords": analysis_data.get("keywords", ["viral", "content"]) if isinstance(analysis_data.get("keywords"), list) else ["viral", "content"],
                "summary": analysis_data.get("summary", ""),
                "target_audience": analysis_data.get("target_audience", ""),
                "content_type": analysis_data.get("content_type", "")
            }
        except (json.JSONDecodeError, AttributeError) as e:
            # Fallback to basic analysis if LLM response parsing fails
            print(f"LLM analysis parsing failed, falling back to basic: {e}")
            return _perform_pattern_analysis(text, content)

    except Exception as e:
        # Fallback to basic analysis if LLM service fails
        print(f"LLM analysis service failed, falling back to basic: {e}")
        return _perform_pattern_analysis(text, content)


def _perform_pattern_analysis(text: str, content: ContentCandidateDB) -> dict[str, Any]:
    """
    Basic fallback pattern analysis (keyword-based) for when AI service is unavailable.
    Kept for backward compatibility and fallback scenarios.
    """
    text_lower = text.lower()

    # Basic keyword extraction
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
