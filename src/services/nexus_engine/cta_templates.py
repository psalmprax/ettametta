from typing import Optional, Dict

class CTATemplate:
    def __init__(self, id: str, default_text: str, duration_seconds: int):
        self.id = id
        self.default_text = default_text
        self.duration_seconds = duration_seconds

    def get_default_text(self) -> str:
        return self.default_text

# Define the templates
CTA_TEMPLATES: Dict[str, CTATemplate] = {
    "standard_subscribe": CTATemplate(
        id="standard_subscribe",
        default_text="Subscribe to the channel for more updates!",
        duration_seconds=5
    ),
    "limited_offer": CTATemplate(
        id="limited_offer",
        default_text="Limited time offer! Click the link below to get started.",
        duration_seconds=6
    ),
    "join_community": CTATemplate(
        id="join_community",
        default_text="Join our community on Discord. Link in description.",
        duration_seconds=5
    ),
    "watch_more": CTATemplate(
        id="watch_more",
        default_text="Watch the next video to learn more secrets.",
        duration_seconds=5
    )
}

def get_cta_template(template_id: str) -> Optional[CTATemplate]:
    if not template_id:
        return None
    return CTA_TEMPLATES.get(template_id)
