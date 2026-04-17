import asyncio
import os
import json
from src.workflows.elite_production_cycle import run_elite_production_cycle
from unittest.mock import MagicMock, patch

async def test_prop_hardening():
    print("🧪 Verifying Remotion Prop Hardening...")
    
    # Mock services to avoid real AI/Network calls
    with patch("src.workflows.elite_production_cycle.discover_multi_platform") as mock_disc, \
         patch("src.workflows.elite_production_cycle.analyze_content_type") as mock_anal, \
         patch("src.workflows.elite_production_cycle.base_viral_critic.review_production") as mock_crit, \
         patch("src.workflows.elite_production_cycle.base_monetization_engine.auto_insert_links") as mock_mon, \
         patch("src.workflows.elite_production_cycle.get_secret") as mock_secret, \
         patch("src.workflows.elite_production_cycle.RealVideoFusionEngine") as mock_engine, \
         patch("src.workflows.elite_production_cycle.remotion_service.render_video") as mock_render:
        
        mock_secret.return_value = "mock_key"
        mock_disc.return_value = [{"id": "v1", "url": "url1", "title": "Lead 1"}]
        mock_anal.return_value = {"usable": True, "score": 0.9}
        mock_crit.return_value = {"overall_score": 9.0}
        mock_mon.return_value = {"insertion_plan": {"insertions": [{"script_addition": "Buy now!"}]}}
        
        # Mock fusion result
        fuse_mock = MagicMock()
        fuse_mock.create_real_video_content.return_value = {
            "video_path": "out/fused.mp4",
            "script": {"title": "Test Viral Video"},
            "fusion_plan": {
                "segments": [{"text": "Hello", "duration": 5, "role": "HOOK"}],
                "editorial_style": "Cinematic"
            }
        }
        mock_engine.return_value = fuse_mock
        
        # We don't want to actually render, just check the props
        await run_elite_production_cycle("test topic", session_id="test_id_123")
        
        # Check call args of render_video
        args, kwargs = mock_render.call_args
        props = kwargs["props"]
        
        print(f"✅ Props Generated: {json.dumps(props, indent=2)}")
        
        # Verification assertions
        assert "videoUrl" in props
        assert props["videoUrl"].startswith("/") # Absolute path
        assert "timeline" in props
        assert len(props["timeline"]) == 1
        assert props["timeline"][0]["text"] == "Hello"
        assert props["subtitle"] == "A ViralForge Production ID: test_id_"
        assert props["showCtaOverlay"] is True
        
        print("🎉 Prop Hardening Verified!")

if __name__ == "__main__":
    asyncio.run(test_prop_hardening())
