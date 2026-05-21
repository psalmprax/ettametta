from .playwright_video_skill import PlaywrightVideoSkill

seedance_skill = type("SeedanceSkill", (PlaywrightVideoSkill,), {
    "engine_name": "seedance",
    "base_url": "https://seedance.ai",
    "wait_timeout_ms": 60000,
    "button_names": ["Generate", "Create"],
})()
