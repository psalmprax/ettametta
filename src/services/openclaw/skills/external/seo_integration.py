import os
import logging
import requests
import aiohttp
from typing import Any
from datetime import datetime
import random

logger = logging.getLogger(__name__)

YAHOO_FINANCE_ENABLED = True  # Free, no API key needed


class BlogSEOService:
    """
    Blog and SEO content generation service.
    Uses Groq (already configured) for content generation.
    """

    def __init__(self):
        self.api_url = os.getenv("API_URL", "http://localhost:8000")

    async def generate_seo_content(
        self, topic: str, content_type: str = "blog", word_count: int = 500
    ) -> dict[str, Any]:
        """
        Generate SEO-optimized content for a topic using Groq.

        Args:
            topic: The main topic/keyword
            content_type: Type of content (blog, product, review)
            word_count: Target word count

        Returns:
            dict with title, content, meta description, keywords
        """
        from src.api.config import settings

        keywords = self._generate_keywords(topic)
        title = self._generate_title(topic, content_type)
        meta_description = self._generate_meta_description(topic, word_count)

        # Use Groq for real content generation if available
        if settings.GROQ_API_KEY:
            try:
                from groq import AsyncGroq

                client = AsyncGroq(api_key=settings.GROQ_API_KEY)

                prompt = f"""Generate a {word_count}-word {content_type} article about {topic}.
Include the following SEO keywords: {", ".join(keywords)}.
Format as:
- Title: <title>
- Meta Description: <meta description under 160 chars>
- Content: <article body in markdown>
- Keywords: <comma-separated>"""

                response = await client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000,
                )

                content = response.choices[0].message.content

                # Parse structured response
                lines = content.split("\n")
                parsed = {
                    "title": title,
                    "meta_description": meta_description,
                    "keywords": keywords,
                    "content": content,
                }

                for line in lines:
                    if line.startswith("Title:"):
                        parsed["title"] = line.replace("Title:", "").strip()
                    elif line.startswith("Meta Description:"):
                        parsed["meta_description"] = line.replace(
                            "Meta Description:", ""
                        ).strip()[:160]
                    elif line.startswith("Keywords:"):
                        parsed["keywords"] = [
                            k.strip() for k in line.replace("Keywords:", "").split(",")
                        ]
                    elif line.startswith("Content:"):
                        parsed["content"] = content.split("Content:")[-1].strip()

                return {
                    "title": parsed["title"],
                    "content": parsed["content"],
                    "meta_description": parsed["meta_description"],
                    "keywords": parsed["keywords"],
                    "headings": self._generate_headings(topic),
                    "word_count": len(parsed["content"].split()),
                    "generated_at": datetime.now().isoformat(),
                    "ai_model": "groq-llama-3.3-70b",
                }
            except Exception as e:
                logger.warning(
                    f"Groq content generation failed: {e}, falling back to template"
                )

        # Fallback: Use structured template
        content = self._structure_content(topic, content_type, word_count)

        return {
            "title": title,
            "content": content,
            "meta_description": meta_description,
            "keywords": keywords,
            "headings": self._generate_headings(topic),
            "word_count": len(content.split()),
            "generated_at": datetime.now().isoformat(),
        }

    async def _generate_keywords(self, topic: str) -> list[str]:
        """Generate SEO keywords for topic."""
        base = topic.lower().strip()
        keywords = [
            base,
            f"best {base}",
            f"{base} guide",
            f"how to {base}",
            f"{base} tips",
            f"{base} tutorial",
            f"{base} review",
            f"top {base}",
        ]
        return keywords[:8]

    async def _generate_title(self, topic: str, content_type: str) -> str:
        """Generate SEO title."""
        templates = {
            "blog": [
                f"The Ultimate Guide to {topic.title()} in 2026",
                f"{topic.title()}: Everything You Need to Know",
                f"How to Master {topic.title()} - Complete Guide",
            ],
            "product": [
                f"Best {topic.title()} - Top Picks for 2026",
                f"{topic.title()} Review: Is It Worth It?",
            ],
            "review": [
                f"Honest {topic.title()} Review",
                f"{topic.title()} - Pros and Cons",
            ],
        }

        options = templates.get(content_type, templates["blog"])
        return random.choice(options)

    async def _generate_meta_description(self, topic: str, word_count: int) -> str:
        """Generate meta description (under 160 chars)."""
        templates = [
            f"Learn everything about {topic}. Complete guide with tips, tricks, and expert insights.",
            f"Discover how to {topic.lower()}. Step-by-step guide for beginners and experts alike.",
            f"Master {topic} with our comprehensive guide. Free tips and strategies inside!",
        ]

        desc = random.choice(templates)
        return desc[:158] + ".." if len(desc) > 160 else desc

    async def _structure_content(self, topic: str, content_type: str, word_count: int) -> str:
        """Generate structured content."""
        sections = [
            f"## Introduction\n\nWelcome to our complete guide on {topic}. In this article, we'll cover everything you need to know.",
            f"## What is {topic}?\n\nLet's start by understanding the basics of {topic} and why it matters.",
            f"## Key Benefits\n\nHere are the main benefits of understanding {topic}:\n- Benefit 1\n- Benefit 2\n- Benefit 3",
            f"## How to Get Started\n\nFollow these steps to begin:\n1. First step\n2. Second step\n3. Third step",
            f"## Common Mistakes to Avoid\n\nMany people make these errors when learning about {topic}. Don't be one of them!",
            f"## Conclusion\n\nNow you have a solid understanding of {topic}. Start implementing these tips today!",
        ]

        return "\n\n".join(sections[:4])

    async def _generate_headings(self, topic: str) -> list[str]:
        """Generate section headings."""
        return [
            f"What is {topic}?",
            f"Why {topic} Matters",
            f"Getting Started with {topic}",
            f"Best Practices",
            f"Common Questions",
        ]


blog_seo_service = BlogSEOService()
