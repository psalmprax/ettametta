import pytest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import google.oauth2.credentials
from src.services.publishing.service import YouTubePublisher, PublishingService
import src.services.publishing.service as publishing_module


@pytest.fixture
def temp_token_dir(tmp_path):
    """Temporary token directory for publisher tests."""
    token_path = tmp_path / "tokens"
    yield token_path
    if token_path.exists():
        shutil.rmtree(token_path)


@pytest.mark.asyncio
async def test_youtube_publisher_get_credentials(temp_token_dir):
    """Verify loading YouTube credentials from json files."""
    publisher = YouTubePublisher()
    publisher.token_dir = temp_token_dir

    # 1. Test missing credentials
    assert publisher._get_credentials("user_missing") is None

    # 2. Test valid credentials file
    temp_token_dir.mkdir(parents=True, exist_ok=True)
    token_file = temp_token_dir / "youtube_user_ok.json"
    token_file.write_text(json.dumps({
        "token": "test_access_token",
        "refresh_token": "test_refresh_token"
    }))

    creds = publisher._get_credentials("user_ok")
    assert creds is not None
    assert creds.token == "test_access_token"
    assert creds.refresh_token == "test_refresh_token"


@pytest.mark.asyncio
async def test_youtube_upload_validation(temp_token_dir):
    """Verify YouTubePublisher validation checks (breaker, credentials)."""
    publisher = YouTubePublisher()
    publisher.token_dir = temp_token_dir

    # Mock availability check and patch asyncio.sleep to prevent tenacity sleep delays
    with patch("src.services.publishing.service.GOOGLE_API_AVAILABLE", True), \
         patch("asyncio.sleep", new_callable=AsyncMock):
         
        # 1. Circuit breaker is open
        publisher.breaker.state = "OPEN"
        with pytest.raises(RuntimeError) as excinfo:
            await publisher.upload_video(
                user_id="user1",
                video_path="test.mp4",
                title="Title",
                description="Desc",
                tags=[]
            )
        assert "blocked by CircuitBreaker" in str(excinfo.value)

        # 2. Credentials missing (will trigger retries, but sleep is mocked to be fast)
        publisher.breaker.reset()
        with pytest.raises(RuntimeError) as excinfo2:
            await publisher.upload_video(
                user_id="user_no_creds",
                video_path="test.mp4",
                title="Title",
                description="Desc",
                tags=[]
            )
        assert "account not connected" in str(excinfo2.value)


@pytest.mark.asyncio
async def test_youtube_upload_success(temp_token_dir, tmp_path):
    """Verify successful YouTube video upload path."""
    publisher = YouTubePublisher()
    publisher.token_dir = temp_token_dir

    # Setup dummy video file
    dummy_video = tmp_path / "dummy.mp4"
    dummy_video.write_text("dummy-content")

    # Setup dummy credentials
    temp_token_dir.mkdir(parents=True, exist_ok=True)
    token_file = temp_token_dir / "youtube_user123.json"
    token_file.write_text(json.dumps({
        "token": "token",
        "refresh_token": "refresh"
    }))

    mock_youtube_client = MagicMock()
    mock_insert_request = MagicMock()
    mock_insert_request.execute.return_value = {"id": "yt_video_id_999"}
    mock_youtube_client.videos().insert.return_value = mock_insert_request

    # Mock the API build and GOOGLE_API_AVAILABLE
    with patch("src.services.publishing.service.GOOGLE_API_AVAILABLE", True), \
         patch("src.services.publishing.service.build", return_value=mock_youtube_client), \
         patch("src.services.publishing.service.MediaFileUpload") as mock_media:

        res = await publisher.upload_video(
            user_id="user123",
            video_path=str(dummy_video),
            title="Cool Video Title",
            description="Awesome description",
            tags=["fun", "viral"],
            privacy_status="public"
        )
        assert res["platform"] == "youtube"
        assert res["video_id"] == "yt_video_id_999"
        assert "yt_video_id_999" in res["url"]
        assert res["status"] == "published"
        assert publisher.breaker.failure_count == 0


@pytest.mark.asyncio
async def test_publishing_service_tiktok_instagram_fallback():
    """Verify TikTok/Instagram publishing falls back to manual action when automation is not used."""
    service = PublishingService()
    
    metadata = {
        "title": "Fun Video",
        "description": "Look at this!",
        "tags": ["shorts", "reels"]
    }
    
    # Tiktok fallback
    res_tiktok = await service.publish_to_platform(
        user_id="user1",
        platform="tiktok",
        video_path="/path/to/my_video.mp4",
        metadata=metadata,
        use_automation=False
    )
    
    assert res_tiktok["platform"] == "tiktok"
    assert res_tiktok["status"] == "manual_action_required"
    assert "manual_action_required" in res_tiktok["status"]
    assert "caption" in res_tiktok
    assert "hashtags" in res_tiktok
    
    # Instagram fallback
    res_insta = await service.publish_to_platform(
        user_id="user1",
        platform="instagram",
        video_path="/path/to/my_video.mp4",
        metadata=metadata,
        use_automation=False
    )
    assert res_insta["platform"] == "instagram"
    assert res_insta["status"] == "manual_action_required"


@pytest.mark.asyncio
async def test_publishing_service_tiktok_automation():
    """Verify TikTok publishing automation logic with success and fail scenarios."""
    service = PublishingService()
    
    mock_publisher = AsyncMock()
    mock_publisher.post_to_tiktok.return_value = {
        "platform": "tiktok",
        "status": "published",
        "video_id": "tt123"
    }

    metadata = {"description": "cool desc", "tags": ["tag"]}

    # Bind mock_publisher to the module directly
    publishing_module.base_playwright_publisher = mock_publisher

    with patch("src.services.publishing.service.PLAYWRIGHT_AVAILABLE", True):
        # 1. Test successful automation
        res = await service.publish_to_platform(
            user_id="user1",
            platform="tiktok",
            video_path="/path/to/vid.mp4",
            metadata=metadata,
            use_automation=True
        )
        assert res["status"] == "published"
        assert service.automation_breaker.failure_count == 0

        # 2. Test automation exception fallback to manual
        mock_publisher.post_to_tiktok.side_effect = RuntimeError("Browser crashed")
        res_fail = await service.publish_to_platform(
            user_id="user1",
            platform="tiktok",
            video_path="/path/to/vid.mp4",
            metadata=metadata,
            use_automation=True
        )
        assert res_fail["status"] == "manual_action_required"
        assert service.automation_breaker.failure_count == 1


@pytest.mark.asyncio
async def test_publishing_service_multiple_platforms():
    """Verify publishing to multiple platforms in parallel."""
    service = PublishingService()
    
    # Mock publish_to_platform
    async def mock_publish(user_id, platform, video_path, metadata, use_automation=False):
        if platform == "youtube":
            return {"platform": "youtube", "status": "published", "video_id": "yt1"}
        elif platform == "tiktok":
            return {"platform": "tiktok", "status": "manual_action_required"}
        else:
            raise ValueError(f"Unknown platform {platform}")

    with patch.object(service, "publish_to_platform", side_effect=mock_publish):
        res = await service.publish_to_multiple(
            user_id="user1",
            platforms=["youtube", "tiktok"],
            video_path="/path/to/vid.mp4",
            metadata={"title": "Vid"}
        )
        
        assert res["published"] == 1
        assert res["failed"] == 1
        assert res["total"] == 2
        assert len(res["results"]) == 2
        assert res["results"][0]["platform"] == "youtube"
        assert res["results"][1]["platform"] == "tiktok"
