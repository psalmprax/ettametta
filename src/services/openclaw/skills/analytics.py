import requests
import logging
from src.api.config import settings
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)

class AnalyticsSkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        self.api_url = f"{settings.API_URL}/api/v1/analytics"

    def execute(self, action: str = "summary", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "revenue":
            return self.get_revenue_report()
        elif action == "posts":
            return self.get_recent_posts(limit=kwargs.get("limit", 5))
        return self.get_summary()


    def get_summary(self) -> str:
        """
        Fetches the high-level dashboard summary.
        """
        try:
            response = requests.get(f"{self.api_url}/stats/summary", headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                raw_data = response.json()
                data = raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data

                return (
                    "📊 **Empire Analytics Summary**:\n"
                    f"• Total Reach: `{data.get('total_reach', '0')}`\n"
                    f"• Active Trends: `{data.get('active_trends', 0)}`\n"
                    f"• Videos Processed: `{data.get('videos_processed', 0)}`\n"
                    f"• Success Rate: `{data.get('success_rate', '0%')}`\n"
                    f"• Engine Load: `{data.get('engine_load', '0%')}`"
                )
            elif response.status_code == 401:
                return "🔒 **Analytics Access Denied**: Agent needs authentication."
            else:
                return f"⚠️ **Analytics Error**: Status {response.status_code}"

        except Exception as e:
            logger.exception(f"Analytics Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

    def get_recent_posts(self, limit: int = 5) -> str:
        """
        Fetches the most recently published posts.
        """
        try:
            response = requests.get(f"{self.api_url}/posts", headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                raw_data = response.json()
                posts = raw_data.get("data", []) if isinstance(raw_data, dict) else raw_data

                if not posts:
                    return "📝 **Recent Posts**: No posts published yet."

                msg = "📝 **Recent Posts**:\n"
                for p in posts[:limit]:
                    title = p.get('title', 'Untitled')
                    view_count = p.get('view_count', 0)
                    msg += f"• *{title}* ({view_count} views)\n"
                return msg
            else:
                return f"⚠️ **Fetch Error**: Status {response.status_code}"
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

    def get_revenue_report(self) -> str:
        """
        Fetches the primary dashboard monetization report.
        """
        try:
            base_url = self.api_url.replace("/analytics", "/monetization")
            response = requests.get(f"{base_url}/report", headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                raw_data = response.json()
                data = raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data

                total = data.get('total_revenue', 0.0)
                epm = data.get('epm', 0.0)
                logs = data.get('logs', [])

                return (
                    "💰 **Revenue Report**:\n"
                    f"• Total Generated: `${total:.2f}`\n"
                    f"• estimated EPM: `${epm:.2f}`\n"
                    f"• Total Transactions: `{len(logs)}`"
                )
            else:
                return f"⚠️ **Revenue Fetch Error**: Status {response.status_code}"
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

analytics_skill = AnalyticsSkill()
