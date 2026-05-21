from .playwright_video_skill import PlaywrightVideoSkill

ltx_skill = type("LTXStudioSkill", (PlaywrightVideoSkill,), {
    "engine_name": "ltx",
    "base_url": "https://ltx.ai",
    "wait_timeout_ms": 60000,
    "create_path": "/studio",
    "button_names": ["Generate", "Create"],
})()
