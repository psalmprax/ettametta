import requests
import logging
from config import settings

logger = logging.getLogger(__name__)

class AnalyticsSkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}/analytics"

    def get_summary(self) -> str:
        """
        Fetches the high-level dashboard summary.
        """
        try:
            # Note: This endpoint usually requires auth. 
            # For the MVP agent, we might need to bypass or use a service token.
            # Assuming widely accessible or internal network trust for now based on docker-compose.
            # If auth fails, we will need to add a token header in the future.
            
            response = requests.get(f"{self.api_url}/stats/summary", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                return (
                    f"📊 **Empire Analytics Summary**:\n"
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
            logger.error(f"Analytics Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

    def get_recent_posts(self, limit: int = 5) -> str:
        """
        Fetches the most recently published posts.
        """
        try:
            response = requests.get(f"{self.api_url}/posts", timeout=10)
            if response.status_code == 200:
                posts = response.json()
                if not posts:
                    return "📝 **Recent Posts**: No posts published yet."
                
                msg = "📝 **Recent Posts**:\n"
                for p in posts[:limit]:
                    title = p.get('metadata', {}).get('title', 'Untitled')
                    views = p.get('performance', {}).get('views', 0)
                    msg += f"• *{title}* ({views} views)\n"
                return msg
            else:
                return f"⚠️ **Fetch Error**: Status {response.status_code}"
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

    def get_revenue_report(self) -> str:
        """
        Fetches the primary dashboard monetization report.
        Note: The endpoint is on the /monetization router.
        """
        try:
            # We access the monetization endpoint from the main API URL
            base_url = self.api_url.replace("/analytics", "/monetization")
            response = requests.get(f"{base_url}/report", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                total = data.get('total_revenue', 0.0)
                epm = data.get('epm', 0.0)
                logs = data.get('logs', [])
                
                return (
                    f"💰 **Revenue Report**:\n"
                    f"• Total Generated: `${total:.2f}`\n"
                    f"• estimated EPM: `${epm:.2f}`\n"
                    f"• Total Transactions: `{len(logs)}`"
                )
            else:
                return f"⚠️ **Revenue Fetch Error**: Status {response.status_code}"
        except Exception as e:
            return f"⚠️ Skill Error: {str(e)}"

analytics_skill = AnalyticsSkill()
