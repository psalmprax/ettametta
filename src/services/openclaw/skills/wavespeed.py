from .playwright_video_skill import PlaywrightVideoSkill

wavespeed_skill = type("WaveSpeedAISkill", (PlaywrightVideoSkill,), {
    "engine_name": "wavespeed",
    "base_url": "https://wavespeed.ai",
    "wait_timeout_ms": 60000,
    "create_path": "/studio",
    "button_names": ["Generate", "Create"],
})()
