import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.discovery.analysis_service import extract_content_patterns
from src.api.utils.models import ContentCandidateDB

@pytest.mark.asyncio
async def test_extract_content_patterns_real_flow(test_db):
    """
    Integration test for the AnalysisService.
    Verifies pattern extraction and database persistence.
    """
    from src.api.utils.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        # 1. Setup test data
        content_id = f"yt_{uuid.uuid4().hex[:8]}"
        content = ContentCandidateDB(
            id=content_id,
            platform="youtube",
            external_id=content_id,
            title="Viral AI Revolution: This technology is exploding!",
            description="Everyone is talking about how AI is changing the world. #trending #viral",
            view_count=150000,
            viral_score=85,
            engagement_score=8.5
        )
        db.add(content)
        await db.commit()

        # 2. Execute analysis
        results = await extract_content_patterns(content_id, db)

        # 3. Verify results
        # Based on analysis_service.py logic:
        # "tech" matches ["tech", "ai", ...]
        assert "tech" in results["niches"]
        # "amazing", "great", etc. not in text, but no negative words either -> neutral or positive if words found
        # Actually "exploding" is not in positive_words, so it might be neutral unless we add more.
        # Wait, I'll use a positive word to be sure.
        
        assert results["viral_potential"] == "high" # view_count > 100k or viral_score >= 80
        assert "viral" in results["keywords"]

        # 4. Verify DB update
        await db.refresh(content)
        assert content.analysis_results == results
        assert content.analyzed_at is not None

@pytest.mark.asyncio
async def test_extract_content_patterns_sentiment(test_db):
    """Test sentiment detection logic."""
    from src.api.utils.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        content_id = f"yt_{uuid.uuid4().hex[:8]}"
        content = ContentCandidateDB(
            id=content_id,
            platform="tiktok",
            external_id=content_id,
            title="This is an amazing and great hit!",
            description="I love this so much, best thing ever.",
            view_count=100
        )
        db.add(content)
        await db.commit()

        results = await extract_content_patterns(content_id, db)
        assert results["sentiment"] == "positive"
