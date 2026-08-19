from src.services.video_engine.stochastic_modulator import StochasticModulator, modulate_style

def test_stochastic_modulator_determinism():
    """Verify that the same seed produces identical modulated configs, while different seeds vary."""
    config = {
        "color_profile": {
            "contrast": 1.2,
            "saturation": 1.1,
            "grain": 0.05,
            "color_temp": 5500,
        },
        "remotion_flags": {
            "zoom_intensity": 1.1,
            "transition_duration_seconds": 0.5,
        }
    }

    # Same seed should be identical
    mod1 = StochasticModulator("seed-1")
    mod2 = StochasticModulator("seed-1")
    res1 = mod1.apply_modulation(config)
    res2 = mod2.apply_modulation(config)

    assert res1 == res2

    # Different seed should produce different values (with very high probability)
    mod3 = StochasticModulator("seed-2")
    res3 = mod3.apply_modulation(config)

    assert res1 != res3

def test_stochastic_modulator_clamping_limits():
    """Verify that modulated values respect their defined mathematical boundaries."""
    config = {
        "color_profile": {
            "contrast": 2.0, # Exceeds max_val 1.6
            "saturation": 2.0, # Exceeds max_val 1.5
            "grain": 0.5, # Exceeds max_val 0.15
            "color_temp": 12000, # Exceeds max_val 9000
        },
        "remotion_flags": {
            "zoom_intensity": 2.0, # Exceeds max_val 1.25
            "transition_duration_seconds": 5.0, # Exceeds max_val 1.5
        }
    }

    mod = StochasticModulator("aggressive-seed")
    res = mod.apply_modulation(config)

    color = res["color_profile"]
    flags = res["remotion_flags"]

    assert 0.9 <= color["contrast"] <= 1.6
    assert 0.7 <= color["saturation"] <= 1.5
    assert 0.01 <= color["grain"] <= 0.15
    assert 3500 <= color["color_temp"] <= 9000
    assert 1.01 <= flags["zoom_intensity"] <= 1.25
    assert 0.1 <= flags["transition_duration_seconds"] <= 1.5

def test_apply_theme_presets():
    """Verify that theme presets correctly override base configurations and apply their rules."""
    config = {
        "color_profile": {
            "contrast": 1.0,
            "saturation": 1.0,
        },
        "remotion_flags": {
            "typography": "sans_clean",
        }
    }

    # Test MONOCHROME_DARK preset
    res = modulate_style(config, "test-seed", "MONOCHROME_DARK")
    assert res["color_profile"]["saturation"] == 0.0
    assert res["remotion_flags"]["typography"] == "serif_classical"
    assert res["remotion_flags"]["vfx"] == "monochrome_grain"

    # Test AMBER_WARM preset
    res_warm = modulate_style(config, "test-seed", "AMBER_WARM")
    assert res_warm["remotion_flags"]["typography"] == "serif_elegant"
    assert res_warm["remotion_flags"]["vfx"] == "warm_glow"

    # Test NEON_CYBER preset
    res_cyber = modulate_style(config, "test-seed", "NEON_CYBER")
    assert res_cyber["remotion_flags"]["typography"] == "impact_bold"
    assert res_cyber["remotion_flags"]["vfx"] == "glitch_shake"
    assert res_cyber["remotion_flags"]["beat_sync"] is True

def test_missing_config_structures():
    """Verify that modulator injects missing keys or dictionary structures gracefully."""
    config = {}
    res = modulate_style(config, "seed-empty")

    assert "color_profile" in res
    assert "remotion_flags" in res
    assert "contrast" in res["color_profile"]
    assert "zoom_intensity" in res["remotion_flags"]
