import logging
import httpx
import random
import uuid
from typing import Dict, Any, Optional
from api.config import settings
from api.utils.os_worker import ai_worker
from services.monetization.commerce_service import base_commerce_service

logger = logging.getLogger("AutoMerchService")

class AutoMerchService:
    """
    Handles 'Reverse Monetization':
    1. Trend -> Image Design Prompt (VLM)
    2. Prompt -> Image PNG (Image API)
    3. Image PNG -> Print-on-Demand / Shopify (Commerce)
    """

    async def generate_and_publish_merch(self, trend_topic: str) -> Optional[Dict[str, Any]]:
        """
        Orchestrates the entire reverse monetization flow.
        Returns the Shopify/POD product data if successful.
        """
        logger.info(f"[AutoMerch] Initiating pipeline for trend: {trend_topic}")
        
        # 1. Concept -> Design Prompt
        design_prompt = await self._generate_design_prompt(trend_topic)
        if not design_prompt:
            logger.error("[AutoMerch] Failed to generate design concept.")
            return None
            
        # 2. Design Prompt -> Image
        image_url = await self._generate_image(design_prompt)
        if not image_url:
            logger.error("[AutoMerch] Failed to generate image.")
            return None
            
        # 3. Publish to Store
        product_title = f"{trend_topic.title()} Official Merch"
        product_data = await self._publish_to_pod(product_title, image_url)
        
        if product_data:
            logger.info(f"[AutoMerch] Successfully published product: {product_data.get('url')}")
        else:
            logger.error("[AutoMerch] Failed to publish product. Auto-merch requires Printify/Shopify integration.")
            raise RuntimeError("Auto-merch publishing failed. Please configure Printify/Shopify API credentials.")
            
        return product_data

    async def _generate_design_prompt(self, trend: str) -> Optional[str]:
        prompt = f"""
        You are a highly skilled merchandise designer. We detected a viral trend: "{trend}".
        Write a hyper-specific, visual prompt for an AI Image Generator (like Midjourney or Flux) 
        to create a minimalist, typography-driven, or striking graphic design suitable for a black T-shirt.
        The design MUST be on a clean white or transparent background.
        
        Return ONLY the raw visual prompt text. No pleasantries. Max 3 sentences.
        """
        response = await ai_worker.analyze_viral_pattern(prompt)
        if "Error" not in response:
            return response.strip()
        return None

    async def _generate_image(self, design_prompt: str) -> Optional[str]:
        """
        Hits an image generation API. 
        We use pollinations.ai for free, fast prototyping.
        """
        encoded_prompt = httpx.utils.quote(design_prompt)
        width, height = 1024, 1024
        
        # Pollinations allows direct GET request for image generation
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        
        logger.info(f"[AutoMerch] Requesting design generation: {image_url}")
        
        # We don't download it here, we just return the URL so the POD service can download it directly.
        # In a production environment, we might download, remove the background, and upload to S3.
        return image_url

    async def _publish_to_pod(self, title: str, image_url: str) -> Optional[Dict[str, Any]]:
        """
        Mocks publishing to a Print-on-Demand (POD) service like Printful,
        which pushes the listing to Shopify.
        """
        # In a real implementation:
        # 1. Download image
        # TODO: Implement actual POD API integration
        # 1. POST to Printful/Printify API to create a product mockup
        # 2. POST to Shopify Admin API to create the listing
        
        logger.error("[AutoMerch] POD publishing not implemented. Please configure Printify/Shopify API credentials.")
        raise NotImplementedError("Auto-merch POD publishing requires Printify/Shopify API integration.")

base_auto_merch_service = AutoMerchService()
