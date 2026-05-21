from .playwright_video_skill import PlaywrightVideoSkill

fliki_skill = type("FlikiSkill", (PlaywrightVideoSkill,), {
    "engine_name": "fliki",
    "base_url": "https://fliki.ai",
    "wait_timeout_ms": 30000,
    "create_path": "/new",
    "button_names": ["Generate", "Create", "Video"],
})()
