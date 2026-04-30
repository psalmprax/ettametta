import logging
import json
from src.services.llm.intelligence_hub import base_intelligence_service
from typing import Any

logger = logging.getLogger(__name__)

class VariantGenerator:
    """
    Handles generation of high-frequency content variants for A/B/n testing.
    Focuses on varying hooks, styles, and script phrasing to 'find winners fast'.
    """

    async def generate_variant_prompts(self, 
        original_prompt: str, 
        count: int = 5, 
        strategy: str = "hook_variation",
        session_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Generates N variant prompts based on the original concept.
        
        Strategies:
        - hook_variation: Changes the first 3-5 seconds of the script.
        - style_variation: Changes the visual style (e.g., Cinematic vs Raw).
        - pacing_variation: Changes the editing/cuts rhythm.
        """
        logger.info(f"🧬 [VariantGenerator] Generating {count} variants for: {original_prompt[:50]}...")

        prompt = f"""
        You are a 'Growth Loop Engineer'. Your goal is to generate {count} diverse variants of a video idea.
        The goal is to find which 'Hook' and 'Angle' performs best on social media.
        
        ORIGINAL PROMPT:
        {original_prompt}
        
        STRATEGY: {strategy}
        
        REQUIREMENTS:
        1. Each variant must have a unique HOOK (the first 3 seconds).
        2. Each variant must have a slightly different script tone (e.g., Urgent, Educational, Story-driven, Contrarian).
        3. Output a list of JSON objects.
        
        JSON STRUCTURE:
        [
            {{
                "variant_name": "Contrarian Hook",
                "modified_prompt": "...",
                "hook_text": "...",
                "suggested_style": "...",
                "logic": "Why this might win"
            }}
        ]
        """

        try:
            result = await base_intelligence_service.chat(
                prompt=prompt,
                system_prompt="You are a professional Content Growth Engineer. Output JSON ONLY.",
                session_id=session_id,
                json_mode=True
            )
            
            variants = json.loads(result["response"])
            if not isinstance(variants, list):
                # Fallback if it's a dict
                if "variants" in variants:
                    variants = variants["variants"]
                else:
                    variants = [variants]
            
            logger.info(f"✅ [VariantGenerator] Successfully generated {len(variants)} variants.")
            return variants[:count]

        except Exception as e:
            logger.error(f"Variant generation failed: {e}")
            return [{"modified_prompt": original_prompt, "variant_name": "Original", "logic": "Fallback"}]

base_variant_service = VariantGenerator()
