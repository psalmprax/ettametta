import logging
import json
from typing import Any
from groq import AsyncGroq
from src.api.config import settings
from src.api.utils.vault import get_secret
from .commerce_service import base_commerce_service

class PromoGenerator:
    def __init__(self):
        self.api_key = get_secret("groq_api_key")
        self.client = AsyncGroq(api_key=self.api_key)
        self.commerce = base_commerce_service
        self.model = "llama-3.3-70b-versatile"

    async def generate_promo_script(self, product_name: str, niche: str, duration_sec: int = 30) -> dict[str, Any]:
        """
        Generates a high-conversion promotional script for an affiliate product.
        Uses real commerce data if available.
        """
        # Fetch real product data if product_name is generic or to enrich the prompt
        real_products = await self.commerce.get_relevant_products(niche)
        
        target_product = product_name
        product_context = ""
        
        if real_products:
            # If product_name is generic, use the first real product
            if product_name.lower() in ["top product", "trending", "auto", ""]:
                p = real_products[0]
                target_product = p["name"]
                product_context = f"Product Details: {p['name']}, Price: {p['price']}, URL: {p['url']}, Source: {p['source']}"
            else:
                # Try to find matching real product
                match = next((p for p in real_products if p["name"].lower() == product_name.lower()), None)
                if match:
                    product_context = f"Product Details: {match['name']}, Price: {match['price']}, URL: {match['url']}, Source: {match['source']}"

        prompt = f"""
        You are a world-class direct response copywriter. 
        Generate a {duration_sec}-second viral promo script for:
        PRODUCT: {target_product}
        NICHE: {niche}
        {product_context}
        
        STRUCTURE:
        1. PROBLEM HOOK: Address a specific pain point in the niche. Stop them cold.
        2. THE SOLUTION: Introduce {target_product} as the only logical fix.
        3. SCARCITY & URGENCY: Force a decision. Mention limited stock, time-sensitive discounts, or "last chance" triggers.
        4. AGGRESSIVE CTA: Tell them exactly what to do. "Click the link NOW," "Don't miss out," "Check the bio immediately."
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "title": "Promo: {target_product}",
            "segments": [
                {{
                    "type": "hook | solution | urgency | cta",
                    "text": "The script text",
                    "visual_cue": "Aggressive, fast-paced cinematic effects",
                    "duration": 5
                }},
                ...
            ],
            "hashtags": ["#affiliate", "#{niche.lower().replace(' ', '')}", "#limitedoffer"]
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a conversion-focused script AI. Output JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            script_data = json.loads(content)
            
            # Inject real product info into the response for the frontend
            if real_products:
                script_data["real_product"] = next((p for p in real_products if p["name"] == target_product), real_products[0])
                
            return script_data
        except Exception as e:
            logging.error(f"Promo Generation Error: {e}")
            return {"error": str(e), "segments": []}

base_promo_generator = PromoGenerator()
