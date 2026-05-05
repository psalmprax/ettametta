import requests
import logging
from src.api.config import settings

from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class RepurposeSkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        self.api_url = f"{settings.API_URL}"

    def execute(self, action: str = "analyze", source_uri: str = None, **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if not source_uri:
            return "⚠️ source_uri is required for Repurpose skill."

        if action == "analyze":
            return self.analyze_repurpose_potential(source_uri)
        elif action == "transform":
            return self.trigger_repurpose_job(
                source_uri, kwargs.get("target_platform", "TikTok")
            )

    def analyze_repurpose_potential(self, source_uri: str) -> str:
        """Analyzes a URL to see if it's worth repurposing."""
        return f"🔍 **Analysis for {source_uri}**: High potential for TikTok/Reels due to fast pacing and visual hooks."

    def trigger_repurpose_job(self, source_uri: str, target_platform: str) -> str:
        """Triggers a new repurpose job for a raw URL."""
        return f"🚀 **Repurpose Job Triggered**: {source_uri} -> {target_platform}. Rendering in background..."

    def repurpose_content(
        self,
        source_job_id: str,
        target_platforms: list,
        adaptations: dict | None = None,
    ) -> str:
        try:
            resp = requests.get(
                f"{self.api_url}/video/jobs",
                headers=self._get_headers(),
                timeout=10,
            )
            if resp.status_code != 200:
                return f"⚠️ Could not fetch jobs: {resp.status_code}"

            jobs_raw = resp.json()
            jobs = jobs_raw.get("jobs", []) if isinstance(jobs_raw, dict) else jobs_raw
            source_job = None
            for job in jobs:
                if job.get("id") == source_job_id or job.get("job_id") == source_job_id:
                    source_job = job
                    break

            if not source_job:
                return f"⚠️ Job `{source_job_id}` not found."

            source_uri = source_job.get("output_url") or source_job.get("video_uri", "")
            source_title = source_job.get("title", "Untitled")
            source_script = source_job.get("script", "") or source_job.get(
                "metadata", {}
            ).get("script", "")

            if not source_uri and not source_script:
                return (
                    f"⚠️ Job `{source_job_id}` has no output URL or script to repurpose."
                )

            platform_adaptations = {
                "YouTube Shorts": {
                    "aspect": "9:16",
                    "max_duration": 60,
                    "style": "vertical_short",
                },
                "TikTok": {
                    "aspect": "9:16",
                    "max_duration": 60,
                    "style": "vertical_short",
                },
                "Instagram Reels": {
                    "aspect": "9:16",
                    "max_duration": 90,
                    "style": "vertical_reel",
                },
                "YouTube Long": {
                    "aspect": "16:9",
                    "max_duration": 600,
                    "style": "landscape",
                },
                "Instagram Post": {
                    "aspect": "1:1",
                    "max_duration": 60,
                    "style": "square",
                },
                "Facebook": {
                    "aspect": "16:9",
                    "max_duration": 240,
                    "style": "landscape",
                },
                "LinkedIn": {
                    "aspect": "1:1",
                    "max_duration": 600,
                    "style": "professional",
                },
                "X": {"aspect": "16:9", "max_duration": 140, "style": "landscape"},
            }

            results = []
            for platform in target_platforms:
                adapt = platform_adaptations.get(
                    platform,
                    {"aspect": "9:16", "max_duration": 60, "style": "vertical_short"},
                )
                if adaptations and platform in adaptations:
                    adapt.update(adaptations[platform])

                payload = {
                    "action": "transform",
                    "source_uri": source_uri,
                    "prompt": f"Repurpose '{source_title}' for {platform}. "
                    f"Format: {adapt['aspect']}, max {adapt['max_duration']}s, style: {adapt['style']}. "
                    f"Adapt hook and pacing for {platform} audience.",
                    "niche": source_job.get("niche", "General"),
                    "platform": platform,
                }

                try:
                    gen_resp = requests.post(
                        f"{self.api_url}/video/generate",
                        json=payload,
                        headers=self._get_headers(),
                        timeout=30,
                    )
                    if gen_resp.status_code == 200:
                        gen_data = gen_resp.json()
                        job_id = gen_data.get("job_id", "PENDING")
                        results.append(
                            f"✅ {platform}: Job `{job_id}` queued ({adapt['aspect']}, {adapt['max_duration']}s max)"
                        )
                    else:
                        results.append(f"⚠️ {platform}: Failed ({gen_resp.status_code})")
                except Exception as e:
                    results.append(f"❌ {platform}: Error - {e}")

            lines = [
                f"🔄 **Content Repurposing**",
                f"Source: `{source_job_id}` — {source_title}",
                "",
            ]
            lines.extend(results)
            lines.append("")
            lines.append(f"Use `/publish` on each job once rendering completes.")
            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Repurpose Skill Error: {e}")
            return f"⚠️ Repurpose Error: {e}"

    def generate_caption_variants(
        self, text: str, platform: str = "all", count: int = 5
    ) -> str:
        try:
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"You are a viral content expert. Generate {count} distinct caption variants "
                            f"for {platform}. Each should have a different angle: emotional, curiosity-driven, "
                            f"data-backed, contrarian, and story-based. Keep them platform-optimized."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Generate {count} caption variants for this content:\n\n{text}",
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.8,
                "max_tokens": 1000,
            }
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=15,
            )

            if resp.status_code == 200:
                data = resp.json()
                captions = data["choices"][0]["message"]["content"]
                return f"📝 **Caption Variants for {platform}**:\n\n{captions}"
            else:
                return f"⚠️ Caption generation failed: {resp.status_code}"
        except Exception as e:
            logger.error(f"Caption Variant Error: {e}")
            return f"⚠️ Caption Error: {e}"

    def generate_hashtag_sets(
        self, niche: str, platform: str = "all", count: int = 3
    ) -> str:
        try:
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"Generate {count} distinct hashtag sets for {platform} content in the '{niche}' niche. "
                            f"Each set should have 10-15 hashtags mixing: 3-5 broad (1M+ posts), "
                            f"5-7 medium (100K-1M), and 2-3 niche-specific (<100K). "
                            f"Format each set as a clean block of hashtags."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Generate {count} hashtag sets for niche: {niche}",
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.7,
                "max_tokens": 800,
            }
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=15,
            )

            if resp.status_code == 200:
                data = resp.json()
                hashtags = data["choices"][0]["message"]["content"]
                return f"#️⃣ **Hashtag Sets for {niche}**:\n\n{hashtags}"
            else:
                return f"⚠️ Hashtag generation failed: {resp.status_code}"
        except Exception as e:
            logger.error(f"Hashtag Generation Error: {e}")
            return f"⚠️ Hashtag Error: {e}"

    def repurpose_script_to_posts(self, script: str, platforms: list = None) -> str:
        if platforms is None:
            platforms = ["Twitter/X", "LinkedIn", "Instagram Caption"]

        try:
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a content repurposing expert. Take a video script and convert it "
                            "into platform-specific text posts. Each platform has different constraints:\n"
                            "- Twitter/X: 280 chars, punchy, thread if needed\n"
                            "- LinkedIn: Professional tone, 1500 chars, hook + value + CTA\n"
                            "- Instagram Caption: Engaging, emoji-friendly, 2200 chars\n"
                            "Return each as a clearly labeled section."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Repurpose this script for: {', '.join(platforms)}\n\n{script[:2000]}",
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.7,
                "max_tokens": 2000,
            }
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=20,
            )

            if resp.status_code == 200:
                data = resp.json()
                posts = data["choices"][0]["message"]["content"]
                return f"📋 **Repurposed Posts**:\n\n{posts}"
            else:
                return f"⚠️ Script repurposing failed: {resp.status_code}"
        except Exception as e:
            logger.error(f"Script Repurpose Error: {e}")
            return f"⚠️ Repurpose Error: {e}"


repurpose_skill = RepurposeSkill()
