import pytest
from src.services.video_engine.free_video_service import base_free_video_service, FreeVideoService, FreeVideoAsset


def test_free_video_prompt_enhancer():
    service = FreeVideoService()

    enhanced_tech = service.enhance_prompt_free("smartphone app demo", style="tech")
    assert "4k resolution" in enhanced_tech
    assert "dark glass reflection" in enhanced_tech

    enhanced_luxury = service.enhance_prompt_free("luxury watch", style="luxury")
    assert "golden hour warm glow" in enhanced_luxury


def test_pollinations_free_url_generation():
    service = FreeVideoService()
    url = service.get_pollinations_free_url("wireless headphones", width=1080, height=1920)

    assert url.startswith("https://image.pollinations.ai/prompt/")
    assert "width=1080" in url
    assert "height=1920" in url
    assert "nologo=true" in url


@pytest.mark.asyncio
async def test_fetch_free_broll_clip():
    service = FreeVideoService()
    assets = await service.fetch_free_broll_clip("cyberpunk city", count=2)

    assert isinstance(assets, list)
    assert len(assets) > 0
    assert isinstance(assets[0], FreeVideoAsset)
    assert assets[0].cost_usd == 0.0
    assert assets[0].provider in ("pollinations", "coverr", "mixkit")
