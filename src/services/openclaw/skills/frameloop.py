from .playwright_video_skill import PlaywrightVideoSkill

frameloop_skill = type("FrameloopSkill", (PlaywrightVideoSkill,), {
    "engine_name": "frameloop",
    "base_url": "https://frameloop.ai",
    "wait_timeout_ms": 60000,
    "button_names": ["Generate", "Create"],
})()
