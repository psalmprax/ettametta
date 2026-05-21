from .playwright_video_skill import PlaywrightVideoSkill

hailuo_skill = type("HailuoSkill", (PlaywrightVideoSkill,), {
    "engine_name": "hailuo",
    "base_url": "https://hailuoml.com",
    "wait_timeout_ms": 60000,
    "button_names": ["Generate", "Create"],
})()
