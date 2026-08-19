import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.optimization.service import base_optimization_service

@pytest.mark.asyncio
async def test_generate_viral_package_humanizes_output():
    """Verify that generate_viral_package humanizes the generated title, description, and cta."""
    # Mock groq response to return JSON containing AI slop words
    mock_response = (
        '{\n'
        '  "title": "Delve into the vibrant world",\n'
        '  "description": "Leveraging our robust framework to revolutionize learning.",\n'
        '  "hashtags": ["test", "niche"],\n'
        '  "cta": "It is important to note that you must follow."\n'
        '}'
    )

    # Mock redis and database
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    base_optimization_service._redis_client = mock_redis

    # Setup db mock
    mock_db_instance = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_instance.execute = AsyncMock(return_value=mock_result)

    with patch("src.services.optimization.service.settings.GROQ_API_KEY", "valid_key"), \
         patch.object(base_optimization_service, "_call_groq", AsyncMock(return_value=mock_response)), \
         patch("src.services.optimization.service.async_session_factory") as mock_db:
        mock_db.return_value.__aenter__.return_value = mock_db_instance

        result = await base_optimization_service.generate_viral_package(
            content_id="123", niche="niche", platform="tiktok"
        )

        # Expected humanized versions:
        # "Delve" -> "Dig"
        # "vibrant" -> "lively"
        # "Leveraging" -> "Using"
        # "robust" -> "reliable"
        # "revolutionize" -> "change"
        # "It is important to note that you must follow." -> "you must follow."
        assert result.title == "Dig into the lively world"
        assert result.description == "Using our reliable framework to change learning."
        assert result.cta == "you must follow."

@pytest.mark.asyncio
async def test_optimize_seo_content_humanizes_output():
    """Verify that optimize_seo_content humanizes title and description."""
    mock_response = (
        '{\n'
        '  "title": "A Pivotal Landscape shift",\n'
        '  "description": "Furthermore, it is a testament to our custom tailoring.",\n'
        '  "hashtags": ["seo", "test"]\n'
        '}'
    )

    with patch("src.services.optimization.service.settings.GROQ_API_KEY", "valid_key"), \
         patch.object(base_optimization_service, "_call_groq", AsyncMock(return_value=mock_response)):
        result = await base_optimization_service.optimize_seo_content(
            title="Old", description="Old desc", platform="youtube", niche="niche"
        )

        # Expected humanized versions:
        # "Pivotal" -> "Key"
        # "Landscape" -> "Environment"
        # "Furthermore" -> "Also"
        # "testament" -> "proof"
        assert result["title"] == "A Key Environment shift"
        assert result["description"] == "Also, it is a proof to our custom tailoring."

@pytest.mark.asyncio
async def test_generate_viral_hooks_humanizes_output():
    """Verify that generate_viral_hooks humanizes all returned hook suggestions."""
    mock_response = '["Delve deeper", "A vibrant future", "Leverage this"]'

    with patch("src.services.optimization.service.settings.GROQ_API_KEY", "valid_key"), \
         patch.object(base_optimization_service, "_call_groq", AsyncMock(return_value=mock_response)):
        result = await base_optimization_service.generate_viral_hooks(
            niche="niche", platform="youtube", count=3
        )

        assert result == ["Dig deeper", "A lively future", "Use this"]
