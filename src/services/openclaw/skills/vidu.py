from .playwright_video_skill import PlaywrightVideoSkill

vidu_skill = type("ViduSkill", (PlaywrightVideoSkill,), {
    "engine_name": "vidu",
    "base_url": "https://vidu.ai",
    "wait_timeout_ms": 60000,
    "button_names": ["Generate", "Create"],
})()
