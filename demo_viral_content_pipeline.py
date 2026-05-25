#!/usr/bin/env python3
"""
Demo script showing the viral content discovery to AI video generation pipeline.
This demonstrates how the ettametta platform can automate content creation from discovery to generation.
"""

import asyncio
import logging
from src.services.discovery.video_content_pipeline import (
    discover_analyze_and_generate,
    discover_analyze_generate_compile
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_basic_pipeline():
    """Demo: Discover content → Analyze → Generate AI videos"""
    print("\n" + "="*60)
    print("🚀 DEMO: Basic Viral Content Pipeline")
    print("   Discovery → Analysis → AI Video Generation")
    print("="*60)
    
    # Example niches to explore
    test_niches = [
        "AI productivity tools",
        "fitness motivation", 
        "tech news",
        "personal finance tips"
    ]
    
    for niche in test_niches[:2]:  # Demo first 2 niches
        print(f"\n🔍 Exploring niche: '{niche}'")
        print("-" * 40)
        
        try:
            # Run the pipeline: discover → analyze → generate
            results = await discover_analyze_and_generate(
                niche=niche,
                max_discover=3,      # Find up to 3 trending pieces
                videos_to_generate=2  # Generate up to 2 AI videos
            )
            
            if results:
                print(f"✅ Generated {len(results)} AI video(s):")
                for i, video in enumerate(results, 1):
                    print(f"   {i}. Provider: {video.get('provider', 'unknown')}")
                    print(f"      Source: {video.get('source_title', 'Unknown')} ({video.get('source_platform', 'unknown')})")
                    print(f"      Insights: {video.get('analysis_insights', {}).get('niches', [])}")
                    print(f"      Sentiment: {video.get('analysis_insights', {}).get('sentiment', 'unknown')}")
                    print(f"      Viral Potential: {video.get('analysis_insights', {}).get('viral_potential', 'unknown')}")
            else:
                print("⚠️  No videos generated (this is expected in demo without actual API keys)")
                
        except Exception as e:
            print(f"❌ Error processing niche '{niche}': {e}")
            logger.exception("Pipeline error")

async def demo_full_compilation_pipeline():
    """Demo: Discover → Analyze → Generate → Compile into final video"""
    print("\n" + "="*60)
    print("🎬 DEMO: Full Compilation Pipeline") 
    print("   Discovery → Analysis → Generation → Compilation")
    print("="*60)
    
    niche = "motivational quotes"
    print(f"\n🎯 Creating compiled video for: '{niche}'")
    print("-" * 40)
    
    try:
        # Run the full pipeline including compilation
        result = await discover_analyze_generate_compile(
            niche=niche,
            max_discover=4  # Discover up to 4 pieces to create 3-4 video clips
        )
        
        if result:
            if result.get("success"):
                print("✅ Successfully created compiled video!")
                print(f"   📁 Output: {result.get('video_path', 'Unknown')}")
                print(f"   🎞️  Source clips: {len(result.get('source_clips', []))}")
                print(f"   ⏱️  Duration: {result.get('duration_seconds', 0)} seconds")
                print(f"   📊 Viral score: {result.get('viral_score', 0)}")
            else:
                print("⚠️  Compilation failed, but individual clips may be available")
                if isinstance(result, list) and result:
                    print(f"   📹 Generated {len(result)} individual clip(s) instead")
        else:
            print("⚠️  No output generated (expected in demo without API keys)")
            
    except Exception as e:
        print(f"❌ Error in compilation pipeline: {e}")
        logger.exception("Compilation pipeline error")

async def main():
    """Run all demos"""
    print("🔥 ettametta Viral Content Discovery Pipeline Demo")
    print("   Demonstrating automated content discovery → AI creation")
    
    await demo_basic_pipeline()
    await demo_full_compilation_pipeline()
    
    print("\n" + "="*60)
    print("📋 Pipeline Capabilities Demonstrated:")
    print("   ✅ Stealth content discovery (CloakBrowser)") 
    print("   ✅ AI-powered content analysis (LLM/NLP)")
    print("   ✅ AI video generation (ZSky/Kling/Runway/etc.)")
    print("   ✅ Automatic prompt generation from insights")
    print("   ✅ Optional video compilation/orchestration")
    print("   ✅ Error handling and fallback mechanisms")
    print("   ✅ Metadata preservation throughout pipeline")
    print("="*60)
    print("\n💡 To use with real APIs:")
    print("   1. Configure API keys in .env file")
    print("   2. Ensure CloakBrowser service is running")
    print("   3. Call the pipeline functions with your target niche")
    print("   4. Monitor logs for discovery and generation progress")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())