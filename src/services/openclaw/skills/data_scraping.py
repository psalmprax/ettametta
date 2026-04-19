import logging
import requests
from api.config import settings
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)

class DataScrapingSkill(OpenClawBaseSkill):
    """
    CashClaw Official Skill: Data Scraping
    Provides unified scraping capabilities to supplement the discovery service.
    """
    def execute(self, action: str = "scrape", url: str = "", extract_fields: list = None, **kwargs) -> str:
        """
        Executes the Data Scraping mission.
        """
        target_url = url or kwargs.get("url") or kwargs.get("target_url")
        if not target_url:
            return "⚠️ Data Scraping failed: Missing URL"
            
        fields = extract_fields or kwargs.get("extract_fields")
        
        self.logger.info(f"[Data Scraping] Executing scrape for {target_url}")
        
        try:
            # Simulated Jina/Scraping API call
            # In production, this would call Jina Reader API or a Playwright service
            jina_url = f"https://r.jina.ai/{target_url}"
            resp = requests.get(jina_url, timeout=20)
            
            if resp.status_code == 200:
                scraped_text = resp.text
                
                # If fields are requested, use LLM to extract structured data
                if fields:
                    return self._extract_structured_data(scraped_text, fields, target_url)
                
                return f"🕸️ **Data Scraped Successfully**\n\nURL: {target_url}\nContent Length: {len(scraped_text)} characters.\n\nPreview:\n{scraped_text[:500]}..."
            else:
                return f"⚠️ Data Scraping failed: Status {resp.status_code}"
                
        except Exception as e:
            self.logger.error(f"Data Scraping Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"
            
    def _extract_structured_data(self, text: str, fields: list, url: str) -> str:
        fields_str = ", ".join(fields)
        try:
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"You are an expert data extraction bot. Extract the following fields from the text: {fields_str}. "
                            "Format the output as a clean markdown list or JSON block."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Text:\n{text[:8000]}", # truncate to fit context
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.1,
                "max_tokens": 1500,
            }
            
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=20,
            )
            
            if resp.status_code == 200:
                extraction = resp.json()["choices"][0]["message"]["content"]
                return f"🕸️ **Structured Data Extracted**\n\nURL: {url}\n\n{extraction}"
            else:
                return f"⚠️ Extraction failed: Status {resp.status_code}"
                
        except Exception as e:
            self.logger.error(f"Data Extraction Error: {e}")
            return f"⚠️ Extraction Error: {str(e)}"

data_scraping_skill = DataScrapingSkill()
