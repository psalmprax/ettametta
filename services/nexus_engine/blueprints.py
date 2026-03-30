from typing import List, Dict

BLUEPRINTS = [
    {
        "id": "viral-reskin",
        "name": "Viral Re-skinner",
        "description": "Auto-discovery of high-velocity clips with neural style injection.",
        "nodes": [
            {"type": "ingress", "label": "Deep Discovery", "desc": "Scanning TikTok clusters for niche alpha."},
            {"type": "cognition", "label": "Viral DNA Match", "desc": "Llama-3 analysis of hook retention."},
            {"type": "synthesis", "label": "Neural Remix", "desc": "Applying cinematic overlays and speed ramping."},
            {"type": "egress", "label": "Global Sync", "desc": "Scheduled dispatch to all social hubs."}
        ]
    },
    {
        "id": "story-factory",
        "name": "Storytelling Engine",
        "description": "Script-to-video autonomous workflow for long-form quality.",
        "nodes": [
            {"type": "ingress", "label": "Script Pulse", "desc": "Generating high-retention narrative scripts."},
            {"type": "cognition", "label": "Vibe Mapping", "desc": "Mapping visual prompts to emotional peaks."},
            {"type": "synthesis", "label": "Nexus Assembly", "desc": "Synthesizing voiceover, music, and stock visuals."},
            {"type": "egress", "label": "HDP Publish", "desc": "High-definition export and cloud archiving."}
        ]
    }
]

def get_blueprints() -> List[Dict]:
    return BLUEPRINTS

def get_blueprint_by_id(blueprint_id: str) -> Dict:
    return next((bp for bp in BLUEPRINTS if bp["id"] == blueprint_id), BLUEPRINTS[0])
