from .playwright_video_skill import PlaywrightVideoSkill

heygen_skill = type("HeyGenSkill", (PlaywrightVideoSkill,), {
    "engine_name": "heygen",
    "base_url": "https://heygen.com",
    "wait_timeout_ms": 60000,
    "create_path": "/ai-video generator",
    "button_names": ["Generate", "Create"],
})()
