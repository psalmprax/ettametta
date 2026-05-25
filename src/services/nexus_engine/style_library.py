from enum import Enum
from typing import Dict, Any

class NexusStyle(Enum):
    CINEMATIC_DOC = "CINEMATIC_DOC"
    VOX_EXPLAINER = "VOX_EXPLAINER"
    DEEP_DIVE = "DEEP_DIVE"
    PERSONA_MONTAGE = "PERSONA_MONTAGE"
    REDDIT_STORY = "REDDIT_STORY"
    FAST_HYPE = "FAST_HYPE"
    NOIR_MYSTERY = "NOIR_MYSTERY"
    INVESTIGATION = "INVESTIGATION"
    RETRO_ARCHIVE = "RETRO_ARCHIVE"
    BROADCAST_NEWS = "BROADCAST_NEWS"
    TOP_LISTICLE = "TOP_LISTICLE"
    MOTIVATIONAL = "MOTIVATIONAL"
    PRODUCT_SHOWCASE = "PRODUCT_SHOWCASE"
    REACTION_COMMENTARY = "REACTION_COMMENTARY"
    HORROR_CREEPY = "HORROR_CREEPY"
    LOFI_CHILL = "LOFI_CHILL"
    PODCAST_SIM = "PODCAST_SIM"
    CULINARY_MASTERCLASS = "CULINARY_MASTERCLASS"
    ULTIMATE_TUTORIAL = "ULTIMATE_TUTORIAL"
    HEARTFELT_NARRATIVE = "HEARTFELT_NARRATIVE"
    STOIC_WISDOM = "STOIC_WISDOM"
    RELATIONSHIP_DRAMA = "RELATIONSHIP_DRAMA"
    TRAVEL_VLOG = "TRAVEL_VLOG"
    FITNESS_MOTIVATION = "FITNESS_MOTIVATION"
    GAMING_LORE = "GAMING_LORE"
    ESPORTS_HYPE = "ESPORTS_HYPE"

STYLE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "ULTIMATE_TUTORIAL": {
        "name": "Ultimate Tutorial (How-To)",
        "description": "Clear, instructional, and structured step-by-step guides for any topic.",
        "prompt_modifier": "Structure: Divide the content into clear, numbered 'Steps'. Tone: Instructional, patient, and encouraging. Use phrases like 'Now, let's move to step X' or 'This is crucial because...'.",
        "visual_keywords": "educational graphics, step-by-step instructions, clear demonstration, overhead view, workshop environment",
        "music_keywords": "lofi study, productive, upbeat corporate, clean rhythmic",
        "voice_id": "fln_serena_educational",
        "remotion_flags": {"show_step_numbers": True, "layout": "instructional", "show_progress_bar": True}
    },
    "CULINARY_MASTERCLASS": {
        "name": "Culinary Masterclass",
        "description": "Vibrant, high-energy cooking tutorials with split-screen prep and reaction.",
        "prompt_modifier": "Tone: Enthusiastic, clear, and sensory-focused. Describe textures, smells, and colors (e.g., the rich red of the palm oil, the aroma of ground egusi).",
        "visual_keywords": "food prep, close-up cooking, steaming pot, vibrant spices, fresh ingredients, kitchen action",
        "music_keywords": "afrobeats, highlife, vibrant acoustic, upbeat percussion",
        "voice_id": "fln_brian_culinary",
        "remotion_flags": {"layout": "split_screen", "vfx": "vibrant_bloom", "show_ingredients": True}
    },
    "CINEMATIC_DOC": {
        "name": "Cinematic Documentary",
        "description": "High-fidelity, polished narrative documentaries.",
        "prompt_modifier": "Tone: Professional, cinematic, and educational. Use sophisticated vocabulary. IMPORTANT: Each segment MUST describe a UNIQUE visual scene. Do NOT repeat visual descriptions. Cycle through different perspectives: wide landscape, close-up detail, historical context, and modern application.",
        "visual_keywords": "cinematic, high-quality, 1080p, professional photography, diverse scenery",
        "music_keywords": "cinematic orchestral, inspiring, hybrid orchestral, dramatic",
        "voice_id": "fln_marcus_narrator",
        "remotion_flags": {"show_headline": True, "vfx": "default"}
    },
    "VOX_EXPLAINER": {
        "name": "Vox-Style Explainer",
        "description": "Fast-paced, minimalist, analytical with heavy data overlays.",
        "prompt_modifier": "Tone: Analytical, objective, and clear. Break down complex topics into simple steps.",
        "visual_keywords": "minimalist animation, motion graphics, clean data visualization, abstract white background",
        "music_keywords": "corporate minimal, tech, clean electronic, rhythmic",
        "remotion_flags": {"layout": "split_screen", "show_data_overlays": True}
    },
    "DEEP_DIVE": {
        "name": "Deep-Dive Lore",
        "description": "Technical, info-dense with blueprint/schematic overlays.",
        "prompt_modifier": "Tone: Technical, detailed, and investigative. Focus on origins, mechanisms, and lore.",
        "visual_keywords": "blueprints, technical drawings, x-ray view, historical documents, schematics",
        "music_keywords": "sci-fi ambient, industrial drone, mysterious pulse",
        "remotion_flags": {"show_schematics": True, "vfx": "blueprint"}
    },
    "REDDIT_STORY": {
        "name": "Reddit Storyteller",
        "description": "Viral Reddit-style storytelling with split-screen satisfying footage.",
        "prompt_modifier": "Tone: Conversational, first-person ('I'), raw, and engaging. Start with a clear Reddit-style hook: 'AITA for...' or 'TIFU by...'.",
        "visual_keywords": "minecraft parkour, satisfying sand cutting, gta 5 racing, slime mixing",
        "music_keywords": "lofi hip hop, chill beats, cozy, jazzy lofi",
        "voice_id": "fln_paul_casual",
        "remotion_flags": {"layout": "split_screen", "show_reddit_hook": True, "satisfying_bg": True}
    },
    "PERSONA_MONTAGE": {
        "name": "Persona Montage",
        "description": "Multi-character scenes with unique voices for each segment.",
        "prompt_modifier": "Structure: Each segment MUST represent a different person. Use diverse perspectives.",
        "visual_keywords": "portrait, talking to camera, diverse people, emotional facial expressions",
        "music_keywords": "upbeat acoustic, friendly pop, conversational background",
        "remotion_flags": {"multi_voice": True, "show_name_plates": True}
    },
    "FAST_HYPE": {
        "name": "Fast-Paced Hype",
        "description": "Extreme retention style with auto-zooms and emojis.",
        "prompt_modifier": "Tone: Energetic, loud, and punchy. Use short, high-impact sentences.",
        "visual_keywords": "high action, sports highlights, flashing lights, fast cars, extreme sports",
        "music_keywords": "phonk, aggressive trap, extreme energy, high bpm",
        "voice_id": "fln_jake_hype",
        "remotion_flags": {"auto_zoom": True, "show_emojis": True, "vfx": "glitch"}
    },
    "NOIR_MYSTERY": {
        "name": "True Crime Noir",
        "description": "Moody, dark, and suspenseful investigative style.",
        "prompt_modifier": "Tone: Suspenseful, dark, and mysterious. Use low-whisper narrations.",
        "visual_keywords": "noir, low lighting, rainy streets, flickering neon, shadowy figures, 35mm film grain",
        "music_keywords": "dark noir jazz, suspenseful cello, dark ambient drone",
        "voice_id": "fln_shadow_noir",
        "remotion_flags": {"vfx": "monochrome_grain", "show_distorted_text": True}
    },
    "INVESTIGATION": {
        "name": "Investigation (UFO/Paranormal)",
        "description": "'Archival' aesthetic with magnifying glass highlights.",
        "prompt_modifier": "Tone: Skeptical but intrigued. Focus on 'leaked' evidence and sightings.",
        "visual_keywords": "night vision, thermal camera, grainy archival footage, leaked sightings, ufo",
        "music_keywords": "eerie pads, paranormal suspense, dark synth pulse",
        "remotion_flags": {"show_magnifier": True, "vfx": "green_tint"}
    },
    "RETRO_ARCHIVE": {
        "name": "Retro Archive",
        "description": "Analog nostalgia with VHS filters and 4:3 aspect ratio.",
        "prompt_modifier": "Tone: Nostalgic, historical. Reference 'the archives' or 'found footage'.",
        "visual_keywords": "vhs, 90s camcorder, home video, fuzzy screen, retro electronics",
        "music_keywords": "80s synthwave, analog tape noise, retro nostalgic",
        "remotion_flags": {"aspect_ratio": "4:3", "vfx": "vhs_glitch", "show_timestamp": True}
    },
    "BROADCAST_NEWS": {
        "name": "Broadcast News",
        "description": "Formal breaking news report style.",
        "prompt_modifier": "Tone: Urgent, formal, objective. Use 'Breaking news' and 'Reporting live'.",
        "visual_keywords": "newsroom, anchor, city drone shots, press conference",
        "music_keywords": "news broadcast theme, urgent orchestral, pulsing hybrid",
        "remotion_flags": {"show_ticker": True, "show_live_bug": True, "layout": "news"}
    },
    "TOP_LISTICLE": {
        "name": "Top 10 Listicle",
        "description": "Numbered countdown with rapid-fire facts.",
        "prompt_modifier": "Structure: Use a countdown format from 5 down to 1. Start each segment with 'Number X'. Tone: Energetic and fast-paced.",
        "visual_keywords": "numbered graphics, countdown timer, bright infographics, sports highlights",
        "music_keywords": "upbeat corporate, energetic pop, high energy trap",
        "voice_id": "fln_jake_hype",
        "remotion_flags": {"show_countdown": True, "show_ranking": True}
    },
    "MOTIVATIONAL": {
        "name": "Motivational Manifestation",
        "description": "Sweeping landscapes and glowing, ethereal typography.",
        "prompt_modifier": "Tone: Inspiring, calm, and powerful. Focus on mindset and success.",
        "visual_keywords": "sunrise, mountain peaks, wide landscapes, golden hour, slow motion",
        "music_keywords": "cinematic ambient, inspiring piano, ethereal pads",
        "remotion_flags": {"vfx": "glow", "typography": "serif_elegant"}
    },
    "PRODUCT_SHOWCASE": {
        "name": "Product Showcase",
        "description": "Ultra-clean Apple-style product presentations.",
        "prompt_modifier": "Tone: Luxurious, precise, and sophisticated.",
        "visual_keywords": "clean product photography, studio lighting, spinning objects, 3d render",
        "music_keywords": "elegant minimal tech, luxury ambient, clean digital",
        "remotion_flags": {"vfx": "liquid_transitions", "bg_color": "white"}
    },
    "REACTION_COMMENTARY": {
        "name": "Reaction/Commentary",
        "description": "Split-screen AI avatar reacting to content.",
        "prompt_modifier": "Tone: Opinionated, humorous, and expressive.",
        "visual_keywords": "talking head, expressive avatar, reaction face",
        "music_keywords": "upbeat funky, quirky comedy, humorous background",
        "remotion_flags": {"layout": "reaction_pip", "show_avatar": True}
    },
    "HORROR_CREEPY": {
        "name": "Horror Creepypasta",
        "description": "Jump-scare oriented dark storytelling.",
        "prompt_modifier": "Tone: Terrifying, unsettling. Use slow buildup and sharp transitions.",
        "visual_keywords": "dark hallway, creepy forest, distorted faces, abandonment",
        "music_keywords": "horror dark ambient, industrial horror, terrifying drones",
        "remotion_flags": {"vfx": "glitch_jumpscare", "audio": "horror_ambience"}
    },
    "LOFI_CHILL": {
        "name": "Lofi Chill Beats",
        "description": "Cozy anime loops with music visualizers.",
        "prompt_modifier": "Tone: Relaxing, calm, and cozy.",
        "visual_keywords": "anime girl study, rainy window, lofi aesthetic, 2d animation loop",
        "music_keywords": "lofi hip hop, jazzy beats, rain background",
        "remotion_flags": {"show_visualizer": True, "show_clock": True}
    },
    "PODCAST_SIM": {
        "name": "Podcast Simulation",
        "description": "Multi-camera podcast conversation style.",
        "prompt_modifier": "Tone: Conversational, casual, and interview-like.",
        "visual_keywords": "podcast studio, microphone, two people talking, close up face",
        "music_keywords": "jazz hop, conversational background, smooth acoustic",
        "remotion_flags": {"layout": "podcast_switch", "multi_voice": True}
    },
    "HEARTFELT_NARRATIVE": {
        "name": "Heartfelt Narrative (Life Lessons)",
        "description": "Emotional, reflective storytelling with cinematic visuals and somber piano.",
        "prompt_modifier": "Tone: Reflective, vulnerable, and sincere. Use pauses for emotional weight. Focus on 'lessons learned' and personal growth. Start with a hook about a life-changing realization.",
        "visual_keywords": "soft lighting, pensive expressions, slow motion, nature, urban melancholy, warm bokeh, sunset reflection, teary eyes",
        "music_keywords": "emotional piano, cinematic strings, somber ambient, minimalist acoustic",
        "voice_id": "fln_sophia_empathetic",
        "remotion_flags": {"vfx": "film_grain", "typography": "serif_elegant", "slow_motion": True, "show_headline": True}
    },
    "STOIC_WISDOM": {
        "name": "Stoic Wisdom (Ancient Quotes)",
        "description": "High-contrast black and white with classical statues and deep, resonant wisdom.",
        "prompt_modifier": "Tone: Deeply philosophical, calm, and authoritative. Use short, powerful quotes from Marcus Aurelius or Seneca. Focus on discipline, inner strength, and the dichotomy of control.",
        "visual_keywords": "marble statue, greek architecture, high contrast black and white, slow pan, shadows, classical art, ancient stone",
        "music_keywords": "deep cinematic drone, low cello, atmospheric ambient, resonant bass",
        "voice_id": "fln_marcus_narrator",
        "remotion_flags": {"vfx": "monochrome_high_contrast", "typography": "serif_classical", "slow_motion": True}
    },
    "RELATIONSHIP_DRAMA": {
        "name": "Relationship Drama / Regret",
        "description": "Raw, emotional stories of heartbreak, divorce, and life lessons with moody urban visuals.",
        "prompt_modifier": "Tone: Emotional, raw, and confessional. Start with a shocking or deeply vulnerable hook (e.g., 'I realized too late that I had destroyed the one thing that mattered'). Focus on regret, realizations, and the messy reality of relationships.",
        "visual_keywords": "pensive window gaze, rainy urban streets, empty rooms, dim lighting, emotional expressions, realistic character scenes, moody atmosphere",
        "music_keywords": "somber acoustic guitar, melancholic piano, distant rain sounds, emotional strings",
        "voice_id": "fln_sophia_empathetic",
        "remotion_flags": {"vfx": "melancholic_filter", "typography": "sans_clean", "show_text_bubbles": True}
    },
    "TRAVEL_VLOG": {
        "name": "Travel Vlog / Wanderlust",
        "description": "Fast-paced, vibrant travel sequences with map animations and upbeat energy.",
        "prompt_modifier": "Tone: Adventurous, enthusiastic, and curious. Focus on hidden gems, local culture, and the feeling of freedom. Use fast-paced narration.",
        "visual_keywords": "drone shots, vibrant markets, tropical beaches, bustling city streets, map zoom, backpacker aesthetic, sun-drenched visuals",
        "music_keywords": "upbeat indie folk, acoustic pop, fast percussion, tropical house",
        "voice_id": "fln_jake_hype",
        "remotion_flags": {"vfx": "vibrant_bloom", "show_map_overlay": True, "fast_cuts": True}
    },
    "FITNESS_MOTIVATION": {
        "name": "Fitness Motivation / The Grind",
        "description": "Aggressive, high-intensity workout reels with beat-synced transitions.",
        "prompt_modifier": "Tone: Aggressive, motivational, and intense. Focus on pain, gain, and the work required to succeed. Use punchy, short sentences.",
        "visual_keywords": "gym setting, heavy weights, sweating, intense focus, slow motion lifts, dark lighting, neon highlights, muscular definition",
        "music_keywords": "hardstyle, phonk, aggressive trap, high bpm cinematic",
        "voice_id": "fln_jake_hype",
        "remotion_flags": {"vfx": "glitch_shake", "typography": "impact_bold", "beat_sync": True}
    },
    "GAMING_LORE": {
        "name": "Gaming Lore / World Building",
        "description": "Epic, technical deep-dives into video game universes, characters, and secrets.",
        "prompt_modifier": "Tone: Mysterious, epic, and technical. Discuss hidden secrets, timeline theories, and character backstories with weight and authority. Use 'The legend says...' or 'Deep in the game files...'.",
        "visual_keywords": "cinematic game world, concept art, character close-ups, fantasy environments, cyberpunk aesthetics, digital artifacts, game engine renders",
        "music_keywords": "dark ambient synth, epic cinematic, mysterious pulse, industrial drone",
        "voice_id": "fln_shadow_noir",
        "remotion_flags": {"vfx": "blueprint", "typography": "sans_clean", "show_schematics": True}
    },
    "ESPORTS_HYPE": {
        "name": "eSports Hype / Gameplay",
        "description": "High-octane competitive gaming highlights with energetic narration and transitions.",
        "prompt_modifier": "Tone: Energetic, fast-paced, and hype-focused. Comment on high-skill plays, tournament stakes, and legendary clutch moments. Use 'Unbelievable play!' or 'The crown is on the line!'.",
        "visual_keywords": "esports tournament, pro player setup, high-action gameplay, crowd cheering, neon gaming lights, victory screen, kinetic graphics",
        "music_keywords": "aggressive trap, high-energy phonk, rhythmic edm, synthwave pulse",
        "voice_id": "fln_jake_hype",
        "remotion_flags": {"vfx": "glitch", "typography": "impact_bold", "auto_zoom": True, "beat_sync": True}
    }
}

def get_style(style_id: str) -> Dict[str, Any]:
    return STYLE_DEFINITIONS.get(style_id, STYLE_DEFINITIONS["CINEMATIC_DOC"])
