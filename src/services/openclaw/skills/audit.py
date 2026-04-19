import json
import logging
import requests
from datetime import datetime
from api.config import settings
from .memory import memory_skill
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class AuditSkill(OpenClawBaseSkill):
    """Platform-agnostic audit skill for analyzing user accounts across social platforms."""

    def __init__(self):
        super().__init__()
        # Platform monetization requirements
        self.monetization_requirements = {
            "youtube": {
                "subscribers": 1000,
                "watch_hours": 4000,
                "public_videos": 1,
                "program": "YouTube Partner Program",
            },
            "tiktok": {
                "followers": 10000,
                "avg_views": 100000,
                "monthly_views": 500000,
                "program": "TikTok Creator Fund",
            },
            "instagram": {
                "followers": 500,
                "avg_views": 15000,
                "program": "Instagram Monetization",
            },
            "facebook": {
                "followers": 10000,
                "avg_views": 50000,
                "program": "Facebook Monetization",
            },
            "x": {
                "followers": 5000000,
                "impressions": 5000000,
                "program": "X Premium Revenue Sharing",
            },
            "linkedin": {
                "followers": 15000,
                "program": "LinkedIn Creator Mode",
            },
            "snapchat": {
                "subscribers": 10000,
                "program": "Snapchat Spotlight",
            },
            "twitch": {
                "followers": 350,
                "avg_viewers": 7,
                "program": "Twitch Partnership",
            },
        }

    def execute(self, action: str = "audit", platform: str = "youtube", user_id: int = 1, competitor_url: str = None, **kwargs) -> str:
        """
        Standardized mission execution.
        Routes to audit or compare based on action.
        """
        # Ensure we have a valid user_id (could be passed in kwargs as well)
        uid = kwargs.get("user_id", user_id)
        
        if action == "compare" and competitor_url:
            return self.compare_with_competitor(uid, competitor_url, platform)
        return self.audit_account(uid, platform)

    def audit_account(self, user_id: int, platform: str = "youtube") -> str:
        """
        Perform a comprehensive audit of the user's account on any platform.
        Analyzes: account health, monetization readiness, growth opportunities.
        """
        platform_lower = platform.lower()

        try:
            if platform_lower == "youtube":
                return self._audit_youtube_account(user_id)
            elif platform_lower in ("tiktok", "tt"):
                return self._audit_tiktok_account(user_id)
            elif platform_lower in ("instagram", "ig"):
                return self._audit_instagram_account(user_id)
            elif platform_lower == "facebook":
                return self._audit_facebook_account(user_id)
            elif platform_lower in ("x", "twitter"):
                return self._audit_x_account(user_id)
            elif platform_lower == "linkedin":
                return self._audit_linkedin_account(user_id)
            elif platform_lower == "snapchat":
                return self._audit_snapchat_account(user_id)
            elif platform_lower == "twitch":
                return self._audit_twitch_account(user_id)
            else:
                return f"⚠️ Unsupported platform: {platform}. Supported: youtube, tiktok, instagram, facebook, x, linkedin, snapchat, twitch"
        except Exception as e:
            logger.error(f"{platform} Audit Error: {e}")
            return f"⚠️ {platform} Audit Error: {e}"

    def _get_user_token(self, platform: str, user_id: int) -> str | None:
        """Get user's OAuth token for specified platform."""
        try:
            from services.optimization.auth import token_manager

            token = token_manager.get_token(platform, user_id=user_id)
            return token
        except Exception as e:
            logger.error(f"Error getting {platform} token: {e}")
            return None

    def _fetch_platform_data(
        self, platform: str, access_token: str, user_id: int
    ) -> dict:
        """Fetch account data for any platform."""
        if platform == "youtube":
            return self._fetch_youtube_data(access_token)
        elif platform == "tiktok":
            return self._fetch_tiktok_data(access_token)
        elif platform == "instagram":
            return self._fetch_instagram_data(access_token)
        elif platform == "facebook":
            return self._fetch_facebook_data(access_token)
        elif platform in ("x", "twitter"):
            return self._fetch_x_data(access_token)
        elif platform == "linkedin":
            return self._fetch_linkedin_data(access_token)
        elif platform == "snapchat":
            return self._fetch_snapchat_data(access_token)
        elif platform == "twitch":
            return self._fetch_twitch_data(access_token)
        return {}

    def _analyze_monetization_readiness(
        self, platform: str, account_data: dict
    ) -> dict:
        """Analyze monetization readiness for any platform."""
        if platform == "youtube":
            return self._analyze_youtube_monetization(account_data)
        elif platform == "tiktok":
            return self._analyze_tiktok_monetization(account_data)
        elif platform == "instagram":
            return self._analyze_instagram_monetization(account_data)
        elif platform == "facebook":
            return self._analyze_facebook_monetization(account_data)
        elif platform in ("x", "twitter"):
            return self._analyze_x_monetization(account_data)
        elif platform == "linkedin":
            return self._analyze_linkedin_monetization(account_data)
        elif platform == "snapchat":
            return self._analyze_snapchat_monetization(account_data)
        elif platform == "twitch":
            return self._analyze_twitch_monetization(account_data)
        return {}

    def _generate_growth_strategy(
        self,
        platform: str,
        account_data: dict,
        monetization: dict,
        recent_content: list[dict],
    ) -> str:
        """Generate AI-powered growth strategy for any platform."""
        try:
            platform_name = platform.title()
            requirements = self.monetization_requirements.get(platform, {})

            # Extract common metrics
            followers = self._extract_followers(platform, account_data)
            total_views = self._extract_total_views(platform, account_data)
            content_count = self._extract_content_count(platform, account_data)

            # Calculate averages from recent content
            avg_engagement_score = self._calculate_avg_engagement_score(platform, recent_content)
            avg_views = self._calculate_avg_views(platform, recent_content)

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"You are a {platform_name} growth strategist specializing in rapid growth "
                            f"and monetization on {platform_name}. Create a 2-week actionable sprint plan. Include:\n"
                            "1. Week 1: Focus areas and daily actions\n"
                            "2. Week 2: Optimization and scaling\n"
                            "3. Specific content types to create\n"
                            "4. Posting schedule recommendation\n"
                            "5. Monetization activation steps\n"
                            "Be specific and actionable. Use bullet points."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Platform: {platform_name}\n"
                            f"Followers: {followers:,}\n"
                            f"Total Views: {total_views:,}\n"
                            f"Content Count: {content_count}\n\n"
                            f"Recent Content Performance:\n"
                            f"- Average views per post: {avg_views:,.0f}\n"
                            f"- Average engagement score: {avg_engagement_score:.1f}%\n"
                            f"- Posts analyzed: {len(recent_content)}\n\n"
                            f"Monetization Requirements for {requirements.get('program', 'Platform Monetization')}:\n"
                            + "\n".join(
                                [
                                    f"- {k.replace('_', ' ').title()}: {v:,}"
                                    for k, v in requirements.items()
                                    if k != "program"
                                ]
                            )
                            + f"\n\nCurrent Monetization Readiness: {monetization.get('completion_percentage', 0):.0f}%\n\n"
                            f"Generate a 2-week growth sprint plan to reach monetization."
                        ),
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.7,
                "max_tokens": 2000,
            }
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            groq_resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if groq_resp.status_code == 200:
                return groq_resp.json()["choices"][0]["message"]["content"]
            else:
                return f"⚠️ Strategy generation failed: {groq_resp.status_code}"

        except Exception as e:
            logger.error(f"Growth strategy error for {platform}: {e}")
            return f"⚠️ Strategy generation error: {e}"

    def _format_audit_report(
        self,
        platform: str,
        account_data: dict,
        monetization: dict,
        growth_strategy: str,
    ) -> str:
        """Format audit report for any platform."""
        platform_name = platform.title()
        requirements = self.monetization_requirements.get(platform, {})

        # Extract platform-specific data
        account_name = self._extract_account_name(platform, account_data)
        followers = self._extract_followers(platform, account_data)
        total_views = self._extract_total_views(platform, account_data)
        content_count = self._extract_content_count(platform, account_data)
        created_date = self._extract_created_date(platform, account_data)

        # Format monetization requirements table
        requirements_table = "\n".join(
            [
                f"| {k.replace('_', ' ').title()} | {v:,} | {'✅' if monetization.get(k, {}).get('eligible', False) else '❌'} |"
                for k, v in requirements.items()
                if k != "program"
            ]
        )

        audit_report = f"""📊 **{platform_name} Account Audit**

**Account:** {account_name}
**Created:** {created_date}
**Platform:** {platform_name}

---

### 📈 Statistics
| Metric | Value |
|--------|-------|
| Followers | {followers:,} |
| Total Views | {total_views:,} |
| Content Posts | {content_count:,} |

---

### 💰 Monetization Readiness ({requirements.get("program", "Platform Monetization")})
| Requirement | Required | Status |
|-------------|----------|--------|
{requirements_table}

**Overall Progress:** {monetization.get("completion_percentage", 0):.0f}% {"✅ Eligible for monetization!" if monetization.get("overall_eligible", False) else "❌ Not yet eligible"}

---

### 🚀 2-Week Growth Sprint

{growth_strategy}

---

*Audit completed at {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""
        return audit_report

    # Platform-specific implementations

    def _audit_youtube_account(self, user_id: int) -> str:
        """YouTube-specific account audit."""
        access_token = self._get_user_token("youtube", user_id)
        if not access_token:
            return self._get_auth_message("youtube")

        account_data = self._fetch_platform_data("youtube", access_token, user_id)
        if not account_data:
            return "⚠️ Could not fetch YouTube channel details. Please re-authenticate."

        monetization = self._analyze_monetization_readiness("youtube", account_data)
        recent_content = self._fetch_recent_content(
            "youtube", access_token, account_data.get("id", "")
        )
        growth_strategy = self._generate_growth_strategy(
            "youtube", account_data, monetization, recent_content
        )

        memory_skill.record_event(
            "account_audit",
            {
                "user_id": user_id,
                "platform": "youtube",
                "account": self._extract_account_name("youtube", account_data),
                "followers": self._extract_followers("youtube", account_data),
                "monetization_ready": monetization.get("overall_eligible", False),
            },
        )

        return self._format_audit_report(
            "youtube", account_data, monetization, growth_strategy
        )

    def _audit_tiktok_account(self, user_id: int) -> str:
        """TikTok-specific account audit."""
        access_token = self._get_user_token("tiktok", user_id)
        if not access_token:
            return self._get_auth_message("tiktok")

        account_data = self._fetch_platform_data("tiktok", access_token, user_id)
        monetization = self._analyze_monetization_readiness("tiktok", account_data)
        recent_content = self._fetch_recent_content(
            "tiktok", access_token, account_data.get("open_id", "")
        )
        growth_strategy = self._generate_growth_strategy(
            "tiktok", account_data, monetization, recent_content
        )

        memory_skill.record_event(
            "account_audit",
            {
                "user_id": user_id,
                "platform": "tiktok",
                "account": self._extract_account_name("tiktok", account_data),
                "followers": self._extract_followers("tiktok", account_data),
                "monetization_ready": monetization.get("overall_eligible", False),
            },
        )

        return self._format_audit_report(
            "tiktok", account_data, monetization, growth_strategy
        )

    def _audit_instagram_account(self, user_id: int) -> str:
        """Instagram-specific account audit."""
        access_token = self._get_user_token("instagram", user_id)
        if not access_token:
            return self._get_auth_message("instagram")

        account_data = self._fetch_platform_data("instagram", access_token, user_id)
        monetization = self._analyze_monetization_readiness("instagram", account_data)
        recent_content = self._fetch_recent_content(
            "instagram", access_token, account_data.get("id", "")
        )
        growth_strategy = self._generate_growth_strategy(
            "instagram", account_data, monetization, recent_content
        )

        memory_skill.record_event(
            "account_audit",
            {
                "user_id": user_id,
                "platform": "instagram",
                "account": self._extract_account_name("instagram", account_data),
                "followers": self._extract_followers("instagram", account_data),
                "monetization_ready": monetization.get("overall_eligible", False),
            },
        )

        return self._format_audit_report(
            "instagram", account_data, monetization, growth_strategy
        )

    # Simplified implementations for other platforms (can be expanded)
    def _audit_facebook_account(self, user_id: int) -> str:
        return self._audit_generic_account("facebook", user_id)

    def _audit_x_account(self, user_id: int) -> str:
        return self._audit_generic_account("x", user_id)

    def _audit_linkedin_account(self, user_id: int) -> str:
        return self._audit_generic_account("linkedin", user_id)

    def _audit_snapchat_account(self, user_id: int) -> str:
        return self._audit_generic_account("snapchat", user_id)

    def _audit_twitch_account(self, user_id: int) -> str:
        return self._audit_generic_account("twitch", user_id)

    def _audit_generic_account(self, platform: str, user_id: int) -> str:
        """Generic audit for platforms without full API integration yet."""
        access_token = self._get_user_token(platform, user_id)
        if not access_token:
            return self._get_auth_message(platform)

        return f"⚠️ {platform.title()} audit not fully implemented yet. Please check back soon!"

    def _get_auth_message(self, platform: str) -> str:
        """Get authentication message for any platform."""
        return (
            f"⚠️ {platform.title()} account not connected.\n\n"
            f"Please authenticate your {platform.title()} account in the dashboard:\n"
            f"→ {self.api_url}/dashboard/publishing"
        )

    # Platform-specific data fetching methods
    def _fetch_youtube_data(self, access_token: str) -> dict:
        """Fetch YouTube channel data."""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        try:
            creds = Credentials(token=access_token)
            youtube = build("youtube", "v3", credentials=creds)

            channels_response = (
                youtube.channels()
                .list(
                    part="snippet,statistics,status,contentDetails,brandingSettings",
                    mine=True,
                )
                .execute()
            )

            if channels_response.get("items"):
                return channels_response["items"][0]
            return {}
        except Exception as e:
            logger.error(f"Error fetching YouTube data: {e}")
            return {}

    def _fetch_tiktok_data(self, access_token: str) -> dict:
        """Fetch TikTok account data."""
        try:
            # TikTok API integration would go here
            # For now, return mock data structure
            return {
                "open_id": "mock_tiktok_id",
                "username": "mock_username",
                "display_name": "Mock TikTok Account",
                "follower_count": 5000,
                "video_count": 25,
                "total_views": 150000,
            }
        except Exception as e:
            logger.error(f"Error fetching TikTok data: {e}")
            return {}

    def _fetch_instagram_data(self, access_token: str) -> dict:
        """Fetch Instagram account data."""
        try:
            # Instagram Graph API integration would go here
            return {
                "id": "mock_instagram_id",
                "username": "mock_username",
                "name": "Mock Instagram Account",
                "followers_count": 1500,
                "media_count": 45,
                "total_views": 75000,
            }
        except Exception as e:
            logger.error(f"Error fetching Instagram data: {e}")
            return {}

    def _fetch_facebook_data(self, access_token: str) -> dict:
        return {}

    def _fetch_x_data(self, access_token: str) -> dict:
        return {}

    def _fetch_linkedin_data(self, access_token: str) -> dict:
        return {}

    def _fetch_snapchat_data(self, access_token: str) -> dict:
        return {}

    def _fetch_twitch_data(self, access_token: str) -> dict:
        return {}

    def _fetch_recent_content(
        self, platform: str, access_token: str, account_id: str, limit: int = 10
    ) -> list[dict]:
        """Fetch recent content for any platform."""
        if platform == "youtube":
            return self._fetch_youtube_videos(access_token, account_id, limit)
        elif platform == "tiktok":
            return self._fetch_tiktok_videos(access_token, account_id, limit)
        elif platform == "instagram":
            return self._fetch_instagram_posts(access_token, account_id, limit)
        return []

    def _fetch_youtube_videos(
        self, access_token: str, channel_id: str, limit: int = 10
    ) -> list[dict]:
        """Fetch recent YouTube videos."""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        try:
            creds = Credentials(token=access_token)
            youtube = build("youtube", "v3", credentials=creds)

            search_response = (
                youtube.search()
                .list(
                    part="id,snippet",
                    channelId=channel_id,
                    order="date",
                    maxResults=limit,
                    type="video",
                )
                .execute()
            )

            video_ids = [
                item["id"]["videoId"] for item in search_response.get("items", [])
            ]

            if video_ids:
                videos_response = (
                    youtube.videos()
                    .list(
                        part="statistics,contentDetails,snippet", id=",".join(video_ids)
                    )
                    .execute()
                )
                return videos_response.get("items", [])

            return []
        except Exception as e:
            logger.error(f"Error fetching YouTube videos: {e}")
            return []

    def _fetch_tiktok_videos(
        self, access_token: str, open_id: str, limit: int = 10
    ) -> list[dict]:
        """Fetch recent TikTok videos."""
        try:
            # TikTok API integration would go here
            return []
        except Exception as e:
            logger.error(f"Error fetching TikTok videos: {e}")
            return []

    def _fetch_instagram_posts(
        self, access_token: str, account_id: str, limit: int = 10
    ) -> list[dict]:
        """Fetch recent Instagram posts."""
        try:
            # Instagram Graph API integration would go here
            return []
        except Exception as e:
            logger.error(f"Error fetching Instagram posts: {e}")
            return []

    # Monetization analysis methods
    def _analyze_youtube_monetization(self, account_data: dict) -> dict:
        """Analyze YouTube monetization readiness."""
        stats = account_data.get("statistics", {})
        subscribers = int(stats.get("subscriberCount", 0))
        views = int(stats.get("viewCount", 0))
        video_count = int(stats.get("videoCount", 0))

        reqs = self.monetization_requirements["youtube"]
        readiness = {
            "subscribers": {
                "current": subscribers,
                "required": reqs["subscribers"],
                "eligible": subscribers >= reqs["subscribers"],
                "gap": max(0, reqs["subscribers"] - subscribers),
            },
            "watch_hours": {
                "current": views,
                "required": reqs["watch_hours"],
                "eligible": views >= reqs["watch_hours"],
                "gap": max(0, reqs["watch_hours"] - views),
            },
            "public_videos": {
                "current": video_count,
                "required": reqs["public_videos"],
                "eligible": video_count >= reqs["public_videos"],
            },
        }

        readiness["overall_eligible"] = all(r["eligible"] for r in readiness.values())
        readiness["completion_percentage"] = (
            sum(1 for r in readiness.values() if r.get("eligible", False))
            / len(readiness)
            * 100
        )

        return readiness

    def _analyze_tiktok_monetization(self, account_data: dict) -> dict:
        """Analyze TikTok monetization readiness."""
        followers = account_data.get("follower_count", 0)
        total_views = account_data.get("total_views", 0)
        video_count = account_data.get("video_count", 0)
        avg_views = total_views / max(video_count, 1)

        reqs = self.monetization_requirements["tiktok"]
        readiness = {
            "followers": {
                "current": followers,
                "required": reqs["followers"],
                "eligible": followers >= reqs["followers"],
                "gap": max(0, reqs["followers"] - followers),
            },
            "avg_views": {
                "current": avg_views,
                "required": reqs["avg_views"],
                "eligible": avg_views >= reqs["avg_views"],
                "gap": max(0, reqs["avg_views"] - avg_views),
            },
        }

        readiness["overall_eligible"] = all(r["eligible"] for r in readiness.values())
        readiness["completion_percentage"] = (
            sum(1 for r in readiness.values() if r.get("eligible", False))
            / len(readiness)
            * 100
        )

        return readiness

    def _analyze_instagram_monetization(self, account_data: dict) -> dict:
        """Analyze Instagram monetization readiness."""
        followers = account_data.get("followers_count", 0)
        total_views = account_data.get("total_views", 0)
        media_count = account_data.get("media_count", 0)
        avg_views = total_views / max(media_count, 1)

        reqs = self.monetization_requirements["instagram"]
        readiness = {
            "followers": {
                "current": followers,
                "required": reqs["followers"],
                "eligible": followers >= reqs["followers"],
                "gap": max(0, reqs["followers"] - followers),
            },
            "avg_views": {
                "current": avg_views,
                "required": reqs["avg_views"],
                "eligible": avg_views >= reqs["avg_views"],
                "gap": max(0, reqs["avg_views"] - avg_views),
            },
        }

        readiness["overall_eligible"] = all(r["eligible"] for r in readiness.values())
        readiness["completion_percentage"] = (
            sum(1 for r in readiness.values() if r.get("eligible", False))
            / len(readiness)
            * 100
        )

        return readiness

    def _analyze_facebook_monetization(self, account_data: dict) -> dict:
        return {}

    def _analyze_x_monetization(self, account_data: dict) -> dict:
        return {}

    def _analyze_linkedin_monetization(self, account_data: dict) -> dict:
        return {}

    def _analyze_snapchat_monetization(self, account_data: dict) -> dict:
        return {}

    def _analyze_twitch_monetization(self, account_data: dict) -> dict:
        return {}

    # Helper methods for data extraction
    def _extract_account_name(self, platform: str, data: dict) -> str:
        """Extract account name from platform data."""
        if platform == "youtube":
            return data.get("snippet", {}).get("title", "Unknown")
        elif platform == "tiktok":
            return data.get("display_name", "Unknown")
        elif platform == "instagram":
            return data.get("name", "Unknown")
        return "Unknown"

    def _extract_followers(self, platform: str, data: dict) -> int:
        """Extract follower count from platform data."""
        if platform == "youtube":
            return int(data.get("statistics", {}).get("subscriberCount", 0))
        elif platform == "tiktok":
            return data.get("follower_count", 0)
        elif platform == "instagram":
            return data.get("followers_count", 0)
        return 0

    def _extract_total_views(self, platform: str, data: dict) -> int:
        """Extract total views from platform data."""
        if platform == "youtube":
            return int(data.get("statistics", {}).get("viewCount", 0))
        elif platform == "tiktok":
            return data.get("total_views", 0)
        elif platform == "instagram":
            return data.get("total_views", 0)
        return 0

    def _extract_content_count(self, platform: str, data: dict) -> int:
        """Extract content count from platform data."""
        if platform == "youtube":
            return int(data.get("statistics", {}).get("videoCount", 0))
        elif platform == "tiktok":
            return data.get("video_count", 0)
        elif platform == "instagram":
            return data.get("media_count", 0)
        return 0

    def _extract_created_date(self, platform: str, data: dict) -> str:
        """Extract account creation date from platform data."""
        if platform == "youtube":
            return data.get("snippet", {}).get("publishedAt", "Unknown")
        return "Unknown"

    def _calculate_avg_engagement_score(self, platform: str, content: list[dict]) -> float:
        """Calculate average engagement score from recent content."""
        if not content:
            return 0.0

        total_engagement = 0
        for item in content:
            if platform == "youtube":
                likes = int(item.get("statistics", {}).get("likeCount", 0))
                comments = int(item.get("statistics", {}).get("commentCount", 0))
                views = int(item.get("statistics", {}).get("viewCount", 0))
                if views > 0:
                    total_engagement += (likes + comments) / views * 100
            elif platform == "tiktok":
                # TikTok engagement calculation
                total_engagement += 5.0  # Placeholder
            elif platform == "instagram":
                # Instagram engagement calculation
                total_engagement += 3.0  # Placeholder

        return total_engagement / len(content) if content else 0.0

    def _calculate_avg_views(self, platform: str, content: list[dict]) -> float:
        """Calculate average views from recent content."""
        if not content:
            return 0.0

        total_views = 0
        for item in content:
            if platform == "youtube":
                total_views += int(item.get("statistics", {}).get("viewCount", 0))
            elif platform == "tiktok":
                total_views += item.get("view_count", 0)
            elif platform == "instagram":
                total_views += item.get("views", 0)

        return total_views / len(content) if content else 0.0

    def compare_with_competitor(
        self, user_id: int, competitor_url: str, platform: str = "youtube"
    ) -> str:
        """
        Compare user's account with a competitor and generate gap analysis.
        """
        try:
            from skills.competitor import CompetitorSkill

            competitor_skill = CompetitorSkill()
            competitor_analysis = competitor_skill.analyze_competitor(
                competitor_url, platform=platform
            )

            user_audit = self.audit_account(user_id, platform)

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"You are a {platform.title()} growth strategist. Compare the user's account audit "
                            "with the competitor analysis and provide actionable insights on how to "
                            "close the gap. Focus on specific strategies the user can implement."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"USER'S ACCOUNT AUDIT:\n{user_audit}\n\n"
                            f"COMPETITOR ANALYSIS:\n{competitor_analysis}\n\n"
                            f"Provide a gap analysis and specific actions to beat this competitor."
                        ),
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.7,
                "max_tokens": 1500,
            }
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            groq_resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if groq_resp.status_code == 200:
                gap_analysis = groq_resp.json()["choices"][0]["message"]["content"]
                return f"📊 **{platform.title()} Competitor Gap Analysis**\n\n{gap_analysis}"
            else:
                return f"⚠️ Gap analysis failed: {groq_resp.status_code}"

        except Exception as e:
            logger.error(f"Competitor comparison error: {e}")
            return f"⚠️ Comparison error: {e}"


audit_skill = AuditSkill()


