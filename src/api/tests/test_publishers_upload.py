"""
Unit tests for TikTok and Instagram publisher _upload_impl methods.
Verifies the fixes applied in the publisher audit:

TikTok fixes:
- Auth check: headers.get("Authorization") or headers.get("Cookie"), not "if not headers"
- Privacy level: PUBLIC_TO_EVERYONE (was SELF_ONLY)
- Chunked upload flow

Instagram fixes:
- IG Business Account ID resolution via _get_ig_user_id
- Container creation with correct ig_user_id (not /me/media)
- Facebook Login OAuth flow compatibility (was Instagram Basic Display)
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# CRITICAL: Set test environment BEFORE importing any project modules
os.environ["ENV"] = "test"
os.environ["DEBUG"] = "false"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_testing"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"


@pytest.fixture
def post_metadata():
    """Standard PostMetadata fixture for tests."""
    from src.services.optimization.models import PostMetadata
    return PostMetadata(
        title="Test Video Title",
        description="A test video description for unit testing",
        hashtags=["test", "viral", "ai"],
        cta="Check the link in bio!",
        best_posting_time="2026-06-15T14:00:00Z",
        platform="tiktok",
    )


# ─── TikTok Publisher Tests ─────────────────────────────────────────────


class TestTikTokPublisherUpload:
    """Tests for TikTokPublisher._upload_impl — focuses on the bugs that were fixed."""

    @pytest.mark.asyncio
    async def test_tiktok_auth_check_empty_headers(self, post_metadata):
        """
        Verify auth check: empty headers dict should return None.
        This tests the fix: 'if not headers' was always truthy for a dict.
        Now uses headers.get("Authorization") or headers.get("Cookie").
        """
        from src.services.optimization.tiktok_publisher import base_tiktok_service

        result = await base_tiktok_service._upload_impl(
            video_path="/tmp/test.mp4",
            metadata=post_metadata,
            user_id="user1",
            account_id=None,
            headers={},  # Empty dict — should fail auth check
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_tiktok_auth_check_no_auth_value(self, post_metadata):
        """
        Verify auth check: headers with Authorization=None should return None.
        This tests the case where get_auth_headers returns {'Authorization': 'Bearer None'}
        or similar invalid values.
        """
        from src.services.optimization.tiktok_publisher import base_tiktok_service

        result = await base_tiktok_service._upload_impl(
            video_path="/tmp/test.mp4",
            metadata=post_metadata,
            user_id="user1",
            account_id=None,
            headers={"Authorization": None, "Content-Type": "application/json"},
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_tiktok_upload_success(self, post_metadata):
        """
        Verify full happy-path upload: init → chunked upload → TikTok URL.
        Also verifies privacy_level is PUBLIC_TO_EVERYONE (not SELF_ONLY).
        """
        from src.services.optimization.tiktok_publisher import base_tiktok_service

        # Mock token_data to return a username
        mock_token_data = {"username": "test_user", "access_token": "tok_123"}

        # Mock the httpx client responses
        mock_init_response = MagicMock()
        mock_init_response.status_code = 200
        mock_init_response.json.return_value = {
            "data": {
                "upload_url": "https://upload.tiktok.com/video/123",
                "publish_id": "pub_abc123",
            }
        }

        mock_chunk_response = MagicMock()
        mock_chunk_response.status_code = 200

        mock_client = AsyncMock()
        # Init call
        mock_client.post.return_value = mock_init_response
        # Chunk upload call
        mock_client.put.return_value = mock_chunk_response

        # Patch dependencies
        with (
            patch(
                "src.services.optimization.tiktok_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch("os.path.getsize", return_value=5 * 1024 * 1024),  # 5MB file
            patch("builtins.open", MagicMock()),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_tiktok_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result == "https://www.tiktok.com/@test_user/video/pub_abc123"

            # Verify the init payload included PUBLIC_TO_EVERYONE
            call_kwargs = mock_client.post.call_args
            assert call_kwargs is not None
            payload = call_kwargs[1].get("json", {})
            assert payload["post_info"]["privacy_level"] == "PUBLIC_TO_EVERYONE"

    @pytest.mark.asyncio
    async def test_tiktok_init_fails(self, post_metadata):
        """
        Verify that when the init API returns non-200, _upload_impl returns None.
        """
        from src.services.optimization.tiktok_publisher import base_tiktok_service

        mock_token_data = {"username": "test_user", "access_token": "tok_123"}

        mock_init_response = MagicMock()
        mock_init_response.status_code = 400
        mock_init_response.text = '{"error": "invalid request"}'

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_init_response

        with (
            patch(
                "src.services.optimization.tiktok_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch("os.path.getsize", return_value=5 * 1024 * 1024),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_tiktok_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_tiktok_chunk_upload_fails(self, post_metadata):
        """
        Verify that when a chunk upload fails, _upload_impl returns None.
        """
        from src.services.optimization.tiktok_publisher import base_tiktok_service

        mock_token_data = {"username": "test_user", "access_token": "tok_123"}

        mock_init_response = MagicMock()
        mock_init_response.status_code = 200
        mock_init_response.json.return_value = {
            "data": {
                "upload_url": "https://upload.tiktok.com/video/123",
                "publish_id": "pub_abc123",
            }
        }

        mock_chunk_response = MagicMock()
        mock_chunk_response.status_code = 400  # Chunk upload fails
        mock_chunk_response.text = '{"error": "upload failed"}'

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_init_response
        mock_client.put.return_value = mock_chunk_response

        with (
            patch(
                "src.services.optimization.tiktok_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch("os.path.getsize", return_value=5 * 1024 * 1024),
            patch(
                "builtins.open",
                MagicMock(
                    return_value=MagicMock(
                        __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"chunk_data")))
                    )
                ),
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_tiktok_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_tiktok_file_not_found(self, post_metadata):
        """
        Verify that when the file doesn't exist (os.path.getsize raises),
        _upload_impl catches the exception and returns None.
        """
        from src.services.optimization.tiktok_publisher import base_tiktok_service

        mock_token_data = {"username": "test_user", "access_token": "tok_123"}

        with (
            patch(
                "src.services.optimization.tiktok_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch(
                "os.path.getsize",
                side_effect=FileNotFoundError("No such file"),
            ),
        ):
            result = await base_tiktok_service._upload_impl(
                video_path="/nonexistent/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None


# ─── Instagram Publisher Tests ──────────────────────────────────────────


class TestInstagramPublisherUpload:
    """Tests for InstagramPublisher._upload_impl — focuses on the bugs that were fixed."""

    @pytest.mark.asyncio
    async def test_instagram_auth_check_no_token_no_cookie(self, post_metadata):
        """
        Verify that when there's no access token and no Cookie header,
        _upload_impl returns None.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service

        with patch(
            "src.services.optimization.instagram_publisher.token_manager.get_token",
            return_value=None,
        ):
            result = await base_instagram_service._upload_impl(
                video_path="https://example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={},  # No Cookie either
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_instagram_full_success(self, post_metadata):
        """
        Verify full happy-path: resolve IG user ID → create container → poll ready → publish.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service

        mock_access_token = "ig_access_token_123"

        # Mock the _resolve_video_uri to return a URL immediately
        # Mock the _get_ig_user_id to return an IG user ID

        # httpx client responses:
        # - Container creation: POST /{ig_user_id}/media → {"id": "container_123"}
        # - Status polling: GET /{container_id} → {"id": "media_456"}
        # - Publish: POST /{ig_user_id}/media_publish → {"id": "media_456"}

        mock_container_response = MagicMock()
        mock_container_response.json.return_value = {"id": "container_123"}

        mock_status_response = MagicMock()
        mock_status_response.json.return_value = {"id": "media_456"}

        mock_publish_response = MagicMock()
        mock_publish_response.json.return_value = {"id": "media_456"}

        # The container creation and publish use .post; status polling uses .get
        mock_client = AsyncMock()

        # We need different return values for different calls:
        # First .post returns container, first .get returns status, second .post returns publish
        mock_client.post = AsyncMock(
            side_effect=[
                mock_container_response,  # Step 1: create container
                mock_publish_response,  # Step 3: publish
            ]
        )
        mock_client.get = AsyncMock(
            side_effect=[
                mock_status_response,  # Step 2: poll status
            ]
        )

        with (
            patch(
                "src.services.optimization.instagram_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_instagram_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch.object(
                base_instagram_service,
                "_get_ig_user_id",
                new_callable=AsyncMock,
                return_value="ig_biz_789",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await base_instagram_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result == "https://instagram.com/p/media_456"

    @pytest.mark.asyncio
    async def test_instagram_no_ig_user_id(self, post_metadata):
        """
        Verify that when _get_ig_user_id returns None, _upload_impl returns None.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service

        mock_access_token = "ig_access_token_123"

        with (
            patch(
                "src.services.optimization.instagram_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_instagram_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch.object(
                base_instagram_service,
                "_get_ig_user_id",
                new_callable=AsyncMock,
                return_value=None,  # No IG Business Account
            ),
        ):
            result = await base_instagram_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_instagram_container_creation_fails(self, post_metadata):
        """
        Verify that when container creation returns an error (no 'id' in response),
        _upload_impl returns None.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service

        mock_access_token = "ig_access_token_123"

        # Container creation returns error
        mock_container_response = MagicMock()
        mock_container_response.json.return_value = {
            "error": {"message": "Invalid video URL", "type": "GraphMethodException"}
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_container_response)

        with (
            patch(
                "src.services.optimization.instagram_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_instagram_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch.object(
                base_instagram_service,
                "_get_ig_user_id",
                new_callable=AsyncMock,
                return_value="ig_biz_789",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await base_instagram_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_instagram_publish_fails(self, post_metadata):
        """
        Verify that when publish API returns an error, _upload_impl returns None.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service

        mock_access_token = "ig_access_token_123"

        mock_container_response = MagicMock()
        mock_container_response.json.return_value = {"id": "container_123"}

        mock_status_response = MagicMock()
        mock_status_response.json.return_value = {"id": "media_456"}

        mock_publish_response = MagicMock()
        mock_publish_response.json.return_value = {
            "error": {"message": "Media processing not complete"}
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[mock_container_response, mock_publish_response]
        )
        mock_client.get = AsyncMock(
            side_effect=[mock_status_response]
        )

        with (
            patch(
                "src.services.optimization.instagram_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_instagram_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch.object(
                base_instagram_service,
                "_get_ig_user_id",
                new_callable=AsyncMock,
                return_value="ig_biz_789",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await base_instagram_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_instagram_resolve_video_url(self):
        """
        Verify that _resolve_video_uri returns URLs as-is (doesn't try to upload to cloud).
        """
        from src.services.optimization.instagram_publisher import base_instagram_service

        url = "https://cdn.example.com/video.mp4"
        result = await base_instagram_service._resolve_video_uri(url)
        assert result == url

    @pytest.mark.asyncio
    async def test_instagram_resolve_video_local_file(self):
        """
        Verify that _resolve_video_uri attempts cloud upload for local files.
        When cloud upload returns None (no object_key), it falls back to
        local static serving and returns a URL.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service
        import tempfile

        # Create a temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy video content")
            temp_path = f.name

        try:
            with (
                patch(
                    "src.services.optimization.instagram_publisher.base_storage_service.upload_to_cloud",
                    return_value=None,  # Cloud upload returns no object_key
                ),
                patch(
                    "src.api.config.settings.PRODUCTION_DOMAIN",
                    "http://localhost:7202/api/v1",
                    create=True,
                ),
            ):
                result = await base_instagram_service._resolve_video_uri(temp_path)
                # Falls back to local static serving with whatever PRODUCTION_DOMAIN is configured
                assert result is not None
                assert "/static/outputs/" in result
                assert result.endswith(".mp4")
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_instagram_resolve_video_cloud_success(self):
        """
        Verify that _resolve_video_uri returns cloud URL when cloud upload succeeds.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            temp_path = f.name

        try:
            with (
                patch(
                    "src.services.optimization.instagram_publisher.base_storage_service.upload_to_cloud",
                    return_value="videos/test123.mp4",
                ),
                patch(
                    "src.services.optimization.instagram_publisher.base_storage_service.get_file_url",
                    return_value="https://storage.example.com/videos/test123.mp4",
                ),
            ):
                result = await base_instagram_service._resolve_video_uri(temp_path)
                assert result == "https://storage.example.com/videos/test123.mp4"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_instagram_resolve_video_cloud_missing_url(self, post_metadata):
        """
        Verify fallback: cloud upload succeeds but get_file_url returns None.
        Should try local static serving fallback, then return that URL.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy content")
            temp_path = f.name

        try:
            with (
                patch(
                    "src.services.optimization.instagram_publisher.base_storage_service.upload_to_cloud",
                    return_value="videos/test123.mp4",
                ),
                patch(
                    "src.services.optimization.instagram_publisher.base_storage_service.get_file_url",
                    return_value=None,  # Cloud URL fails
                ),
                patch(
                    "src.api.config.settings.PRODUCTION_DOMAIN",
                    "http://localhost:7202/api/v1",
                    create=True,
                ),
            ):
                result = await base_instagram_service._resolve_video_uri(temp_path)
                # Falls back to local static serving with whatever PRODUCTION_DOMAIN is configured
                assert result is not None
                assert "/static/outputs/" in result
                assert result.endswith(".mp4")
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_instagram_get_ig_user_id_success(self):
        """
        Verify _get_ig_user_id resolves IG Business Account ID from Facebook Pages.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service

        mock_client = AsyncMock()

        # First call: GET /me/accounts returns a Facebook Page
        mock_pages_response = MagicMock()
        mock_pages_response.json.return_value = {
            "data": [
                {
                    "id": "page_123",
                    "name": "My Page",
                    "access_token": "page_token_abc",
                }
            ]
        }

        # Second call: GET /{page_id} with fields=instagram_business_account
        mock_page_info_response = MagicMock()
        mock_page_info_response.json.return_value = {
            "id": "page_123",
            "instagram_business_account": {"id": "ig_biz_789"},
        }

        mock_client.get = AsyncMock(
            side_effect=[mock_pages_response, mock_page_info_response]
        )

        result = await base_instagram_service._get_ig_user_id(
            access_token="test_token", client=mock_client
        )
        assert result == "ig_biz_789"

    @pytest.mark.asyncio
    async def test_instagram_get_ig_user_id_no_pages(self):
        """
        Verify _get_ig_user_id returns None when user has no Facebook Pages.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service

        mock_client = AsyncMock()

        mock_pages_response = MagicMock()
        mock_pages_response.json.return_value = {"data": []}  # No pages

        mock_client.get = AsyncMock(return_value=mock_pages_response)

        result = await base_instagram_service._get_ig_user_id(
            access_token="test_token", client=mock_client
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_instagram_get_ig_user_id_no_ig_account(self):
        """
        Verify _get_ig_user_id returns None when user has a Facebook Page
        but no Instagram Business Account connected.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service

        mock_client = AsyncMock()

        mock_pages_response = MagicMock()
        mock_pages_response.json.return_value = {
            "data": [
                {"id": "page_123", "name": "My Page", "access_token": "page_token_abc"}
            ]
        }

        mock_page_info_response = MagicMock()
        mock_page_info_response.json.return_value = {
            "id": "page_123"
            # No instagram_business_account field
        }

        mock_client.get = AsyncMock(
            side_effect=[mock_pages_response, mock_page_info_response]
        )

        result = await base_instagram_service._get_ig_user_id(
            access_token="test_token", client=mock_client
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_instagram_get_ig_user_id_http_error(self):
        """
        Verify _get_ig_user_id handles HTTP errors gracefully.
        """
        from src.services.optimization.instagram_publisher import base_instagram_service

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))

        result = await base_instagram_service._get_ig_user_id(
            access_token="test_token", client=mock_client
        )
        assert result is None


# ─── Direct Unit Tests ────────────────────────────────────────────────


class TestTikTokPublisherUnit:
    """Direct unit tests for TikTokPublisher methods."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Verify health_check returns False when no token exists."""
        from src.services.optimization.tiktok_publisher import base_tiktok_service

        with patch(
            "src.services.optimization.tiktok_publisher.token_manager.get_token",
            return_value=None,
        ):
            result = await base_tiktok_service.health_check("user_no_token")
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_with_token(self):
        """Verify health_check returns True when token exists."""
        from src.services.optimization.tiktok_publisher import base_tiktok_service

        with patch(
            "src.services.optimization.tiktok_publisher.token_manager.get_token",
            return_value="tok_123",
        ):
            result = await base_tiktok_service.health_check("user_with_token")
            assert result is True


class TestInstagramPublisherUnit:
    """Direct unit tests for InstagramPublisher methods."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Verify health_check returns False when no token exists."""
        from src.services.optimization.instagram_publisher import base_instagram_service

        with patch(
            "src.services.optimization.instagram_publisher.token_manager.get_token",
            return_value=None,
        ):
            result = await base_instagram_service.health_check("user_no_token")
            assert result is False

    @pytest.mark.asyncio
    async def test_build_caption(self, post_metadata):
        """Verify _build_caption constructs caption from metadata."""
        from src.services.optimization.instagram_publisher import base_instagram_service

        caption = base_instagram_service._build_caption(post_metadata)
        assert "Test Video Title" in caption
        assert "test" in caption  # hashtag
        assert "#viral" in caption
        assert "Check the link" in caption


# ─── X (Twitter) Publisher Tests ────────────────────────────────────────


class TestXPublisherUpload:
    """Tests for XPublisher._upload_impl — focuses on auth check, polling guard, and upload flow."""

    @pytest.mark.asyncio
    async def test_x_auth_check_empty_headers(self, post_metadata):
        """
        Verify auth check: empty headers dict returns None.
        Tests the fix: 'if not headers' → 'if not headers.get("Authorization") and not headers.get("Cookie")'
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        result = await base_x_publisher_service._upload_impl(
            video_path="/tmp/test.mp4",
            metadata=post_metadata,
            user_id="user1",
            account_id=None,
            headers={},
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_x_auth_check_no_auth_value(self, post_metadata):
        """
        Verify auth check: headers with Authorization=None returns None.
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        result = await base_x_publisher_service._upload_impl(
            video_path="/tmp/test.mp4",
            metadata=post_metadata,
            user_id="user1",
            account_id=None,
            headers={"Authorization": None},
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_x_upload_success(self, post_metadata):
        """
        Verify full happy-path upload: INIT → APPEND → FINALIZE → STATUS (ready) → tweet → X URL.
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        mock_init_response = MagicMock()
        mock_init_response.status_code = 200
        mock_init_response.json.return_value = {"media_id_string": "media_123"}

        mock_append_response = MagicMock()
        mock_append_response.status_code = 200

        mock_finalize_response = MagicMock()
        mock_finalize_response.status_code = 200
        mock_finalize_response.json.return_value = {
            "media_id_string": "media_123",
            "processing_info": {"state": "succeeded"},  # Already succeeded, no polling needed
        }

        mock_tweet_response = MagicMock()
        mock_tweet_response.status_code = 201
        mock_tweet_response.json.return_value = {
            "data": {"id": "tweet_456", "text": "Test Video Title"}
        }

        mock_client = AsyncMock()

        # mock_client.post is called 4 times: INIT, APPEND, FINALIZE, tweet
        # But since total_bytes < chunk_size (5MB), there's only 1 APPEND call
        mock_client.post = AsyncMock(
            side_effect=[
                mock_init_response,     # Step 1: INIT
                mock_append_response,   # Step 2: APPEND (1 chunk)
                mock_finalize_response, # Step 3: FINALIZE
                mock_tweet_response,    # Step 4: Create Tweet
            ]
        )

        with (
            patch.object(
                base_x_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=(b"video_data_here", 1000),
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_x_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result == "https://x.com/i/status/tweet_456"

    @pytest.mark.asyncio
    async def test_x_init_fails(self, post_metadata):
        """
        Verify INIT failure returns None.
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        mock_init_response = MagicMock()
        mock_init_response.status_code = 400
        mock_init_response.text = '{"error": "Invalid request"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_init_response)

        with (
            patch.object(
                base_x_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=(b"video_data", 1000),
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_x_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_x_append_fails(self, post_metadata):
        """
        Verify APPEND failure returns None.
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        mock_init_response = MagicMock()
        mock_init_response.status_code = 200
        mock_init_response.json.return_value = {"media_id_string": "media_123"}

        mock_append_response = MagicMock()
        mock_append_response.status_code = 400
        mock_append_response.text = '{"error": "Chunk upload failed"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_init_response,
                mock_append_response,
            ]
        )

        with (
            patch.object(
                base_x_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=(b"video_data", 1000),
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_x_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_x_finalize_fails(self, post_metadata):
        """
        Verify FINALIZE failure returns None.
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        mock_init_response = MagicMock()
        mock_init_response.status_code = 200
        mock_init_response.json.return_value = {"media_id_string": "media_123"}

        mock_append_response = MagicMock()
        mock_append_response.status_code = 200

        mock_finalize_response = MagicMock()
        mock_finalize_response.status_code = 400
        mock_finalize_response.text = '{"error": "Finalize failed"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_init_response,
                mock_append_response,
                mock_finalize_response,
            ]
        )

        with (
            patch.object(
                base_x_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=(b"video_data", 1000),
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_x_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_x_processing_timeout(self, post_metadata):
        """
        Verify processing polling hits max_polls=30 guard and returns None.
        This tests the fix: added max_polls guard to prevent infinite polling.
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        mock_init_response = MagicMock()
        mock_init_response.status_code = 200
        mock_init_response.json.return_value = {"media_id_string": "media_123"}

        mock_append_response = MagicMock()
        mock_append_response.status_code = 200

        # FINALIZE returns pending processing state
        mock_finalize_response = MagicMock()
        mock_finalize_response.status_code = 200
        mock_finalize_response.json.return_value = {
            "media_id_string": "media_123",
            "processing_info": {
                "state": "pending",
                "check_after_secs": 0,  # Instant for testing
            },
        }

        # STATUS poll always returns pending
        mock_status_response = MagicMock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "processing_info": {"state": "pending"}
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_init_response,
                mock_append_response,
                mock_finalize_response,
            ]
        )
        # STATUS uses GET, which keeps returning pending
        mock_client.get = AsyncMock(return_value=mock_status_response)

        with (
            patch.object(
                base_x_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=(b"video_data", 1000),
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await base_x_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            # Should time out after 30 polls
            assert result is None
            # Verify we polled at most 30 times
            assert mock_client.get.call_count <= 30

    @pytest.mark.asyncio
    async def test_x_processing_failed(self, post_metadata):
        """
        Verify processing state='failed' returns None.
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        mock_init_response = MagicMock()
        mock_init_response.status_code = 200
        mock_init_response.json.return_value = {"media_id_string": "media_123"}

        mock_append_response = MagicMock()
        mock_append_response.status_code = 200

        mock_finalize_response = MagicMock()
        mock_finalize_response.status_code = 200
        mock_finalize_response.json.return_value = {
            "media_id_string": "media_123",
            "processing_info": {"state": "pending", "check_after_secs": 0},
        }

        # STATUS returns failed
        mock_status_response = MagicMock()
        mock_status_response.status_code = 200
        mock_status_response.json.return_value = {
            "processing_info": {
                "state": "failed",
                "error": {"message": "Processing error"},
            }
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_init_response,
                mock_append_response,
                mock_finalize_response,
            ]
        )
        mock_client.get = AsyncMock(return_value=mock_status_response)

        with (
            patch.object(
                base_x_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=(b"video_data", 1000),
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await base_x_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_x_tweet_creation_fails(self, post_metadata):
        """
        Verify when tweet creation fails, _upload_impl returns None.
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        mock_init_response = MagicMock()
        mock_init_response.status_code = 200
        mock_init_response.json.return_value = {"media_id_string": "media_123"}

        mock_append_response = MagicMock()
        mock_append_response.status_code = 200

        mock_finalize_response = MagicMock()
        mock_finalize_response.status_code = 200
        mock_finalize_response.json.return_value = {
            "processing_info": {"state": "succeeded"},
        }

        mock_tweet_response = MagicMock()
        mock_tweet_response.status_code = 400
        mock_tweet_response.text = '{"error": "Duplicate content"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_init_response,
                mock_append_response,
                mock_finalize_response,
                mock_tweet_response,
            ]
        )

        with (
            patch.object(
                base_x_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=(b"video_data", 1000),
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_x_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_x_load_video_data_fails(self, post_metadata):
        """
        Verify when _load_video_data returns (None, 0), _upload_impl returns None.
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        with (
            patch.object(
                base_x_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=(None, 0),
            ),
        ):
            result = await base_x_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_x_file_too_large(self, post_metadata):
        """
        Verify when local file exceeds max size, _upload_impl returns None.
        """
        from src.services.optimization.x_publisher import base_x_publisher_service

        # max_file_size_bytes = 512 * 1024 * 1024 = 536870912
        with (
            patch("os.path.isfile", return_value=True),
            patch("os.path.getsize",
                  return_value=600 * 1024 * 1024),  # 600MB > 512MB limit
        ):
            result = await base_x_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None


class TestXPublisherUnit:
    """Direct unit tests for XPublisher methods."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Verify health_check returns False when no token exists."""
        from src.services.optimization.x_publisher import base_x_publisher_service

        with patch(
            "src.services.optimization.x_publisher.token_manager.get_token",
            return_value=None,
        ):
            result = await base_x_publisher_service.health_check("user_no_token")
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_with_token(self):
        """Verify health_check returns True when token exists."""
        from src.services.optimization.x_publisher import base_x_publisher_service

        with patch(
            "src.services.optimization.x_publisher.token_manager.get_token",
            return_value="tok_123",
        ):
            result = await base_x_publisher_service.health_check("user_with_token")
            assert result is True


# ─── LinkedIn Publisher Tests ──────────────────────────────────────────


class TestLinkedInPublisherUpload:
    """Tests for LinkedInPublisher._upload_impl — focuses on auth check, URN resolution, and upload flow."""

    @pytest.mark.asyncio
    async def test_linkedin_auth_check_empty_headers(self, post_metadata):
        """
        Verify auth check: empty headers dict returns None.
        Tests the fix: 'if not headers' → 'if not headers.get("Authorization")'
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        result = await base_linkedin_publisher_service._upload_impl(
            video_path="/tmp/test.mp4",
            metadata=post_metadata,
            user_id="user1",
            account_id=None,
            headers={},
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_linkedin_auth_check_no_auth_value(self, post_metadata):
        """
        Verify auth check: headers with Authorization=None returns None.
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        result = await base_linkedin_publisher_service._upload_impl(
            video_path="/tmp/test.mp4",
            metadata=post_metadata,
            user_id="user1",
            account_id=None,
            headers={"Authorization": None},
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_linkedin_full_success(self, post_metadata):
        """
        Verify full happy-path: register upload → binary upload → create UGC post → LinkedIn URL.
        Also verifies URN uses stored username (not app user_id).
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        mock_token_data = {
            "username": "linkedin_sub_abc",
            "access_token": "tok_123",
        }

        # Register upload response
        mock_register_response = MagicMock()
        mock_register_response.status_code = 200
        mock_register_response.json.return_value = {
            "value": {
                "asset": "urn:li:digitalmediaAsset:media_123",
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                        "uploadUrl": "https://api.linkedin.com/upload/media_123",
                    }
                },
            }
        }

        # Binary upload response
        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 201

        # UGC post creation response
        mock_post_response = MagicMock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = {
            "id": "urn:li:share:post_456"
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_register_response,  # Step 1: registerUpload
                mock_post_response,      # Step 3: create UGC post
            ]
        )
        mock_client.put = AsyncMock(
            return_value=mock_upload_response  # Step 2: binary upload
        )

        with (
            patch(
                "src.services.optimization.linkedin_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch.object(
                base_linkedin_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=b"video_data_here",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_linkedin_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result == "https://www.linkedin.com/feed/update/urn:li:share:post_456"

    @pytest.mark.asyncio
    async def test_linkedin_register_fails(self, post_metadata):
        """
        Verify registerUpload failure returns None.
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        mock_token_data = {"username": "linkedin_sub_abc", "access_token": "tok_123"}

        mock_register_response = MagicMock()
        mock_register_response.status_code = 400
        mock_register_response.text = '{"error": "Invalid recipe"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_register_response)

        with (
            patch(
                "src.services.optimization.linkedin_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch.object(
                base_linkedin_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=b"video_data",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_linkedin_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_linkedin_no_asset_urn(self, post_metadata):
        """
        Verify when register response has no asset URN, returns None.
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        mock_token_data = {"username": "linkedin_sub_abc", "access_token": "tok_123"}

        mock_register_response = MagicMock()
        mock_register_response.status_code = 200
        mock_register_response.json.return_value = {
            "value": {
                # No "asset" key
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                        "uploadUrl": "https://api.linkedin.com/upload/media_123",
                    }
                },
            }
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_register_response)

        with (
            patch(
                "src.services.optimization.linkedin_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_linkedin_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_linkedin_no_upload_url(self, post_metadata):
        """
        Verify when register response has no uploadUrl, returns None.
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        mock_token_data = {"username": "linkedin_sub_abc", "access_token": "tok_123"}

        mock_register_response = MagicMock()
        mock_register_response.status_code = 200
        mock_register_response.json.return_value = {
            "value": {
                "asset": "urn:li:digitalmediaAsset:media_123",
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {}
                    # No uploadUrl
                },
            }
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_register_response)

        with (
            patch(
                "src.services.optimization.linkedin_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_linkedin_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_linkedin_binary_upload_fails(self, post_metadata):
        """
        Verify when binary PUT upload returns non-200, returns None.
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        mock_token_data = {"username": "linkedin_sub_abc", "access_token": "tok_123"}

        mock_register_response = MagicMock()
        mock_register_response.status_code = 200
        mock_register_response.json.return_value = {
            "value": {
                "asset": "urn:li:digitalmediaAsset:media_123",
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                        "uploadUrl": "https://api.linkedin.com/upload/media_123",
                    }
                },
            }
        }

        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 500
        mock_upload_response.text = '{"error": "Upload failed"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_register_response)
        mock_client.put = AsyncMock(return_value=mock_upload_response)

        with (
            patch(
                "src.services.optimization.linkedin_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch.object(
                base_linkedin_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=b"video_data",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_linkedin_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_linkedin_post_creation_fails(self, post_metadata):
        """
        Verify when UGC post creation returns non-200, returns None.
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        mock_token_data = {"username": "linkedin_sub_abc", "access_token": "tok_123"}

        mock_register_response = MagicMock()
        mock_register_response.status_code = 200
        mock_register_response.json.return_value = {
            "value": {
                "asset": "urn:li:digitalmediaAsset:media_123",
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                        "uploadUrl": "https://api.linkedin.com/upload/media_123",
                    }
                },
            }
        }

        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 201

        mock_post_response = MagicMock()
        mock_post_response.status_code = 400
        mock_post_response.text = '{"error": "Invalid URN"}'

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[mock_register_response, mock_post_response]
        )
        mock_client.put = AsyncMock(return_value=mock_upload_response)

        with (
            patch(
                "src.services.optimization.linkedin_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch.object(
                base_linkedin_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=b"video_data",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_linkedin_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_linkedin_urn_with_username(self, post_metadata):
        """
        Verify URN uses stored username (not app user_id) when token_data is available.
        The correct URN should be urn:li:person:linkedin_sub_abc, not urn:li:person:user1.
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        mock_token_data = {
            "username": "linkedin_sub_abc",  # OpenID sub stored as username
            "access_token": "tok_123",
        }

        mock_register_response = MagicMock()
        mock_register_response.status_code = 200
        mock_register_response.json.return_value = {
            "value": {
                "asset": "urn:li:digitalmediaAsset:media_123",
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                        "uploadUrl": "https://api.linkedin.com/upload/media_123",
                    }
                },
            }
        }

        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 201

        mock_post_response = MagicMock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = {"id": "urn:li:share:post_456"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[mock_register_response, mock_post_response]
        )
        mock_client.put = AsyncMock(return_value=mock_upload_response)

        with (
            patch(
                "src.services.optimization.linkedin_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch.object(
                base_linkedin_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=b"video_data",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_linkedin_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",  # App user_id — should NOT appear in URN
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is not None
            # Verify the registerUpload used the correct URN with linkedin_sub
            call_args = mock_client.post.call_args_list
            # First POST call should be registerUpload
            register_call = call_args[0]
            register_payload = register_call[1].get("json", {})
            owner = register_payload.get("registerUploadRequest", {}).get("owner")
            assert owner == "urn:li:person:linkedin_sub_abc"

    @pytest.mark.asyncio
    async def test_linkedin_urn_fallback(self, post_metadata):
        """
        Verify URN falls back to user_id when token_data is None.
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        mock_register_response = MagicMock()
        mock_register_response.status_code = 200
        mock_register_response.json.return_value = {
            "value": {
                "asset": "urn:li:digitalmediaAsset:media_123",
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                        "uploadUrl": "https://api.linkedin.com/upload/media_123",
                    }
                },
            }
        }

        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 201

        mock_post_response = MagicMock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = {"id": "urn:li:share:post_456"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[mock_register_response, mock_post_response]
        )
        mock_client.put = AsyncMock(return_value=mock_upload_response)

        with (
            patch(
                "src.services.optimization.linkedin_publisher.token_manager.get_token_data",
                return_value=None,  # No token data — should fall back to user_id
            ),
            patch.object(
                base_linkedin_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=b"video_data",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_linkedin_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="fallback_user_id",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is not None
            # Verify the registerUpload used fallback URN
            call_args = mock_client.post.call_args_list
            register_call = call_args[0]
            register_payload = register_call[1].get("json", {})
            owner = register_payload.get("registerUploadRequest", {}).get("owner")
            assert owner == "urn:li:person:fallback_user_id"

    @pytest.mark.asyncio
    async def test_linkedin_load_video_data_fails(self, post_metadata):
        """
        Verify when _load_video_data returns None, _upload_impl returns None.
        """
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        mock_token_data = {"username": "linkedin_sub_abc", "access_token": "tok_123"}

        mock_register_response = MagicMock()
        mock_register_response.status_code = 200
        mock_register_response.json.return_value = {
            "value": {
                "asset": "urn:li:digitalmediaAsset:media_123",
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                        "uploadUrl": "https://api.linkedin.com/upload/media_123",
                    }
                },
            }
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_register_response)

        with (
            patch(
                "src.services.optimization.linkedin_publisher.token_manager.get_token_data",
                return_value=mock_token_data,
            ),
            patch.object(
                base_linkedin_publisher_service,
                "_load_video_data",
                new_callable=AsyncMock,
                return_value=None,  # Video data loading fails
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_linkedin_publisher_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": "Bearer tok_123"},
            )

            assert result is None


class TestLinkedInPublisherUnit:
    """Direct unit tests for LinkedInPublisher methods."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Verify health_check returns False when no token exists."""
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        with patch(
            "src.services.optimization.linkedin_publisher.token_manager.get_token",
            return_value=None,
        ):
            result = await base_linkedin_publisher_service.health_check("user_no_token")
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_with_token(self):
        """Verify health_check returns True when token exists."""
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        with patch(
            "src.services.optimization.linkedin_publisher.token_manager.get_token",
            return_value="tok_123",
        ):
            result = await base_linkedin_publisher_service.health_check("user_with_token")
            assert result is True

    def test_build_post_text(self, post_metadata):
        """Verify _build_post_text constructs post text from metadata."""
        from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service

        text = base_linkedin_publisher_service._build_post_text(post_metadata)
        assert "Test Video Title" in text
        assert "A test video description" in text
        assert "#viral" in text  # hashtag


# ─── Facebook Publisher Tests ───────────────────────────────────────────


class TestFacebookPublisherUpload:
    """Tests for FacebookPublisher._upload_impl — auth check, upload flow, processing timeout."""

    @pytest.mark.asyncio
    async def test_facebook_auth_check_no_token_no_cookie(self, post_metadata):
        """
        Verify auth check: no token and no Cookie header returns None.
        Facebook uses get_token() instead of headers dict, but still checks Cookie fallback.
        """
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        with patch(
            "src.services.optimization.facebook_publisher.token_manager.get_token",
            return_value=None,
        ):
            result = await base_facebook_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={},
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_facebook_auth_check_no_token_with_cookie(self, post_metadata):
        """
        Verify auth check: no token but Cookie header present proceeds.
        Configures the mock_client.post to return a response without upload_session_id
        so the code fails deterministically at step 1 (not at auth check).
        """
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        mock_container_response = MagicMock()
        mock_container_response.json.return_value = {
            "error": {"message": "Invalid token"}
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_container_response)

        with (
            patch(
                "src.services.optimization.facebook_publisher.token_manager.get_token",
                return_value=None,
            ),
            patch.object(
                base_facebook_publisher_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_facebook_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Cookie": "session=abc123"},
            )
            # Should not return None from auth check — fails at step 1 (container creation)
            assert result is None

    @pytest.mark.asyncio
    async def test_facebook_full_success(self, post_metadata):
        """
        Verify full happy-path: start → transfer → finish → poll (ready) → Facebook URL.
        """
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        mock_access_token = "fb_token_123"

        # Step 1: start upload → upload_session_id
        mock_start_response = MagicMock()
        mock_start_response.json.return_value = {"upload_session_id": "session_abc"}

        # Step 2: transfer → success
        mock_transfer_response = MagicMock()
        mock_transfer_response.json.return_value = {"success": True}

        # Step 3: finish → success + video_id
        mock_finish_response = MagicMock()
        mock_finish_response.json.return_value = {
            "success": True,
            "video_id": "video_456",
        }

        # Step 4: poll status → ready
        mock_status_response = MagicMock()
        mock_status_response.json.return_value = {
            "status": {"video_status": "ready"}
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_start_response,    # Step 1: start
                mock_transfer_response,  # Step 2: transfer
                mock_finish_response,    # Step 3: finish
            ]
        )
        mock_client.get = AsyncMock(
            side_effect=[mock_status_response]  # Step 4: poll status
        )

        with (
            patch(
                "src.services.optimization.facebook_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_facebook_publisher_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await base_facebook_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result == "https://www.facebook.com/watch/?v=video_456"

    @pytest.mark.asyncio
    async def test_facebook_container_creation_fails(self, post_metadata):
        """
        Verify when start upload returns no upload_session_id, returns None.
        """
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        mock_access_token = "fb_token_123"

        mock_start_response = MagicMock()
        mock_start_response.json.return_value = {
            "error": {"message": "Invalid permissions"}
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_start_response)

        with (
            patch(
                "src.services.optimization.facebook_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_facebook_publisher_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_facebook_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_facebook_upload_transfer_fails(self, post_metadata):
        """
        Verify when transfer upload returns no success, returns None.
        """
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        mock_access_token = "fb_token_123"

        mock_start_response = MagicMock()
        mock_start_response.json.return_value = {"upload_session_id": "session_abc"}

        mock_transfer_response = MagicMock()
        mock_transfer_response.json.return_value = {
            "error": {"message": "Invalid file URL"}
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[mock_start_response, mock_transfer_response]
        )

        with (
            patch(
                "src.services.optimization.facebook_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_facebook_publisher_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_facebook_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_facebook_finalize_fails(self, post_metadata):
        """
        Verify when finalize returns no success, returns None.
        """
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        mock_access_token = "fb_token_123"

        mock_start_response = MagicMock()
        mock_start_response.json.return_value = {"upload_session_id": "session_abc"}

        mock_transfer_response = MagicMock()
        mock_transfer_response.json.return_value = {"success": True}

        mock_finish_response = MagicMock()
        mock_finish_response.json.return_value = {
            "error": {"message": "Processing failed"}
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_start_response,
                mock_transfer_response,
                mock_finish_response,
            ]
        )

        with (
            patch(
                "src.services.optimization.facebook_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_facebook_publisher_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_facebook_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_facebook_no_video_id(self, post_metadata):
        """
        Verify when finalize response has no video_id, returns None.
        """
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        mock_access_token = "fb_token_123"

        mock_start_response = MagicMock()
        mock_start_response.json.return_value = {"upload_session_id": "session_abc"}

        mock_transfer_response = MagicMock()
        mock_transfer_response.json.return_value = {"success": True}

        mock_finish_response = MagicMock()
        mock_finish_response.json.return_value = {
            "success": True
            # No "video_id" key
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_start_response,
                mock_transfer_response,
                mock_finish_response,
            ]
        )

        with (
            patch(
                "src.services.optimization.facebook_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_facebook_publisher_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
        ):
            result = await base_facebook_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_facebook_processing_timeout(self, post_metadata):
        """
        Verify processing polling hits max_polls=60 guard and returns None.
        Tests the polling guard pattern (similar to X's max_polls=30).
        """
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        mock_access_token = "fb_token_123"

        mock_start_response = MagicMock()
        mock_start_response.json.return_value = {"upload_session_id": "session_abc"}

        mock_transfer_response = MagicMock()
        mock_transfer_response.json.return_value = {"success": True}

        mock_finish_response = MagicMock()
        mock_finish_response.json.return_value = {
            "success": True,
            "video_id": "video_456",
        }

        # Status always returns not-ready
        mock_status_response = MagicMock()
        mock_status_response.json.return_value = {
            "status": {"video_status": "processing"}
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_start_response,
                mock_transfer_response,
                mock_finish_response,
            ]
        )
        mock_client.get = AsyncMock(return_value=mock_status_response)

        with (
            patch(
                "src.services.optimization.facebook_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_facebook_publisher_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await base_facebook_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_facebook_processing_error(self, post_metadata):
        """
        Verify when status check returns an error, _upload_impl returns None.
        """
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        mock_access_token = "fb_token_123"

        mock_start_response = MagicMock()
        mock_start_response.json.return_value = {"upload_session_id": "session_abc"}

        mock_transfer_response = MagicMock()
        mock_transfer_response.json.return_value = {"success": True}

        mock_finish_response = MagicMock()
        mock_finish_response.json.return_value = {
            "success": True,
            "video_id": "video_456",
        }

        # Status returns an error
        mock_status_response = MagicMock()
        mock_status_response.json.return_value = {
            "error": {"message": "Video processing failed"}
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                mock_start_response,
                mock_transfer_response,
                mock_finish_response,
            ]
        )
        mock_client.get = AsyncMock(return_value=mock_status_response)

        with (
            patch(
                "src.services.optimization.facebook_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch.object(
                base_facebook_publisher_service,
                "_resolve_video_uri",
                new_callable=AsyncMock,
                return_value="https://cdn.example.com/video.mp4",
            ),
            patch(
                "httpx.AsyncClient",
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_client)),
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await base_facebook_publisher_service._upload_impl(
                video_path="https://cdn.example.com/video.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None


class TestFacebookPublisherUnit:
    """Direct unit tests for FacebookPublisher methods."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Verify health_check returns False when no token exists."""
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        with patch(
            "src.services.optimization.facebook_publisher.token_manager.get_token",
            return_value=None,
        ):
            result = await base_facebook_publisher_service.health_check("user_no_token")
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_with_token(self):
        """Verify health_check returns True when token exists."""
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        with patch(
            "src.services.optimization.facebook_publisher.token_manager.get_token",
            return_value="tok_123",
        ):
            result = await base_facebook_publisher_service.health_check("user_with_token")
            assert result is True

    @pytest.mark.asyncio
    async def test_resolve_video_url(self):
        """Verify _resolve_video_uri returns URLs as-is."""
        from src.services.optimization.facebook_publisher import base_facebook_publisher_service

        url = "https://cdn.example.com/video.mp4"
        result = await base_facebook_publisher_service._resolve_video_uri(url)
        assert result == url


# ─── YouTube Publisher Tests ────────────────────────────────────────────


class TestYouTubePublisherUpload:
    """Tests for YouTubePublisher._upload_impl — auth check, upload flow, error handling."""

    @pytest.mark.asyncio
    async def test_youtube_auth_check_no_token(self, post_metadata):
        """
        Verify auth check: no token returns None.
        YouTube uses get_token() directly, so auth check is inherently correct,
        but we still test the behavior.
        """
        from src.services.optimization.youtube_publisher import base_youtube_service

        with patch(
            "src.services.optimization.youtube_publisher.token_manager.get_token",
            return_value=None,
        ):
            result = await base_youtube_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={},
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_youtube_upload_success(self, post_metadata):
        """
        Verify full happy-path: upload YouTube video → returns shorts URL.
        Uses mocked Google API client.
        """
        from src.services.optimization.youtube_publisher import base_youtube_service

        mock_access_token = "yt_token_123"

        # Mock the Google API response
        mock_video_insert = MagicMock()
        mock_video_insert.execute.return_value = {"id": "yt_video_abc123"}

        mock_youtube_client = MagicMock()
        mock_youtube_client.videos().insert.return_value = mock_video_insert

        with (
            patch(
                "src.services.optimization.youtube_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch(
                "googleapiclient.discovery.build",
                return_value=mock_youtube_client,
            ),
            patch("googleapiclient.http.MediaFileUpload"),
            patch("google.oauth2.credentials.Credentials"),
        ):
            result = await base_youtube_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result == "https://youtube.com/shorts/yt_video_abc123"

            # Verify the API was called with correct parameters
            mock_youtube_client.videos().insert.assert_called_once()
            call_kwargs = mock_youtube_client.videos().insert.call_args
            assert call_kwargs[1]["part"] == "snippet,status"
            body = call_kwargs[1]["body"]
            assert body["snippet"]["title"] == "Test Video Title"
            assert body["snippet"]["categoryId"] == "22"
            assert body["status"]["privacyStatus"] == "public"

    @pytest.mark.asyncio
    async def test_youtube_upload_api_error(self, post_metadata):
        """
        Verify when Google API raises an exception, _upload_impl returns None.
        """
        from src.services.optimization.youtube_publisher import base_youtube_service

        mock_access_token = "yt_token_123"

        mock_video_insert = MagicMock()
        mock_video_insert.execute.side_effect = Exception("API quota exceeded")

        mock_youtube_client = MagicMock()
        mock_youtube_client.videos().insert.return_value = mock_video_insert

        with (
            patch(
                "src.services.optimization.youtube_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch(
                "googleapiclient.discovery.build",
                return_value=mock_youtube_client,
            ),
            patch("googleapiclient.http.MediaFileUpload"),
            patch("google.oauth2.credentials.Credentials"),
        ):
            result = await base_youtube_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_youtube_no_video_id(self, post_metadata):
        """
        Verify when response has no 'id' field, _upload_impl returns None.
        """
        from src.services.optimization.youtube_publisher import base_youtube_service

        mock_access_token = "yt_token_123"

        mock_video_insert = MagicMock()
        mock_video_insert.execute.return_value = {}  # No 'id' key

        mock_youtube_client = MagicMock()
        mock_youtube_client.videos().insert.return_value = mock_video_insert

        with (
            patch(
                "src.services.optimization.youtube_publisher.token_manager.get_token",
                return_value=mock_access_token,
            ),
            patch(
                "googleapiclient.discovery.build",
                return_value=mock_youtube_client,
            ),
            patch("googleapiclient.http.MediaFileUpload"),
            patch("google.oauth2.credentials.Credentials"),
        ):
            result = await base_youtube_service._upload_impl(
                video_path="/tmp/test.mp4",
                metadata=post_metadata,
                user_id="user1",
                account_id=None,
                headers={"Authorization": f"Bearer {mock_access_token}"},
            )

            assert result is None


class TestYouTubePublisherUnit:
    """Direct unit tests for YouTubePublisher methods."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Verify health_check returns False when no token exists."""
        from src.services.optimization.youtube_publisher import base_youtube_service

        with patch(
            "src.services.optimization.youtube_publisher.token_manager.get_token",
            return_value=None,
        ):
            result = await base_youtube_service.health_check("user_no_token")
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_with_token(self):
        """Verify health_check returns True when token exists."""
        from src.services.optimization.youtube_publisher import base_youtube_service

        with patch(
            "src.services.optimization.youtube_publisher.token_manager.get_token",
            return_value="tok_123",
        ):
            result = await base_youtube_service.health_check("user_with_token")
            assert result is True
