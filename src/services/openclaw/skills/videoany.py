from .playwright_video_skill import PlaywrightVideoSkill

videoany_skill = type("VideoAnySkill", (PlaywrightVideoSkill,), {
    "engine_name": "videoany",
    "base_url": "https://videoany.io",
    "wait_timeout_ms": 60000,
    "button_names": ["Generate", "Create"],
})()
