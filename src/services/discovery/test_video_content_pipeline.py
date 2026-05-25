"""
Tests for the viral content discovery to AI video generation pipeline.
"""

import asyncio
import pytest
from unittest.mock import patch

from src.services.discovery.video_content_pipeline import (
    ViralContentPipeline,
    discover_analyze_and_generate,
    discover_analyze_generate_compile
)
from src.services.discovery.cloak_scanner import ContentCandidate


class TestViralContentPipeline:
    """Test the viral content discovery pipeline."""

    @pytest.fixture
    def pipeline(self):
        return ViralContentPipeline()

    @pytest.fixture
    def sample_content_candidate(self):
        return ContentCandidate(
            id="test_123",
            platform="YouTube",
            source_uri="https://youtube.com/watch?v=test123",
            creator_name="Test Creator",
            title="5 AI Productivity Hacks You Need",
            description="Learn about the latest AI tools for productivity",
            thumbnail_uri="https://i.ytimg.com/vi/test123/hqdefault.jpg",
            view_count=50000,
            like_count=2000,
            comment_count=150,
            share_count=75,
            engagement_score=8.5,
            viral_score=75,
            duration_seconds=60,
            region="US",
            category="video",
            tags=["ai", "productivity"],
            metadata={"scraper": "cloakbrowser", "source": "youtube_web"}
        )

    @pytest.mark.asyncio
    async def test_discover_and_analyze_content(self, pipeline, sample_content_candidate):
        """Test content discovery and analysis."""
        with patch.object(pipeline.cloak_scanner, 'scan_trends', 
                         return_value=[sample_content_candidate]) as mock_scan:
            
            with patch('src.services.discovery.video_content_pipeline.extract_content_patterns',
                      return_value={
                          "niches": ["education", "tech"],
                          "sentiment": "positive",
                          "viral_potential": "high",
                          "keywords": ["AI", "productivity", "hacks", "tools"],
                          "summary": "Essential AI productivity tools for modern workers",
                          "target_audience": "professionals seeking efficiency",
                          "content_type": "tutorial"
                      }) as mock_analyze:
                
                result = await pipeline.discover_and_analyze_content(
                    niche="AI productivity",
                    max_results=1
                )
                
                assert len(result) == 1
                assert result[0]["discovered_content"]["title"] == "5 AI Productivity Hacks You Need"
                assert result[0]["analysis"]["niches"] == ["education", "tech"]
                assert result[0]["analysis"]["sentiment"] == "positive"
                assert result[0]["analysis"]["viral_potential"] == "high"
                
                mock_scan.assert_called_once_with(
                    niche="AI productivity",
                    region="US",
                    published_after=None
                )
                mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_ai_video_from_insights(self, pipeline):
        """Test AI video generation from content insights."""
        analyzed_content = {
            "discovered_content": {
                "id": "test_123",
                "title": "5 AI Productivity Hacks You Need",
                "platform": "YouTube"
            },
            "analysis": {
                "niches": ["education", "tech"],
                "keywords": ["AI", "productivity", "tools"],
                "sentiment": "positive",
                "summary": "Essential AI productivity tools"
            }
        }
        
        mock_video_result = {
            "video_uri": "https://storage.googleapis.com/test-bucket/video.mp4",
            "provider": "zsky",
            "metadata": {"model": "zsky-wan"}
        }
        
        with patch.object(free_video_provider, 'generate_video',
                         return_value=mock_video_result) as mock_generate:
            
            result = await pipeline.generate_ai_video_from_insights(
                analyzed_content=analyzed_content,
                video_style="cinematic",
                duration=8
            )
            
            assert result is not None
            assert result["video_uri"] == "https://storage.googleapis.com/test-bucket/video.mp4"
            assert result["provider"] == "zsky"
            assert result["source_content_id"] == "test_123"
            assert result["pipeline_stage"] == "ai_video_generation_complete"
            
            # Verify the generation prompt was constructed properly
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args[1]  # kwargs
            assert "AI productivity hacks" in call_args["prompt"]
            assert call_args["duration"] == 8
            assert call_args["aspect_ratio"] == "9:16"
            assert call_args["style"] == "cinematic"

    @pytest.mark.asyncio
    async def test_discover_and_create_video_full_pipeline(self, pipeline, sample_content_candidate):
        """Test the complete discovery → analysis → generation pipeline."""
        with patch.object(pipeline.cloak_scanner, 'scan_trends',
                         return_value=[sample_content_candidate]) as mock_scan:
            
            with patch('src.services.discovery.video_content_pipeline.extract_content_patterns',
                      return_value={
                          "niches": ["education"],
                          "sentiment": "positive", 
                          "viral_potential": "high",
                          "keywords": ["AI", "productivity"],
                          "summary": "AI tools for productivity",
                          "target_audience": "professionals",
                          "content_type": "tutorial"
                      }) as mock_analyze:
                
                mock_video_result = {
                    "video_uri": "https://storage.googleapis.com/test-bucket/video.mp4",
                    "provider": "kling",
                    "metadata": {"model": "kling-v1"}
                }
                
                with patch.object(free_video_provider, 'generate_video',
                                 return_value=mock_video_result) as mock_generate:
                    
                    results = await pipeline.discover_and_create_video(
                        niche="AI productivity",
                        max_discover=2,
                        videos_to_generate=1,
                        video_style="educational"
                    )
                    
                    assert len(results) == 1
                    assert results[0]["provider"] == "kling"
                    assert results[0]["source_content_id"] == "test_123"
                    assert results[0]["pipeline_stage"] == "ai_video_generation_complete"
                    
                    mock_scan.assert_called_once()
                    mock_analyze.assert_called_once()
                    mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_discovery_handling(self, pipeline):
        """Test handling when no content is discovered."""
        with patch.object(pipeline.cloak_scanner, 'scan_trends',
                         return_value=[]) as mock_scan:
            
            results = await pipeline.discover_and_analyze_content(
                niche="obscure_niche_12345",
                max_results=5
            )
            
            assert results == []
            mock_scan.assert_called_once()

    @pytest.mark.asyncio
    async def test_analysis_failure_handling(self, pipeline, sample_content_candidate):
        """Test graceful handling when analysis fails."""
        with patch.object(pipeline.cloak_scanner, 'scan_trends',
                         return_value=[sample_content_candidate]):
            
            with patch('src.services.discovery.video_content_pipeline.extract_content_patterns',
                      side_effect=Exception("Analysis service failed")):
                
                results = await pipeline.discover_and_analyze_content(
                    niche="test niche",
                    max_results=1
                )
                
                # Should return empty list when analysis fails
                assert results == []

    @pytest.mark.asyncio
    async def test_video_generation_failure_handling(self, pipeline):
        """Test handling when AI video generation fails."""
        analyzed_content = {
            "discovered_content": {
                "id": "test_123",
                "title": "Test Video",
                "platform": "YouTube"
            },
            "analysis": {
                "niches": ["entertainment"],
                "keywords": ["test"],
                "sentiment": "neutral",
                "summary": "Test content"
            }
        }
        
        with patch.object(free_video_provider, 'generate_video',
                         return_value=None) as mock_generate:  # Simulate failure
            
            result = await pipeline.generate_ai_video_from_insights(
                analyzed_content=analyzed_content
            )
            
            assert result is None
            mock_generate.assert_called_once()


# Integration test style demonstrations
class TestPipelineIntegration:
    """Integration-style tests showing how the pipeline works."""

    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test the convenience functions work correctly."""
        # Mock the pipeline methods
        with patch.object(viral_content_pipeline, 'discover_and_create_video',
                         return_value=[{"test": "video_result"}]) as mock_pipeline:
            
            result = await discover_analyze_and_generate(
                niche="test niche",
                max_discover=3,
                videos_to_generate=2
            )
            
            assert result == [{"test": "video_result"}]
            mock_pipeline.assert_called_once_with(
                niche="test niche",
                max_discover=3,
                videos_to_generate=2,
                video_style="cinematic"  # default
            )

    @pytest.mark.asyncio
    async def test_compile_convenience_function(self):
        """Test the compile convenience function."""
        with patch.object(viral_content_pipeline, 'create_compiled_video',
                         return_value={"success": True, "video_path": "/tmp/test.mp4"}) as mock_pipeline:
            
            result = await discover_analyze_generate_compile(
                niche="test niche",
                max_discover=5
            )
            
            assert result["success"] is True
            assert result["video_path"] == "/tmp/test.mp4"
            mock_pipeline.assert_called_once_with(
                niche="test niche",
                max_discover=5,
                video_style="cinematic"  # default
            )


if __name__ == "__main__":
    # Run basic functionality test
    async def demo():
        print("🧪 Testing Viral Content Pipeline...")
        
        # This would normally require actual API keys and services
        # For demo purposes, we'll show the structure
        
        ViralContentPipeline()
        print("✅ Pipeline instantiated successfully")
        print("📋 Pipeline includes:")
        print("   - CloakBrowser discovery")
        print("   - AI-powered content analysis") 
        print("   - AI video generation (ZSky/Kling/Runway/etc.)")
        print("   - Optional video compilation")
        print("🚀 Ready for end-to-end viral content creation!")
    
    asyncio.run(demo())