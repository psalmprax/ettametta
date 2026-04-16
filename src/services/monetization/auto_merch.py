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
        
        return image_url

    async def _publish_to_pod(self, title: str, image_url: str) -> Optional[Dict[str, Any]]:
        """
        Publishes the design to Print-on-Demand (POD) via Printful API.
        Enforces "Real-First" policy: No mock products allowed.
        """
        api_key = settings.PRINTFUL_API_KEY
        
        if not api_key or api_key == "your_printful_api_key":
            logger.error("[AutoMerch] PRINTFUL_API_KEY is missing or invalid. Action required.")
            raise ValueError("Printful API Key not configured. Auto-merch requires a valid Printful integration.")

        logger.info(f"[AutoMerch] Publishing to Printful: {title}")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Create localized product sync data
        sync_product_data = {
            "sync_product": {
                "name": title,
                "thumbnail": image_url
            },
            "sync_variants": [
                {
                    "retail_price": "24.99",
                    "variant_id": 4011, # Men's Premium Tee (Black/L)
                    "files": [
                        {
                            "url": image_url,
                            "position": "front"
                        }
                    ]
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.printful.com/store/products",
                    headers=headers,
                    json=sync_product_data,
                    timeout=30.0
                )
                
                if response.status_code in [200, 201]:
                    data = response.json().get("result", {})
                    return {
                        "id": str(data.get("id")),
                        "title": data.get("name"),
                        "url": f"https://dashboard.printful.com/products/{data.get('id')}",
                        "status": "published",
                        "preview_url": image_url
                    }
                else:
                    error_detail = response.json().get("error", {}).get("message", response.text)
                    logger.error(f"[AutoMerch] Printful API Rejection: {response.status_code} - {error_detail}")
                    # Throw specific runtime error for user visibility
                    raise RuntimeError(f"Printful Rejection: {error_detail}")

        except httpx.RequestError as exc:
            logger.error(f"[AutoMerch] Network connectivity issue with Printful: {exc}")
            raise RuntimeError(f"Failed to reach Printful: {exc}")
        except Exception as e:
            logger.error(f"[AutoMerch] POD Pipeline Failure: {e}")
            raise

base_auto_merch_service = AutoMerchService()
