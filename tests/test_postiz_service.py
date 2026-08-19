import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.distribution.postiz_service import base_postiz_service, PostizPublisherService, PostizPostResponse


@pytest.mark.asyncio
async def test_postiz_simulation_publish():
    # When no API key is provided, should default to successful simulation
    service = PostizPublisherService()
    service.api_key = ""

    response = await service.publish_video(
        video_path=None,
        caption="Check out this viral AI automation tip! #ai #trending",
        platforms=["tiktok", "youtube"],
    )

    assert isinstance(response, PostizPostResponse)
    assert response.success is True
    assert "tiktok" in response.platforms
    assert response.status == "published_simulation"


@pytest.mark.asyncio
async def test_postiz_api_dispatch():
    service = PostizPublisherService()
    service.api_key = "test_key"

    mock_client = AsyncMock()
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 201
    mock_post_resp.json.return_value = {"id": "post_999", "status": "ok"}
    mock_client.post.return_value = mock_post_resp

    with patch.object(service, "_client", mock_client):
        response = await service.publish_video(
            video_path=None,
            caption="High performance video",
            platforms=["youtube", "instagram"],
        )

        assert response.success is True
        assert response.post_id == "post_999"
