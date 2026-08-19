"""
Traffic Driver — Automated Marketing Content Generation

Creates social posts, SEO content, and email sequences
to drive traffic to product listings.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/revenue_engine/traffic")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SocialPost:
    platform: str
    content: str
    hashtags: list[str] = field(default_factory=list)
    url: str = ""
    scheduled_time: str = ""
    status: str = "draft"


@dataclass
class EmailSequence:
    name: str
    emails: list[dict] = field(default_factory=list)
    trigger: str = "signup"


@dataclass
class SEOArticle:
    title: str
    content: str
    keywords: list[str] = field(default_factory=list)
    meta_description: str = ""
    word_count: int = 0


class TrafficDriver:
    """Generates marketing content for product promotion."""

    def generate_social_posts(
        self, product_name: str, niche: str, url: str = "", count: int = 10
    ) -> list[SocialPost]:
        """Generate social media posts for a product."""
        posts = []
        templates = [
            "🎯 Just launched: {product}\n\nStop wasting hours on {niche}.\n\nThis template pack gives you professional, ready-to-use designs in minutes.\n\n{url}\n\n#digitaldownload #template",
            "⚡ {product} is live!\n\nPerfect for {niche} professionals who want to save time.\n\nInstant download. Editable. Ready to use.\n\n{url}\n\n#etsyseller #digitalproduct",
            "🔥 New release: {product}\n\nThe fastest way to create professional {niche} materials.\n\n✅ Editable\n✅ Instant download\n✅ Works with free tools\n\n{url}\n\n#smallbusiness",
            "💡 Want better {niche} materials?\n\nCheck out {product} — professional templates ready in minutes.\n\n{url}\n\n#template #productivity",
            "🚀 {product} just dropped!\n\nFor anyone who needs great {niche} materials without the hassle.\n\n{url}\n\n#newproduct #digital",
            "✨ {product}\n\nProfessional {niche} templates.\nInstant download.\nFully editable.\n\nGrab yours: {url}\n\n#canva #template",
            "📦 What's inside {product}:\n- 50+ professional templates\n- Fully customizable\n- Works with Canva\n\nPerfect for {niche}.\n\n{url}\n\n#digitaldownload",
            "⏰ Limited time: {product}\n\nEverything you need for {niche} in one pack.\n\n{url}\n\n#sale #template",
            "🎯 {product}\n\nJoin 100+ {niche} pros using these templates.\n\nSave hours every week.\n\n{url}\n\n#productivity #business",
            "💡 Pro tip: Use {product} to create stunning {niche} materials in minutes.\n\n{url}\n\n#pro #template",
        ]

        for i, template in enumerate(templates[:count]):
            post = SocialPost(
                platform=["x", "linkedin", "facebook", "instagram"][i % 4],
                content=template.format(product=product_name, niche=niche, url=url),
                hashtags=[f"#{w}" for w in niche.split()[:3]] + ["#digitaldownload"],
                url=url,
            )
            posts.append(post)

        return posts

    def generate_email_sequence(
        self, product_name: str, niche: str, url: str = ""
    ) -> EmailSequence:
        """Generate an automated email sequence."""
        emails = [
            {
                "subject": f"Your {product_name} is ready!",
                "body": f"Thanks for your interest in {product_name}.\n\n"
                f"Your download is ready: {url}\n\n"
                f"Quick tips to get started:\n"
                f"1. Download the files\n"
                f"2. Open in Canva (free)\n"
                f"3. Customize to your brand\n"
                f"4. Use immediately\n\n"
                f"Need help? Reply to this email.",
                "delay_days": 0,
            },
            {
                "subject": f"Pro tips for {niche}",
                "body": f"Here are 3 ways to get more from your {product_name}:\n\n"
                f"1. Customize colors to match your brand\n"
                f"2. Add your logo for a professional look\n"
                f"3. Save as templates for reuse\n\n"
                f"Want more templates? Check out our other products.",
                "delay_days": 3,
            },
            {
                "subject": f"Need more {niche} templates?",
                "body": f"We have more products that pair perfectly with {product_name}.\n\n"
                f"Check out our full collection and save 20% with code WELCOME20.\n\n"
                f"Thanks for being a customer!",
                "delay_days": 7,
            },
        ]

        return EmailSequence(
            name=f"{product_name} sequence",
            emails=emails,
            trigger="purchase",
        )

    def generate_seo_article(
        self, niche: str, product_name: str, url: str = ""
    ) -> SEOArticle:
        """Generate an SEO article to drive organic traffic."""
        title = f"Best {niche.title()} Templates in 2026"
        keywords = [niche, f"{niche} template", f"best {niche}", f"{niche} download"]

        content = (
            f"# {title}\n\n"
            f"Looking for the best {niche} templates? You're in the right place.\n\n"
            f"## Why Use {niche.title()} Templates?\n\n"
            f"Creating {niche} materials from scratch takes hours. "
            f"Professional templates save you time while looking polished.\n\n"
            f"## Top Pick: {product_name}\n\n"
            f"After reviewing dozens of options, {product_name} stands out for:\n\n"
            f"- Professional design quality\n"
            f"- Easy customization (works with free tools)\n"
            f"- Instant download and setup\n"
            f"- Great value for the price\n\n"
            f"## What's Included\n\n"
            f"- 50+ editable templates\n"
            f"- Step-by-step instructions\n"
            f"- Bonus tips and tricks\n\n"
            f"## Get Started\n\n"
            f"Ready to upgrade your {niche} materials?\n\n"
            f"[Get {product_name} here]({url})\n\n"
            f"## FAQ\n\n"
            f"**Do I need paid software?** No — works with free Canva.\n"
            f"**Can I customize them?** Yes — fully editable.\n"
            f"**How soon can I use them?** Instantly after download.\n"
        )

        meta = f"Discover the best {niche} templates for 2026. Professional, editable, and instant download."

        return SEOArticle(
            title=title,
            content=content,
            keywords=keywords,
            meta_description=meta,
            word_count=len(content.split()),
        )

    def save_content(self, posts: list[SocialPost], product_name: str) -> Path:
        """Save generated content."""
        product_dir = DATA_DIR / product_name.lower().replace(" ", "_")
        product_dir.mkdir(exist_ok=True)

        posts_file = product_dir / "social_posts.json"
        posts_file.write_text(json.dumps([asdict(p) for p in posts], indent=2))

        logger.info(f"Saved {len(posts)} posts to {posts_file}")
        return product_dir
