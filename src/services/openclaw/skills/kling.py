from .playwright_video_skill import PlaywrightVideoSkill

kling_skill = type("KlingSkill", (PlaywrightVideoSkill,), {
    "engine_name": "kling",
    "base_url": "https://kling.ai",
    "wait_timeout_ms": 60000,
    "button_names": ["Generate", "Create", "AI"],
})()
