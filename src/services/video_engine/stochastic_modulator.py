import hashlib
import random
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

THEME_PRESETS: Dict[str, Dict[str, Any]] = {
    "AMBER_WARM": {
        "color_profile": {
            "contrast": 1.15,
            "saturation": 0.95,
            "grain": 0.04,
            "color_temp": 4800, # Warm amber tint
        },
        "remotion_flags": {
            "typography": "serif_elegant",
            "slow_motion": True,
            "vfx": "warm_glow",
        },
        "music_keywords": "acoustic piano, warm ambient, acoustic folk",
    },
    "NEON_CYBER": {
        "color_profile": {
            "contrast": 1.35,
            "saturation": 1.30,
            "grain": 0.08,
            "color_temp": 7500, # Cool/blue neon tint
        },
        "remotion_flags": {
            "typography": "impact_bold",
            "auto_zoom": True,
            "vfx": "glitch_shake",
            "beat_sync": True,
        },
        "music_keywords": "cyberpunk synthwave, industrial electronic, aggressive trap",
    },
    "MONOCHROME_DARK": {
        "color_profile": {
            "contrast": 1.45,
            "saturation": 0.0, # Black & white
            "grain": 0.07,
            "color_temp": 6500, # Neutral
        },
        "remotion_flags": {
            "typography": "serif_classical",
            "slow_motion": True,
            "vfx": "monochrome_grain",
        },
        "music_keywords": "melancholic solo cello, dark ambient drone, somber piano",
    }
}

class StochasticModulator:
    """
    Introduces controlled, deterministic randomness to video generation parameters
    based on a seed (e.g. job_id or search query). This ensures a video render is
    reproducible given the same inputs, while offering unique artistic variance across
    different jobs.
    """

    def __init__(self, seed: Optional[str] = None):
        self.seed = seed or "default_seed"
        # Generate a stable integer seed from string hash
        hasher = hashlib.sha256(self.seed.encode("utf-8"))
        self._seed_int = int(hasher.hexdigest(), 16) % (2**32)
        self.rng = random.Random(self._seed_int)

    def modulate_value(self, base: float, variance: float, min_val: float, max_val: float) -> float:
        """Perturbs a base float value by a variance percentage, clamped between min/max."""
        factor = self.rng.uniform(1.0 - variance, 1.0 + variance)
        return max(min_val, min(max_val, base * factor))

    def get_random_theme_preset(self) -> str:
        """Select a random ThemePreset from the available list."""
        return self.rng.choice(list(THEME_PRESETS.keys()))

    def _apply_theme_preset(self, config: Dict[str, Any], theme_preset_name: Optional[str]) -> None:
        """Apply theme preset overrides to config."""
        if not theme_preset_name:
            return
        preset = THEME_PRESETS.get(theme_preset_name)
        if not preset:
            return

        logger.info(f"[StochasticModulator] Applying ThemePreset: {theme_preset_name}")
        if "color_profile" not in config:
            config["color_profile"] = {}
        config["color_profile"].update(preset["color_profile"])

        if "remotion_flags" not in config:
            config["remotion_flags"] = {}
        config["remotion_flags"].update(preset["remotion_flags"])

        if "music_keywords" in preset:
            config["music_keywords"] = preset["music_keywords"]

    def _modulate_color_profile(self, color: Dict[str, Any]) -> None:
        """Modulate Color Grading properties stochastically."""
        contrast = float(color.get("contrast", 1.2))
        color["contrast"] = round(self.modulate_value(contrast, variance=0.10, min_val=0.9, max_val=1.6), 2)

        # Do not modulate saturation if monochrome (saturation = 0)
        saturation = float(color.get("saturation", 1.1))
        if saturation > 0.01:
            color["saturation"] = round(self.modulate_value(saturation, variance=0.15, min_val=0.7, max_val=1.5), 2)

        grain = float(color.get("grain", 0.05))
        color["grain"] = round(self.modulate_value(grain, variance=0.30, min_val=0.01, max_val=0.15), 3)

        color_temp = float(color.get("color_temp", 5500))
        color["color_temp"] = int(self.modulate_value(color_temp, variance=0.08, min_val=3500, max_val=9000))

    def _modulate_remotion_flags(self, flags: Dict[str, Any]) -> None:
        """Modulate timing and motion parameters."""
        if "zoom_intensity" in flags:
            zoom = float(flags["zoom_intensity"])
            flags["zoom_intensity"] = round(self.modulate_value(zoom, variance=0.20, min_val=1.01, max_val=1.25), 3)
        else:
            # Inject a modulated default zoom factor
            flags["zoom_intensity"] = round(self.rng.uniform(1.05, 1.15), 3)

        if "transition_duration_seconds" in flags:
            duration = float(flags["transition_duration_seconds"])
            flags["transition_duration_seconds"] = round(self.modulate_value(duration, variance=0.25, min_val=0.1, max_val=1.5), 2)
        else:
            flags["transition_duration_seconds"] = round(self.rng.uniform(0.2, 0.6), 2)

    def apply_modulation(self, style_config: Dict[str, Any], theme_preset_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Applies theme preset overrides and stochastically modulates color, timing, and zoom properties.
        """
        # Create a deep copy of style_config
        config = {k: (v.copy() if isinstance(v, dict) else v) for k, v in style_config.items()}

        self._apply_theme_preset(config, theme_preset_name)

        # Ensure dictionary structures exist
        if "color_profile" not in config:
            config["color_profile"] = {}
        if "remotion_flags" not in config:
            config["remotion_flags"] = {}

        self._modulate_color_profile(config["color_profile"])
        self._modulate_remotion_flags(config["remotion_flags"])

        logger.debug(f"[StochasticModulator] Modulated style config: {config}")
        return config

# Singleton / convenience helper
def modulate_style(style_config: Dict[str, Any], seed: str, theme_preset: Optional[str] = None) -> Dict[str, Any]:
    modulator = StochasticModulator(seed)
    return modulator.apply_modulation(style_config, theme_preset)
