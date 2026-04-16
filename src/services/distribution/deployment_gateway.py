"""
The Forge Gateway: Multi-Platform Distribution (10/10)
=====================================================

Automates the generation of platform-specific metadata (Captions, Tags)
and manages the hand-off to social media platforms.
"""

import logging
import json
import asyncio
from typing import Dict, Any, List
from services.script_generator.service import base_script_generator

logger = logging.getLogger(__name__)

class DeploymentGateway:
    """
    Handles metadata optimization and multi-platform distribution.
    """

    def __init__(self):
        self.platforms = ["tiktok", "youtube_shorts", "instagram_reels"]

    async def generate_production_package(self, production_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crafts a complete distribution package with captions and tags"""
        title = production_data.get("title", "Universal Viral Variant")
        
        # 1. Platform-Specific Metadata Generation (LLM-Driven)
        print(f"✍️  Generating Metadata for {title}...")
        
        metadata = {}
        for platform in self.platforms:
            prompt = f"Create a high-CTR {platform} caption and 10 hashtags for a video about: {title}. Focus on curiosity and virality."
            content = await base_script_generator.complete(prompt, system_prompt="You are a Viral Marketing Expert.")
            
            metadata[platform] = {
                "variant_id": production_data.get("variant_id", "gen_target"),
                "caption": content.split("#")[0].strip(),
                "hashtags": ["#" + tag.strip() for tag in content.split("#")[1:] if tag.strip()],
                "video_path": production_data.get("video_path")
            }
            
        return {
            "title": title,
            "platforms": metadata,
            "timestamp": production_data.get("timestamp")
        }

    async def distribute_to_world(self, package: Dict[str, Any]):
        """Simulation: Pushing content to platforms"""
        for platform, data in package["platforms"].items():
            logger.info(f"🚀 [Gateway] Pushing to {platform.upper()}...")
            # Simulate API Latency
            await asyncio.sleep(0.5)
            logger.info(f"✅ [Gateway] Post Live on {platform}: {data['caption'][:30]}...")
            
        return {"status": "deployed", "platforms_reached": self.platforms}

# Singleton Instance
base_deployment_gateway = DeploymentGateway()
