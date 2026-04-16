import logging
import json
from typing import Dict, Any
from groq import Groq
from services.openclaw.config import settings

logger = logging.getLogger(__name__)

class MarketScreenerTool:
    """
    AI-driven tool for sentiment analysis and niche screening.
    Helps Agent Zero decide which trends are actually worth producing.
    """
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.MODEL

    def run(self, raw_trend_data: str) -> Dict[str, Any]:
        """
        Screens raw trend data for sentiment and conversion potential.
        """
        try:
            prompt = f"""
            Act as a Data Scientist and Affiliate Marketer.
            Analyze the following trend data:
            ---
            {raw_trend_data}
            ---
            Evaluate:
            1. Sentiment Score (0-100)
            2. Monetization Potential (High/Medium/Low)
            3. Recommended CTA type (Shop/Learn More/Join)
            
            Return ONLY a JSON object.
            """
            
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"}
            )
            return json.loads(chat_completion.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"MarketScreenerTool Error: {e}")
            return {"error": str(e)}

market_screener_tool = MarketScreenerTool()
