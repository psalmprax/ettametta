from src.services.optimization.humanizer import base_humanizer

def test_humanizer_replacements():
    """Verify that common AI slop words and phrases are correctly humanized."""
    # Test individual slop words replacement
    test_cases = [
        ("We should leverage this tool.", "We should use this tool."),
        ("Delve deeper into the code.", "Dig deeper into the code."),
        ("This is a testament to our progress.", "This is a proof to our progress."),
        ("A vibrant community.", "A lively community."),
        ("In the current tech landscape.", "In the current tech environment."),
        ("A pivotal moment in history.", "A key moment in history."),
        ("A rich tapestry of experiences.", "A rich mix of experiences."),
        ("This is a game-changer.", "This is a big deal."),
        ("To revolutionize our approach.", "To change our approach."),
        ("A multifaceted solution.", "A varied solution."),
        ("Moreover, it is faster.", "Also, it is faster."),
        ("Furthermore, we found bugs.", "Also, we found bugs."),
        ("In the realm of science.", "In the area of science."),
        ("Let's demystify the system.", "Let's explain the system."),
        ("A beacon of hope.", "A guide of hope."),
        ("A treasure trove of ideas.", "A goldmine of ideas."),
        ("This underscores the importance.", "This shows the importance."),
        ("Elevate your skills.", "Raise your skills."),
        ("Foster a culture of learning.", "Build a culture of learning."),
        ("Streamline the pipeline.", "Simplify the pipeline."),
        ("Nestled in the mountains.", "Located in the mountains."),
        ("Whispers about the feature.", "Rumors about the feature."),
        ("It is important to note that we are done.", "we are done."),
        ("A plethora of options.", "A lot of options."),
        ("Utmost respect.", "Greatest respect."),
        ("Bespoke tailoring.", "Custom tailoring."),
        ("Cutting-edge technology.", "Modern technology."),
        ("Robust system.", "Reliable system."),
    ]

    for original, expected in test_cases:
        assert base_humanizer.humanize(original) == expected

def test_humanizer_none_and_empty():
    """Verify that None and empty strings are handled gracefully."""
    assert base_humanizer.humanize(None) is None
    assert base_humanizer.humanize("") == ""

def test_humanizer_spacing_cleanup():
    """Verify that multiple consecutive spaces are collapsed after replacements."""
    original = "It is important to note that   we need to simplify things."
    expected = "we need to simplify things."
    assert base_humanizer.humanize(original) == expected
