from .playwright_video_skill import PlaywrightVideoSkill

morph_skill = type("MorphStudioSkill", (PlaywrightVideoSkill,), {
    "engine_name": "morph",
    "base_url": "https://morphstudio.com",
    "wait_timeout_ms": 45000,
    "button_names": ["Generate", "Create", "Video"],
})()
