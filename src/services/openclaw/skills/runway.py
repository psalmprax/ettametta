from .playwright_video_skill import PlaywrightVideoSkill

runway_skill = type("RunwaySkill", (PlaywrightVideoSkill,), {
    "engine_name": "runway",
    "base_url": "https://runwayml.com",
    "wait_timeout_ms": 60000,
    "button_names": ["Generate", "Create"],
})()
