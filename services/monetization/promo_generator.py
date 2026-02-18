import logging
import json
from typing import Dict, Any, List, Optional
from groq import AsyncGroq
from api.config import settings
from .commerce_service import base_commerce_service

class PromoGenerator:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.commerce = base_commerce_service
        self.model = "llama-3.3-70b-versatile"

    async def generate_promo_script(self, product_name: str, niche: str, duration_sec: int = 30) -> Dict[str, Any]:
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
        1. PROBLEM HOOK: Address a specific pain point in the niche.
        2. THE SOLUTION: Introduce {target_product} as the ultimate fix.
        3. SCARCITY/CTA: High-pressure call to action. Include the price if mentioned in context.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "title": "Promo: {target_product}",
            "segments": [
                {{
                    "type": "hook",
                    "text": "The script text",
                    "visual_cue": "Aggressive, fast-paced stock footage",
                    "duration": 5
                }},
                ...
            ],
            "hashtags": ["#affiliate", "#{niche.lower().replace(' ', '')}", "#result"]
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
