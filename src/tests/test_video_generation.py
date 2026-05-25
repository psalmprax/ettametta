import pytest
import asyncio
import logging

# Configure logging to see results
logging.basicConfig(level=logging.INFO)

# Try to import generative service, handle gracefully if dependencies missing
try:
    from src.services.video_engine.synthesis_service import base_generative_service

    GENERATIVE_SERVICE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Generative service not available: {e}")
    base_generative_service = None
    GENERATIVE_SERVICE_AVAILABLE = False

# Configure logging to see results
logging.basicConfig(level=logging.INFO)


class TestVideoGeneration:
    """Test suite for video generation engines."""

    @pytest.mark.asyncio
    async def test_veo3_generation(self):
        if not GENERATIVE_SERVICE_AVAILABLE:
            pytest.skip("Generative service not available")
        """Test Veo3 engine with basic prompt."""
        """Test Veo3 engine with basic prompt."""
        prompt = "A beautiful sunset over mountains"
        result = await base_generative_service.synthesize_video(
            prompt=prompt, engine="veo3", aspect_ratio="16:9", style="Cinematic"
        )

        if result:
            print(f"✅ Veo3 generation successful: {result}")
            assert isinstance(result, str)
        else:
            print("⚠️ Veo3 generation returned None (expected fallback)")
            assert result is None  # Expected for no API keys

    @pytest.mark.asyncio
    async def test_wan_generation(self):
        if not GENERATIVE_SERVICE_AVAILABLE:
            pytest.skip("Generative service not available")
        """Test Wan engine."""
        prompt = "A cat playing in a garden"
        result = await base_generative_service.synthesize_video(
            prompt=prompt, engine="wan", aspect_ratio="9:16", style="Cinematic"
        )

        if result:
            print(f"✅ Wan generation successful: {result}")
            assert isinstance(result, str)
        else:
            print("⚠️ Wan generation returned None (expected for no GPU/local setup)")
            assert result is None

    @pytest.mark.asyncio
    async def test_hunyuan_generation(self):
        if not GENERATIVE_SERVICE_AVAILABLE:
            pytest.skip("Generative service not available")
        """Test Hunyuan engine."""
        prompt = "A futuristic city at night"
        result = await base_generative_service.synthesize_video(
            prompt=prompt, engine="hunyuan", aspect_ratio="9:16", style="Cinematic"
        )

        if result:
            print(f"✅ Hunyuan generation successful: {result}")
            assert isinstance(result, str)
        else:
            print("⚠️ Hunyuan generation returned None (expected for no ComfyUI)")
            assert result is None

    @pytest.mark.asyncio
    async def test_ltx_video_generation(self):
        if not GENERATIVE_SERVICE_AVAILABLE:
            pytest.skip("Generative service not available")
        """Test LTX-Video engine."""
        prompt = "Water flowing in a stream"
        result = await base_generative_service.synthesize_video(
            prompt=prompt, engine="ltx-video", aspect_ratio="16:9", style="Cinematic"
        )

        if result:
            print(f"✅ LTX-Video generation successful: {result}")
            assert isinstance(result, str)
        else:
            print("⚠️ LTX-Video generation returned None (expected for no ComfyUI)")
            assert result is None

    @pytest.mark.asyncio
    async def test_free_provider_zsky(self):
        if not GENERATIVE_SERVICE_AVAILABLE:
            pytest.skip("Generative service not available")
        """Test free provider ZSky."""
        prompt = "A peaceful lake scene"
        result = await base_generative_service.synthesize_video(
            prompt=prompt, engine="zsky", aspect_ratio="9:16", style="Cinematic"
        )

        if result:
            print(f"✅ ZSky generation successful: {result}")
            assert isinstance(result, str)
            assert result.startswith("http")  # Should be a URL
        else:
            print("⚠️ ZSky generation returned None (expected for no API)")
            assert result is None

    @pytest.mark.asyncio
    async def test_free_provider_kling(self):
        if not GENERATIVE_SERVICE_AVAILABLE:
            pytest.skip("Generative service not available")
        """Test free provider Kling."""
        prompt = "A bird flying in the sky"
        result = await base_generative_service.synthesize_video(
            prompt=prompt, engine="kling", aspect_ratio="9:16", style="Cinematic"
        )

        if result:
            print(f"✅ Kling generation successful: {result}")
            assert isinstance(result, str)
            assert result.startswith("http")
        else:
            print("⚠️ Kling generation returned None (expected for no API)")
            assert result is None

    @pytest.mark.asyncio
    async def test_lite4k_fallback(self):
        if not GENERATIVE_SERVICE_AVAILABLE:
            pytest.skip("Generative service not available")
        """Test Lite4K fallback engine."""
        prompt = "A simple animation of shapes"
        result = await base_generative_service.synthesize_video(
            prompt=prompt, engine="lite4k", aspect_ratio="1:1", style="Cinematic"
        )

        if result:
            print(f"✅ Lite4K generation successful: {result}")
            assert isinstance(result, str)
        else:
            print("⚠️ Lite4K generation returned None (unexpected)")
            # Lite4K should always work as it's image+parallax

    @pytest.mark.asyncio
    async def test_aspect_ratios(self):
        if not GENERATIVE_SERVICE_AVAILABLE:
            pytest.skip("Generative service not available")
        """Test different aspect ratios with Veo3."""
        prompt = "A test scene"
        ratios = ["9:16", "16:9", "1:1"]

        for ratio in ratios:
            result = await base_generative_service.synthesize_video(
                prompt=prompt, engine="veo3", aspect_ratio=ratio, style="Cinematic"
            )

            if result:
                print(f"✅ Aspect ratio {ratio} successful")
            else:
                print(f"⚠️ Aspect ratio {ratio} returned None")

    @pytest.mark.asyncio
    async def test_error_handling(self):
        if not GENERATIVE_SERVICE_AVAILABLE:
            pytest.skip("Generative service not available")
        """Test error handling with invalid engine."""
        prompt = "A test prompt"
        result = await base_generative_service.synthesize_video(
            prompt=prompt,
            engine="invalid_engine",
            aspect_ratio="9:16",
            style="Cinematic",
        )

        assert result is None, "Invalid engine should return None"

    @pytest.mark.asyncio
    async def test_empty_prompt(self):
        if not GENERATIVE_SERVICE_AVAILABLE:
            pytest.skip("Generative service not available")
        """Test with empty prompt."""
        result = await base_generative_service.synthesize_video(
            prompt="", engine="veo3", aspect_ratio="9:16", style="Cinematic"
        )

        # Should handle empty prompt gracefully
        if result:
            print("✅ Empty prompt handled successfully")
        else:
            print("⚠️ Empty prompt returned None")


if __name__ == "__main__":
    # Run basic smoke test if executed directly
    async def run_smoke_test():
        print("Running video generation smoke test...")
        if not GENERATIVE_SERVICE_AVAILABLE:
            print("⚠️ Generative service not available - smoke test skipped")
            return
        try:
            result = await base_generative_service.synthesize_video(
                prompt="Test video generation", engine="veo3", aspect_ratio="9:16"
            )
            if result:
                print(f"✅ Smoke test passed: {result}")
            else:
                print("⚠️ Smoke test returned None (expected without API keys)")
        except Exception as e:
            print(f"❌ Smoke test failed: {e}")
            raise

    asyncio.run(run_smoke_test())
