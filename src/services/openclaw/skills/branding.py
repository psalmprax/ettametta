import os
import logging
import json
from typing import Any
from .perchance import perchance_skill

from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class BrandingSkill(OpenClawBaseSkill):
    def __init__(self, branding_dir: str = "assets/branding"):
        super().__init__()
        self.branding_dir = branding_dir
        os.makedirs(branding_dir, exist_ok=True)

    async def execute(
        self, action: str = "identity", niche: str = "General", **kwargs
    ) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "identity":
            client = kwargs.get("client")
            result = await self.generate_identity(niche, client)

            if result.get("status") == "success":
                return (
                    f"🎨 **Brand Identity: {result['brand_name']}**\n"
                    f"• Primary Color: `{result['primary_color']}`\n"
                    f"• Logo URL: {result['logo_url']}\n"
                    f"• Brief: {result['visual_prompt']}"
                )
            return "⚠️ Branding generation failed."

        return f"⚠️ Unknown action for Branding: {action}. Valid actions: identity"

    async def generate_identity(self, niche: str, client: Any = None) -> dict[str, Any]:
        """
        Generate brand identity (Logo, Name, Color) using AI.
        Runs inside OpenClaw to leverage playwright/perchance.
        """
        brand_name = f"{niche} Channel"
        visual_prompt = f"Professional minimalist logo for a {niche} brand, high-quality vector style, 1:1 ratio, centered, white on dark background"
        primary_color = "#FFFFFF"

        if client:
            try:
                system_prompt = "You are a world-class brand identity designer. Create a visual brief for a new brand logo."
                user_prompt = f"""
                Niche: {niche}
                Task: Generate a 1-sentence visual prompt for an AI image generator to create a professional logo.
                Also suggest a Brand Name (2 words max) and a Primary Hex Color.

                Return ONLY a JSON object:
                {{
                    "brand_name": "string",
                    "visual_prompt": "string",
                    "primary_color": "hex_code"
                }}
                """

                if hasattr(client, "chat"):
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.7,
                    )
                    brand_data = json.loads(response.choices[0].message.content)
                    brand_name = brand_data.get("brand_name", brand_name)
                    visual_prompt = brand_data.get("visual_prompt", visual_prompt)
                    primary_color = brand_data.get("primary_color", primary_color)
            except Exception as e:
                logger.warning(f"[BrandingSkill] AI brief generation failed: {e}")

        logger.info(f"[BrandingSkill] Synthesizing logo for {brand_name}")
        result = await perchance_skill.generate(
            prompt=visual_prompt,
            generator="product",
            resolution="square",
            aspect_ratio="1:1",
        )

        logo_url = None
        if result.get("status") == "success" and result.get("image_uris"):
            logo_url = result["image_uris"][0]

        return {
            "brand_name": brand_name,
            "logo_url": logo_url,
            "primary_color": primary_color,
            "visual_prompt": visual_prompt,
            "status": "success" if logo_url else "failed",
        }


branding_skill = BrandingSkill()
