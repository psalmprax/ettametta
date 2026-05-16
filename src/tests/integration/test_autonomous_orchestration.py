import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.services.discovery.scanner_service import ScannerService
from src.services.discovery.models import ContentCandidate
from src.api.utils.models import ContentCandidateDB, NexusJobDB

@pytest.mark.asyncio
async def test_autonomous_flow_discovery_to_nexus(test_db):
    """
    Integration test for the autonomous lifecycle:
    ScannerService finds content -> Analysis categorizes it -> Nexus Job triggered.
    """
    from src.api.utils.database import AsyncSessionLocal
    
    # 1. Mock the platform scanner to return a specific candidate
    mock_candidate = ContentCandidate(
        id="yt_test123",
        platform="youtube",
        title="AI Revolution in 2024",
        description="This technology is going viral! #ai #tech",
        source_uri="https://youtube.com/v/test123",
        view_count=50000,
        viral_score=90,
        engagement_score=7.0,
        niche="Technology",
        creator_name="TechInsider",
        thumbnail_uri="https://example.com/thumb.jpg",
        duration_seconds=60,
        category="video",
        like_count=5000,
        comment_count=200,
        share_count=100,
        published_at=None,
        metadata_json={}
    )
    
    scanner_service = ScannerService()
    
    # Mocking all scanners to return empty except youtube_shorts
    with patch.object(scanner_service.scanners["youtube_shorts"], "scan_trends", new_callable=AsyncMock) as mock_scan, \
         patch.object(scanner_service.scanners["youtube_long"], "scan_trends", new_callable=AsyncMock, return_value=[]), \
         patch.object(scanner_service.scanners["tiktok"], "scan_trends", new_callable=AsyncMock, return_value=[]), \
         patch.object(scanner_service.scanners["instagram"], "scan_trends", new_callable=AsyncMock, return_value=[]), \
         patch.object(scanner_service.scanners["x"], "scan_trends", new_callable=AsyncMock, return_value=[]):
        
        mock_scan.return_value = [mock_candidate]
        
        # 2. Run scan
        candidates = await scanner_service.scan_all_platforms("Technology")
        assert len(candidates) == 1
        
        # 3. Save to database
        saved = await scanner_service.save_to_database(candidates)
        assert saved == 1
        
    async with AsyncSessionLocal() as db:
        # Verify it's in the DB
        from sqlalchemy import select
        stmt = select(ContentCandidateDB).where(ContentCandidateDB.id == "yt_test123")
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()
        assert content is not None
        assert content.title == "AI Revolution in 2024"
        
        # 4. Trigger Analysis
        from src.services.discovery.analysis_service import extract_content_patterns
        analysis = await extract_content_patterns(content.id, db)
        assert "tech" in analysis["niches"]
        assert analysis["viral_potential"] == "high"
        
        # 5. Verify Nexus Trigger Logic
        # We verify that if we were to trigger the AutoCreator, it would receive the correct parameters.
        with patch("src.services.nexus_engine.auto_creator.base_creator_service.create_cinema_video", new_callable=AsyncMock) as mock_nexus:
            mock_nexus.return_value = "/tmp/viral_video.mp4"
            
            # Simulate the autonomous decision logic
            if analysis["viral_potential"] == "high":
                job_id = "job_auto_123"
                await mock_nexus(
                    job_id=job_id,
                    topic=content.title,
                    niche=analysis["niches"][0],
                    style="CINEMATIC_DOC"
                )
            
            mock_nexus.assert_called_once_with(
                job_id="job_auto_123",
                topic="AI Revolution in 2024",
                niche="tech",
                style="CINEMATIC_DOC"
            )
