from .playwright_video_skill import PlaywrightVideoSkill

pika_skill = type("PikaSkill", (PlaywrightVideoSkill,), {
    "engine_name": "pika",
    "base_url": "https://pika.art",
    "wait_timeout_ms": 45000,
    "button_names": ["Generate", "Create"],
})()
