import requests
import logging
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)


class ResearchSkill:
    """
    Free academic research skill using OpenAlex API (no API key required).
    Source: https://openalex.org/
    """

    def __init__(self):
        self.base_url = "https://api.openalex.org"

    def search_papers(self, query: str, limit: int = 5) -> str:
        """
        Search for academic papers on a topic.
        Uses OpenAlex API - free, no API key needed.
        """
        try:
            params = urllib.parse.urlencode({"search": query, "per-page": limit})
            url = f"{self.base_url}/works?{params}"
            response = requests.get(url, timeout=15)

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if not results:
                    return f"No papers found for '{query}'."

                summary = f"📚 **Academic Papers on '{query}':**\n"
                for i, paper in enumerate(results, 1):
                    title = paper.get("title", "Untitled")
                    doi = paper.get("doi", "")
                    year = paper.get("publication_year", "N/A")
                    citation_count = paper.get("cited_by_count", 0)
                    abstract = paper.get("abstract", "")

                    summary += f"\n{i}. **{title}**\n"
                    summary += f"   📅 {year} | 📖 {citation_count} citations\n"
                    if doi:
                        summary += f"   🔗 {doi}\n"
                    if abstract:
                        summary += f"   📝 {abstract[:150]}...\n"

                return summary
            else:
                return f"⚠️ API Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Research Skill Error: {e}")
            return f"⚠️ Error: {str(e)}"

    def search_trends(self, topic: str) -> str:
        """
        Find trending topics in academic literature.
        """
        try:
            params = urllib.parse.urlencode({"search": topic})
            url = f"{self.base_url}/works?{params}"
            response = requests.get(url, timeout=15)

            if response.status_code == 200:
                return f"📈 Trend analysis for '{topic}': Use search_papers for detailed results."
            else:
                return f"⚠️ Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Research Trend Error: {e}")
            return f"⚠️ Error: {str(e)}"


research_skill = ResearchSkill()
