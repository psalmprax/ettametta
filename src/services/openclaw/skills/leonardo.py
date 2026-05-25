from .playwright_video_skill import PlaywrightVideoSkill

leonardo_skill = type("LeonardoSkill", (PlaywrightVideoSkill,), {
    "engine_name": "leonardo",
    "base_url": "https://leonardo.ai",
    "wait_timeout_ms": 60000,
    "create_path": "/platform/ai-video",
    "button_names": ["Generate", "Create"],
})()
