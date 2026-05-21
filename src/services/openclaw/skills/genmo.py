from .playwright_video_skill import PlaywrightVideoSkill

genmo_skill = type("GenmoSkill", (PlaywrightVideoSkill,), {
    "engine_name": "genmo",
    "base_url": "https://genmo.ai",
    "wait_timeout_ms": 45000,
    "button_names": ["Generate", "Create", "Video"],
})()
