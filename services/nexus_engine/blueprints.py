from typing import List, Dict

BLUEPRINTS = [
    {
        "id": "viral-reskin",
        "name": "Viral Re-skinner",
        "description": "Auto-discovery of high-velocity clips with neural style injection.",
        "nodes": [
            {
                "type": "ingress",
                "label": "Deep Discovery",
                "desc": "Scanning TikTok clusters for niche alpha.",
            },
            {
                "type": "cognition",
                "label": "Viral DNA Match",
                "desc": "Llama-3 analysis of hook retention.",
            },
            {
                "type": "synthesis",
                "label": "Neural Remix",
                "desc": "Applying cinematic overlays and speed ramping.",
            },
            {
                "type": "egress",
                "label": "Global Sync",
                "desc": "Scheduled dispatch to all social hubs.",
            },
        ],
    },
    {
        "id": "story-factory",
        "name": "Storytelling Engine",
        "description": "Script-to-video autonomous workflow for long-form quality.",
        "nodes": [
            {
                "type": "ingress",
                "label": "Script Pulse",
                "desc": "Generating high-retention narrative scripts.",
            },
            {
                "type": "cognition",
                "label": "Vibe Mapping",
                "desc": "Mapping visual prompts to emotional peaks.",
            },
            {
                "type": "synthesis",
                "label": "Nexus Assembly",
                "desc": "Synthesizing voiceover, music, and stock visuals.",
            },
            {
                "type": "egress",
                "label": "HDP Publish",
                "desc": "High-definition export and cloud archiving.",
            },
        ],
    },
    {
        "id": "documentary-style",
        "name": "Docu-Style Narrative",
        "description": "Creates documentary-style videos with dramatic narration and archival footage.",
        "nodes": [
            {
                "type": "ingress",
                "label": "Research Core",
                "desc": "Gathering factual background and archive material.",
            },
            {
                "type": "cognition",
                "label": "Narrative Arc",
                "desc": "Structuring story with exposition, climax, resolution.",
            },
            {
                "type": "synthesis",
                "label": "Cinematic Cut",
                "desc": "Editing with dramatic pacing, color grading, lower-thirds.",
            },
            {
                "type": "egress",
                "label": "Prestige Publish",
                "desc": "Upload in premium 4K with metadata.",
            },
        ],
    },
    {
        "id": "tutorial-flow",
        "name": "Tutorial Flow",
        "description": "Educational step-by-step tutorials with clear visuals and voiceover.",
        "nodes": [
            {
                "type": "ingress",
                "label": "Lesson Planner",
                "desc": "Break topic into logical steps and key points.",
            },
            {
                "type": "cognition",
                "label": "Visual Mapping",
                "desc": "Match each step with appropriate screen recordings or stock visuals.",
            },
            {
                "type": "synthesis",
                "label": "Demo Assembly",
                "desc": "Combine voiceover, cursor highlights, and zooms.",
            },
            {
                "type": "egress",
                "label": "Knowledge Drop",
                "desc": "Export with chapter markers and description links.",
            },
        ],
    },
    {
        "id": "promo-ad",
        "name": "High-Energy Promo",
        "description": "Fast-paced promotional ad with punchy hooks and call-to-action.",
        "nodes": [
            {
                "type": "ingress",
                "label": "Hook Generator",
                "desc": "Craft 3-second attention-grabbing opener.",
            },
            {
                "type": "cognition",
                "label": "Pain Point Amplify",
                "desc": "Identify audience pain and amplify urgency.",
            },
            {
                "type": "synthesis",
                "label": "Flash Editing",
                "desc": "Rapid cuts, zooms, text pop-ups, sound stings.",
            },
            {
                "type": "egress",
                "label": "Conversion Push",
                "desc": "Add CTA overlays and track clicks.",
            },
        ],
    },
]


def get_blueprints() -> List[Dict]:
    return BLUEPRINTS


def get_blueprint_by_id(blueprint_id: str) -> Dict:
    return next((bp for bp in BLUEPRINTS if bp["id"] == blueprint_id), BLUEPRINTS[0])
