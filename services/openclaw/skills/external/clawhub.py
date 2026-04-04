import requests
import logging
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

CLAWHUB_SKILLS_REPO = "https://api.github.com/repos/openclaw/skills/contents/skills"


class ClawHubSkillLoader:
    """
    Load skills from ClawHub GitHub repository.
    https://github.com/openclaw/skills
    """

    def __init__(self, cache_dir: str = "/tmp/clawhub_skills"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {"User-Agent": "viral_forge/1.0"}

    def list_categories(self) -> List[str]:
        """Get list of skill categories from the repo."""
        try:
            response = requests.get(
                CLAWHUB_SKILLS_REPO, headers=self.headers, timeout=30
            )
            if response.status_code == 200:
                contents = response.json()
                return [item["name"] for item in contents if item["type"] == "dir"]
            return []
        except Exception as e:
            logger.error(f"Error listing categories: {e}")
            return []

    def list_skills_in_category(self, category: str) -> List[Dict]:
        """List skills in a specific category."""
        try:
            url = f"{CLAWHUB_SKILLS_REPO}/{category}"
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                contents = response.json()
                return [
                    {"name": item["name"], "path": item["path"], "url": item["url"]}
                    for item in contents
                    if item["type"] == "dir"
                ]
            return []
        except Exception as e:
            logger.error(f"Error listing skills in {category}: {e}")
            return []

    def get_skill_details(self, skill_path: str) -> Optional[Dict]:
        """Get skill details (SKILL.md content)."""
        try:
            url = f"https://api.github.com/repos/openclaw/skills/contents/{skill_path}"
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                contents = response.json()
                skill_info = {"files": [], "name": skill_path.split("/")[-1]}

                for item in contents:
                    if item["name"] == "SKILL.md":
                        # Get SKILL.md content
                        md_response = requests.get(item["download_url"], timeout=30)
                        if md_response.status_code == 200:
                            skill_info["description"] = md_response.text[:500]
                    skill_info["files"].append(item["name"])

                return skill_info
            return None
        except Exception as e:
            logger.error(f"Error getting skill details for {skill_path}: {e}")
            return None

    def search_skills(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search skills by query."""
        results = []
        categories = [category] if category else self.list_categories()

        for cat in categories[:10]:  # Limit to avoid rate limits
            skills = self.list_skills_in_category(cat)
            for skill in skills:
                if query.lower() in skill["name"].lower():
                    skill["category"] = cat
                    results.append(skill)

        return results[:20]

    def get_skill_by_name(self, author: str, name: str) -> Optional[Dict]:
        """Get a specific skill by author/name."""
        try:
            path = f"skills/{author}/{name}"
            return self.get_skill_details(path)
        except Exception as e:
            logger.error(f"Error getting skill {author}/{name}: {e}")
            return None


class PopularSkills:
    """
    Pre-configured popular skills relevant to viral_forge.
    """

    SKILLS = {
        "affiliate_master": {
            "author": "michael-laffin",
            "name": "affiliate-master",
            "description": "Full-stack affiliate marketing automation with FTC-compliant disclosures",
            "category": "Marketing & Sales",
            "api_required": ["Amazon Associates"],  # Optional, can work without
            "priority": "high",
        },
        "social_media_agent": {
            "author": "lobehub",
            "name": "openclaw-skills-social-media-agent",
            "description": "Autonomous social media management for X/Twitter",
            "category": "Communication",
            "api_required": [],
            "priority": "high",
        },
        "github_trending": {
            "author": "zanblayde",
            "name": "agent-commons",
            "description": "GitHub automation and research tools",
            "category": "Git & GitHub",
            "api_required": [],
            "priority": "medium",
        },
        "research": {
            "author": "rogersuperbuilderalpha",
            "name": "academic-research",
            "description": "Academic paper search using OpenAlex API (free)",
            "category": "Search & Research",
            "api_required": [],
            "priority": "high",
        },
        "browser_automation": {
            "author": "thesethrose",
            "name": "agent-browser",
            "description": "Rust-based headless browser automation",
            "category": "Browser & Automation",
            "api_required": [],
            "priority": "medium",
        },
        "rss_ingestion": {
            "author": "seandong",
            "name": "ak-rss-24h-brief",
            "description": "RSS/Atom feed reader with Chinese categorization",
            "category": "Browser & Automation",
            "api_required": [],
            "priority": "medium",
        },
        "youtube_metrics": {
            "author": "dannyshmueli",
            "name": "agent-analytics",
            "description": "Simple website analytics your AI agent controls",
            "category": "Data & Analytics",
            "api_required": [],
            "priority": "medium",
        },
        "tiktok_b2b": {
            "author": "openclaw",
            "name": "tiktok-b2b-scripting",
            "description": "High-tier B2B viral script generation for technical niches",
            "category": "Marketing & Sales",
            "api_required": [],
            "priority": "high",
        },
        "b2c_marketing": {
            "author": "openclaw",
            "name": "b2c-marketing-automation",
            "description": "Consumer-focused engagement and account warm-up automation",
            "category": "Marketing & Sales",
            "api_required": [],
            "priority": "high",
        },
        "remotion_toolkit": {
            "author": "shreefentsar",
            "name": "remotion-video-toolkit",
            "description": "Programmatic React-based video editing and FFMPEG integration",
            "category": "Creative AI",
            "api_required": [],
            "priority": "high",
        },
        "science_pop": {
            "author": "claw4science",
            "name": "short-video-script-generator",
            "description": "Transforms technical/academic data into viral 'Science-Pop' scripts",
            "category": "Search & Research",
            "api_required": [],
            "priority": "high",
        },
    }

    @classmethod
    def get_skill(cls, key: str) -> Optional[Dict]:
        return cls.SKILLS.get(key)

    @classmethod
    def get_all_skills(cls) -> List[Dict]:
        return list(cls.SKILLS.values())

    @classmethod
    def get_skills_by_priority(cls, priority: str) -> List[Dict]:
        return [s for s in cls.SKILLS.values() if s.get("priority") == priority]


clawhub_loader = ClawHubSkillLoader()
popular_skills = PopularSkills()
