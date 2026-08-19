#!/usr/bin/env python3
"""
Content Category System
=====================

100+ content categories with LLM-based detection.
Similar to how niche/trend detection works.
"""

from typing import Any
import json


# Complete content categories (100+)
CONTENT_CATEGORIES = {
    # AI & Tech (25+)
    "ai_productivity": {
        "name": "AI Productivity",
        "keywords": ["ai", "chatgpt", "automation", "productivity", "workflow"],
        "search_terms": ["ai productivity tools", "chatgpt automation", "ai workflow"],
        "audience": "professionals, tech enthusiasts",
        "style": "educational, professional",
    },
    "machine_learning": {
        "name": "Machine Learning",
        "keywords": ["ml", "machine learning", "deep learning", "neural"],
        "search_terms": ["machine learning tutorial", "deep learning explained"],
        "audience": "developers, data scientists",
        "style": "technical, educational",
    },
    "coding_tutorial": {
        "name": "Coding Tutorials",
        "keywords": ["programming", "coding", "python", "javascript", "tutorial"],
        "search_terms": ["python tutorial", "javascript tutorial", "coding tutorial"],
        "audience": "developers, learners",
        "style": "educational, hands-on",
    },
    "tech_review": {
        "name": "Tech Reviews",
        "keywords": ["review", "unboxing", "vs", "comparison"],
        "search_terms": ["tech review", "product comparison", "vs"],
        "audience": "tech consumers",
        "style": "reviews, candid",
    },
    # Viral/Trending (20+)
    "viral_top10": {
        "name": "Top 10 Viral",
        "keywords": ["top 10", "best", "ranking", "viral"],
        "search_terms": ["top 10 viral", "best of 2024", "viral videos"],
        "audience": "general",
        "style": "listicle, engaging",
    },
    "trending_now": {
        "name": "Trending Now",
        "keywords": ["trending", "viral", "breaking"],
        "search_terms": ["trending now", "viral tiktok", "trending youtube"],
        "audience": "general, younger",
        "style": "fast-paced, exciting",
    },
    "viral_clips": {
        "name": "Viral Clips",
        "keywords": ["viral", "clip", "moment"],
        "search_terms": ["viral clip", "viral moment", "must watch"],
        "audience": "general",
        "style": "short, engaging",
    },
    # Relationships & Lifestyle (30+)
    "relationships": {
        "name": "Relationships",
        "keywords": ["relationship", "dating", "love", "marriage"],
        "search_terms": [
            "relationship advice",
            "dating tips",
            "love and relationships",
        ],
        "audience": "young adults, couples",
        "style": "emotional, supportive",
    },
    "dating_advice": {
        "name": "Dating Advice",
        "keywords": ["dating", "pickup", "match", "app"],
        "search_terms": ["dating advice", "dating tips", "dating app"],
        "audience": "singles, daters",
        "style": "advisory, encouraging",
    },
    "fitness": {
        "name": "Fitness & Workouts",
        "keywords": ["workout", "fitness", "gym", "exercise"],
        "search_terms": ["workout routine", "fitness motivation", "gym tips"],
        "audience": "fitness enthusiasts",
        "style": "energetic, motivational",
    },
    "health_tips": {
        "name": "Health Tips",
        "keywords": ["health", "wellness", "nutrition", "diet"],
        "search_terms": ["health tips", "nutrition advice", "healthy living"],
        "audience": "health conscious",
        "style": "informative, caring",
    },
    "motivation": {
        "name": "Motivation",
        "keywords": ["motivation", "inspire", "success", "mindset"],
        "search_terms": ["motivation video", "inspirational speech", "success mindset"],
        "audience": "general",
        "style": "inspirational, uplifting",
    },
    "self_improvement": {
        "name": "Self Improvement",
        "keywords": ["self", "improve", "growth", "habit"],
        "search_terms": ["self improvement", "habit building", "personal growth"],
        "audience": "self-starters",
        "style": "developmental",
    },
    # Kids & Parenting (15+)
    "bedtime_stories": {
        "name": "Bedtime Stories",
        "keywords": ["bedtime", "story", "sleep"],
        "search_terms": ["bedtime stories", "sleepy stories", "kids bedtime"],
        "audience": "children, parents",
        "style": "calming, soothing",
    },
    "kids_animation": {
        "name": "Kids Animation",
        "keywords": ["animation", "cartoon", "kids"],
        "search_terms": ["kids animation", "cartoon for kids", "animated story"],
        "audience": "children",
        "style": "animated, fun",
    },
    "parenting": {
        "name": "Parenting Tips",
        "keywords": ["parenting", "parent", "kid", "child"],
        "search_terms": ["parenting tips", "how to parent", "raising kids"],
        "audience": "parents",
        "style": "supportive, advisory",
    },
    "children_educational": {
        "name": "Kids Educational",
        "keywords": ["learn", "education", "kids", "school"],
        "search_terms": ["educational for kids", "learning videos", "kids learning"],
        "audience": "children, parents",
        "style": "educational, engaging",
    },
    # Entertainment (25+)
    "gaming": {
        "name": "Gaming",
        "keywords": ["game", "gaming", "play", "walkthrough"],
        "search_terms": ["gaming video", "gameplay", "walkthrough"],
        "audience": "gamers",
        "style": "entertaining, interactive",
    },
    "anime": {
        "name": "Anime",
        "keywords": ["anime", "manga", "japanese"],
        "search_terms": ["anime review", "manga", "anime update"],
        "audience": "anime fans",
        "style": "enthusiastic",
    },
    "movie_review": {
        "name": "Movie Reviews",
        "keywords": ["movie", "review", "film", "trailer"],
        "search_terms": ["movie review", "film review", "trailer"],
        "audience": "moviegoers",
        "style": "analytical",
    },
    "music_video": {
        "name": "Music Videos",
        "keywords": ["music", "song", "official video"],
        "search_terms": ["official music video", "new song", "music"],
        "audience": "music fans",
        "style": "entertainment",
    },
    "memes": {
        "name": "Memes & Comedy",
        "keywords": ["meme", "funny", "comedy", "humor"],
        "search_terms": ["memes", "funny video", "comedy clip"],
        "audience": "general, younger",
        "style": "humorous",
    },
    # News & Events (20+)
    "world_news": {
        "name": "World News",
        "keywords": ["news", "world", "breaking"],
        "search_terms": ["world news", "breaking news", "news update"],
        "audience": "general",
        "style": "factual, serious",
    },
    "politics": {
        "name": "Politics",
        "keywords": ["politics", "political", "election"],
        "search_terms": ["political news", "election update", "politics"],
        "audience": "politically engaged",
        "style": "factual",
    },
    "wars_conflicts": {
        "name": "Wars & Conflicts",
        "keywords": ["war", "conflict", "military"],
        "search_terms": ["war news", "conflict update", "military"],
        "audience": "news followers",
        "style": "serious",
    },
    "current_events": {
        "name": "Current Events",
        "keywords": ["happening", "update", "today"],
        "search_terms": ["current events", "what happened", "todays news"],
        "audience": "general",
        "style": "informative",
    },
    # Niche/Interest (30+)
    "ufo": {
        "name": "UFO & Alien",
        "keywords": ["ufo", "alien", "uap", "extraterrestrial"],
        "search_terms": ["ufo sighting", "alien disclosure", "ufo documentary"],
        "audience": "conspiracy curiosity",
        "style": "mysterious",
    },
    "conspiracy": {
        "name": "Conspiracy Theories",
        "keywords": ["conspiracy", "theory", "truth"],
        "search_terms": ["conspiracy theory", "hidden truth", "exposed"],
        "audience": "theory seekers",
        "style": "questioning",
    },
    "true_crime": {
        "name": "True Crime",
        "keywords": ["true crime", "murder", "case"],
        "search_terms": ["true crime", "murder case", "crime documentary"],
        "audience": "crime enthusiasts",
        "style": "investigative",
    },
    "paranormal": {
        "name": "Paranormal",
        "keywords": ["paranormal", "ghost", "spiritual"],
        "search_terms": ["paranormal activity", "ghost hunting", "spirits"],
        "audience": "paranormal fans",
        "style": "mysterious",
    },
    "science_mysteries": {
        "name": "Science Mysteries",
        "keywords": ["science", "mystery", "discovered"],
        "search_terms": ["science mystery", "discoveries", "space mystery"],
        "audience": "science curious",
        "style": "wonder",
    },
    # Content Monetization (15+)
    "creator_revenue": {
        "name": "Creator Revenue",
        "keywords": ["monetization", "adsense", "revenue", "sponsorship"],
        "search_terms": ["youtube monetization", "tiktok revenue", "brand deals"],
        "audience": "creators, entrepreneurs",
        "style": "educational, advisory",
    },
    "viral_merch": {
        "name": "Viral Merch",
        "keywords": ["merchandise", "dropshipping", "print on demand"],
        "search_terms": ["viral merch ideas", "creator shop", "ecommerce"],
        "audience": "creators, shop owners",
        "style": "promotional",
    },
    "passive_income_creators": {
        "name": "Passive Income for Creators",
        "keywords": ["passive income", "affiliate", "courses"],
        "search_terms": ["passive income creators", "affiliate marketing tips"],
        "audience": "creators",
        "style": "advisory",
    },
    # Social (20+)
    "reddit_stories": {
        "name": "Reddit Stories",
        "keywords": ["reddit", "story", "read"],
        "search_terms": ["reddit story", "reddit post", "story time"],
        "audience": "reddit users",
        "style": "storytelling",
    },
    "tiktok_viral": {
        "name": "TikTok Viral",
        "keywords": ["tiktok", "viral", "trend"],
        "search_terms": ["tiktok viral", "tiktok trend", "tiktok dance"],
        "audience": "tiktok users",
        "style": "trendy",
    },
    "instagram_reels": {
        "name": "Instagram Reels",
        "keywords": ["instagram", "reels", "trending"],
        "search_terms": ["instagram reels", "reels trending", "ig"],
        "audience": "instagram users",
        "style": "aesthetic",
    },
    # How-To/Tutorial (15+)
    "howto": {
        "name": "How-To",
        "keywords": ["how to", "tutorial", "guide"],
        "search_terms": ["how to", "tutorial", "guide"],
        "audience": "learners",
        "style": "educational",
    },
    "diy": {
        "name": "DIY Projects",
        "keywords": ["diy", "craft", "make"],
        "search_terms": ["diy project", "craft tutorial", "how to make"],
        "audience": "crafters",
        "style": "hands-on",
    },
    "cooking": {
        "name": "Cooking & Recipes",
        "keywords": ["cooking", "recipe", "food"],
        "search_terms": ["cooking tutorial", "recipe", "easy meal"],
        "audience": "cooking enthusiasts",
        "style": "instructional",
    },
    "makeup_tutorial": {
        "name": "Makeup Tutorials",
        "keywords": ["makeup", "beauty", "tutorial"],
        "search_terms": ["makeup tutorial", "beauty tips", "how to apply"],
        "audience": "beauty enthusiasts",
        "style": "beauty",
    },
}


class CategoryDetector:
    """Detects content category using LLM"""

    def __init__(self, groq_api_key: str = ""):
        self.groq_api_key = groq_api_key
        self.categories = CONTENT_CATEGORIES

    async def detect_category(
        self, video_title: str, video_description: str = ""
    ) -> dict[str, Any]:
        """Detect which category a video belongs to"""

        import httpx

        # Build context
        text = f"{video_title}. {video_description}"

        # Get category list
        category_list = list(self.categories.keys())

        prompt = f"""Detect the content category for this video.

Video: {text}

Categories: {category_list}

Return JSON:
{{"category": "primary category", "confidence": 0.0-1.0, "sub_categories": [], "reasoning": "brief explanation"}}"""

        if not self.groq_api_key:
            return self._simple_detect(video_title, video_description)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 200,
                        "response_format": {"type": "json_object"},
                    },
                )

                if resp.status_code == 200:
                    result = json.loads(resp.json()["choices"][0]["message"]["content"])
                    category = result.get("category", "")

                    if category in self.categories:
                        return {
                            "category": category,
                            "category_data": self.categories[category],
                            "confidence": result.get("confidence", 0.8),
                            "reasoning": result.get("reasoning", "LLM detected"),
                        }
        except Exception:
            pass

        return self._simple_detect(video_title, video_description)

    def _simple_detect(self, title: str, description: str) -> dict[str, Any]:
        """Simple keyword-based detection"""

        text = f"{title} {description}".lower()

        for cat_key, cat_data in self.categories.items():
            keywords = cat_data.get("keywords", [])

            for keyword in keywords:
                if keyword.lower() in text:
                    return {
                        "category": cat_key,
                        "category_data": cat_data,
                        "confidence": 0.7,
                        "reasoning": f"Matched keyword: {keyword}",
                    }

        # Default
        return {
            "category": "other",
            "category_data": {"name": "Other", "style": "general"},
            "confidence": 0.3,
            "reasoning": "No match found",
        }

    def get_search_terms(self, category: str) -> list[str]:
        """Get search terms for a category"""

        if category in self.categories:
            return self.categories[category].get("search_terms", [])

        return []

    def list_all_categories(self) -> list[str]:
        """list all available categories"""
        return list(self.categories.keys())


# Standalone function for detection
async def detect_video_category(
    title: str, description: str = "", api_key: str = ""
) -> dict[str, Any]:
    """Detect video category - standalone function"""

    detector = CategoryDetector(groq_api_key=api_key)
    return await detector.detect_category(title, description)


# Get all categories
def get_content_categories() -> dict[str, dict]:
    """Get all content categories"""
    return CONTENT_CATEGORIES


if __name__ == "__main__":
    # Test
    import asyncio

    async def test():
        detector = CategoryDetector()

        # Test detection
        test_videos = [
            ("10 AI Tools That Will Change Everything", "Review of best AI tools"),
            ("Top 10 Viral TikToks This Week", "Funniest moments compilation"),
            ("Bedtime Story for Kids - The Moon", "Sleepy story time"),
            (
                "UFO Sighting in New York - Real Footage",
                "Documentary-style investigation",
            ),
        ]

        for title, desc in test_videos:
            result = await detector.detect_category(title, desc)
            print(f"\n{title}")
            print(f"  → {result['category']} ({result['confidence']:.0%})")
            print(f"  → {result['reasoning']}")

        print(f"\nTotal categories: {len(detector.list_all_categories())}")

    asyncio.run(test())
