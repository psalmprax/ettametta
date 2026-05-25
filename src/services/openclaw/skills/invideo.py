from .playwright_video_skill import PlaywrightVideoSkill

invideo_skill = type("InVideoAISkill", (PlaywrightVideoSkill,), {
    "engine_name": "invideo",
    "base_url": "https://invideo.io",
    "wait_timeout_ms": 30000,
    "create_path": "/video-generator",
    "button_names": ["Generate", "Create", "AI"],
})()
