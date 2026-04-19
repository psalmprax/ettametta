import requests
import logging
import re
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class SocialMetricsSkill(OpenClawBaseSkill):
    """
    Free social media metrics skill using web scraping (no API keys required).
    Note: May be limited by rate limiting and anti-bot protection.
    """

    def __init__(self):
        super().__init__()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def execute(self, action: str = "scan", platform: str = "", handle: str = "", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        plt = (platform or kwargs.get("platform", "")).lower()
        hdl = handle or kwargs.get("handle", "")
        
        if plt == "x":
            return self.get_x_followers(hdl)
        elif plt == "reddit":
            return self.get_reddit_stats(hdl)
        elif plt == "github":
            return self.get_github_stats(hdl)
        elif plt == "instagram":
            return self.get_instagram_profile(hdl)
        
        # Multi-platform fallback
        handles = kwargs.get("handles", {})
        if handles:
            return self.get_multi_platform(handles)
            
        return f"⚠️ Unsupported platform: {plt}"

    def get_x_followers(self, username: str) -> str:
        """
        Get X (Twitter) follower count via web scraping.
        """
        try:
            url = f"https://x.com/{username}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                # Extract follower count from page
                match = re.search(r"(\d[\d,]*) Followers", response.text)
                if match:
                    return f"@{username}: {match.group(1)} followers"
                return f"Could not extract followers for @{username}"
            elif response.status_code == 404:
                return f"User @{username} not found"
            else:
                return f"⚠️ Error: {response.status_code}"

        except Exception as e:
            logger.error(f"X Metrics Error: {e}")
            return f"⚠️ Error: {str(e)}"

    def get_reddit_stats(self, subreddit: str) -> str:
        """
        Get subreddit stats via public API (no auth needed).
        """
        try:
            url = f"https://www.reddit.com/r/{subreddit}/about.json"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                info = data.get("data", {})

                members = info.get("subscribers", 0)
                online = info.get("active_user_count", 0)
                description = info.get("public_description", "")[:100]

                return f"📊 **r/{subreddit}**\n   👥 {members:,} members\n   🟢 {online:,} online\n   📝 {description}"
            else:
                return f"⚠️ Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Reddit Stats Error: {e}")
            return f"⚠️ Error: {str(e)}"

    def get_youtube_channel(self, channel_url: str) -> str:
        """
        Get YouTube channel stats - requires YouTube Data API for full access.
        This is a placeholder that returns info about limitation.
        """
        return "📺 YouTube metrics require YouTube Data API key. Use RSS feeds for free alternative."

    def get_instagram_profile(self, username: str) -> str:
        """
        Get Instagram profile - limited without API.
        """
        try:
            url = f"https://www.instagram.com/{username}/"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                # Try to extract from page (limited)
                match = re.search(r"([\d,]+) Followers", response.text)
                if match:
                    return f"@{username}: {match.group(1)} followers"
                return f"Profile found but metrics unavailable"
            elif response.status_code == 404:
                return f"User @{username} not found"
            else:
                return f"⚠️ Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Instagram Error: {e}")
            return f"⚠️ Error: {str(e)}"

    def get_github_stats(self, username: str) -> str:
        """
        Get GitHub user stats (free, no API key needed).
        """
        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                repos = data.get("public_repos", 0)
                followers = data.get("followers", 0)
                following = data.get("following", 0)
                name = data.get("name", username)

                return f"🐙 **{name}** (@{username})\n   ⭐ {repos} repos | 👥 {followers} followers | 👤 {following} following"
            elif response.status_code == 404:
                return f"User @{username} not found"
            else:
                return f"⚠️ Error: {response.status_code}"

        except Exception as e:
            logger.error(f"GitHub Error: {e}")
            return f"⚠️ Error: {str(e)}"

    def get_multi_platform(self, handles: dict[str, str]) -> str:
        """
        Get metrics for multiple platforms.
        Expected format: {"x": "username", "reddit": "subreddit", "github": "username"}
        """
        results = []

        for platform, handle in handles.items():
            if platform == "x":
                results.append(self.get_x_followers(handle))
            elif platform == "reddit":
                results.append(self.get_reddit_stats(handle))
            elif platform == "github":
                results.append(self.get_github_stats(handle))
            elif platform == "instagram":
                results.append(self.get_instagram_profile(handle))
            else:
                results.append(f"Unknown platform: {platform}")

        return "\n\n".join(results)


social_metrics_skill = SocialMetricsSkill()
