import requests
import logging
from datetime import datetime, timedelta
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class DataIngestionSkill(OpenClawBaseSkill):
    """
    Free multi-source data ingestion skill.
    Sources: RSS feeds, Reddit (public), YouTube (via RSS), GitHub trending.
    No API keys required - uses public endpoints.
    """

    def __init__(self):
        super().__init__()
        self.reddit_url = "https://www.reddit.com"

    def execute(self, action: str = "ingest", source: str = "", limit: int = 5, **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "reddit":
            return self.reddit_hot(source, limit)
        elif action == "rss":
            return self.fetch_rss(source, limit)
        elif action == "github":
            return self.github_trending(source, timeframe=kwargs.get("timeframe", "daily"), limit=limit)

        # Multi-source fallback
        sources = kwargs.get("sources", [])
        if sources:
            return self.ingest_multi_source(sources)

        return f"⚠️ Unsupported ingestion action: {action}"

    def fetch_rss(self, feed_url: str, limit: int = 5) -> str:
        """
        Fetch and parse RSS feed items.
        """
        try:
            headers = {"User-Agent": "ettametta/1.0"}
            response = requests.get(feed_url, headers=headers, timeout=10)

            if response.status_code != 200:
                return f"⚠️ RSS Error: {response.status_code}"

            # Simple XML parsing - extract titles and links
            content = response.text
            items = []
            import re

            titles = re.findall(
                r"<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>", content
            )
            links = re.findall(r"<link>(.*?)</link>", content)

            for i, (title, _) in enumerate(
                titles[1 : limit + 1]
            ):  # Skip first (feed title)
                link = links[i + 1] if i + 1 < len(links) else "#"
                items.append({"title": title, "link": link})

            if not items:
                return "No items found in RSS feed."

            summary = "📰 **RSS Feed Results:**\n"
            for i, item in enumerate(items, 1):
                summary += f"{i}. {item['title']}\n   🔗 {item['link']}\n"
            return summary

        except Exception as e:
            logger.exception(f"RSS Error: {e}")
            return f"⚠️ Error: {str(e)}"

    def reddit_hot(self, subreddit: str, limit: int = 5) -> str:
        """
        Fetch hot posts from a subreddit (public, no auth needed).
        """
        try:
            url = f"{self.reddit_url}/r/{subreddit}/hot.json"
            headers = {"User-Agent": "ettametta/1.0"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])

                if not posts:
                    return f"No posts found in r/{subreddit}"

                summary = f"🔥 **r/{subreddit} Hot Posts:**\n"
                for i, post in enumerate(posts[:limit], 1):
                    post_data = post.get("data", {})
                    title = post_data.get("title", "Untitled")
                    score = post_data.get("score", 0)
                    comments = post_data.get("num_comments", 0)
                    url = post_data.get("url", "#")

                    summary += f"{i}. {title}\n"
                    summary += f"   👍 {score} | 💬 {comments} | [Link]({url})\n"
                return summary
            else:
                return f"⚠️ Reddit Error: {response.status_code}"

        except Exception as e:
            logger.exception(f"Reddit Error: {e}")
            return f"⚠️ Error: {str(e)}"

    def github_trending(
        self, language: str = "", timeframe: str = "daily", limit: int = 5
    ) -> str:
        """
        Fetch GitHub trending repos.
        """
        try:
            import urllib.parse

            query = (
                f"created:>{(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')}"
            )
            if language:
                query += f" language:{language}"

            params = urllib.parse.urlencode(
                {"q": query, "sort": "stars", "per_page": limit}
            )
            url = f"https://api.github.com/search/repositories?{params}"

            headers = {"User-Agent": "ettametta/1.0"}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return f"⚠️ GitHub Error: {response.status_code}"

            data = response.json()
            if not data:
                return "⚠️ No data returned from GitHub"

            items = data.get("items")
            if not items:
                return "⚠️ No repositories found"

            repos = items[:limit]
            summary = "⭐ **GitHub Trending:**\n"
            for i, repo in enumerate(repos, 1):
                name = repo.get("full_name", "Unknown")
                stars = repo.get("stargazers_count", 0)
                desc = repo.get("description", "No description") or "No description"
                repo_url = repo.get("html_url", "#")

                summary += f"{i}. **{name}** ⭐{stars}\n"
                summary += f"   {desc[:80]}...\n   🔗 {repo_url}\n"
            return summary

        except Exception as e:
            logger.exception(f"GitHub Error: {e}")
            return f"⚠️ Error: {str(e)}"

    def youtube_trending(self, region: str = "US") -> str:
        """
        Get YouTube trending via RSS (no API key).
        """
        try:
            # Hardened: YouTube true trending requires API authentication.
            # No placeholders allowed.
            return (
                "📺 YouTube trending requires a valid GOOGLE_API_KEY. Feature locked."
            )
        except Exception as e:
            logger.exception(f"YouTube Error: {e}")
            return f"⚠️ Error: {str(e)}"

    def ingest_multi_source(self, sources: list[str]) -> str:
        """
        Ingest data from multiple sources.
        Expected format: ["reddit:technology", "rss:https://.../", "github:python"]
        """
        results = []
        for source in sources:
            try:
                parts = source.split(":", 1)
                if len(parts) != 2:
                    continue

                source_type, value = parts

                if source_type == "reddit":
                    results.append(self.reddit_hot(value))
                elif source_type == "rss":
                    results.append(self.fetch_rss(value))
                elif source_type == "github":
                    results.append(self.github_trending(value))
                else:
                    results.append(f"Unknown source: {source_type}")

            except Exception as e:
                results.append(f"⚠️ Error: {str(e)}")

        return "\n\n".join(results) if results else "No sources provided."


data_ingestion_skill = DataIngestionSkill()
