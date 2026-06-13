#!/usr/bin/env python3
"""Comprehensive fix for nexus/page.tsx - all template literals in JSX style={} blocks"""


path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    content = f.read()

original = content
changes = []

# ==============================================================================
# FIX 1: Line ~499 - progress bar width
# ==============================================================================
old = "style={{ width: `${job.progress || 0}%` }}"
new = "style={{ width: (job.progress || 0) + '%' }}"
if old in content:
    content = content.replace(old, new)
    changes.append("1. Progress bar width template literal")
    print("Fix 1: progress bar width - OK")

# ==============================================================================
# FIX 2: Lines ~799-800 - radar chart left/top percentages
# ==============================================================================
old = "left: `${x}%`,"
new = "left: x + '%',"
if old in content:
    content = content.replace(old, new)
    changes.append("2. Radar chart left percentage")
    print("Fix 2: left percentage - OK")
else:
    print("Fix 2: left percentage - NOT FOUND")

old = "top: `${y}%`,"
new = "top: y + '%',"
if old in content:
    content = content.replace(old, new)
    changes.append("3. Radar chart top percentage")
    print("Fix 3: top percentage - OK")
else:
    print("Fix 3: top percentage - NOT FOUND")

# ==============================================================================
# FIX 4: Lines ~1357, ~1370 - histogram bar heights
# ==============================================================================
old = "style={{ height: `${h * 10}%` }}"
new = "style={{ height: h * 10 + '%' }}"
count = content.count(old)
if count > 0:
    content = content.replace(old, new)
    changes.append(f"4. Histogram bar heights ({count} occurrences)")
    print(f"Fix 4: histogram heights - OK ({count} occurrences)")
else:
    print("Fix 4: histogram heights - NOT FOUND")

# ==============================================================================
# FIX 5: Line ~1572 - transform scale
# ==============================================================================
old = "transform: `scale(${1 + (kenBurnsSpeed * 0.005)})`,"
new = "transform: 'scale(' + (1 + kenBurnsSpeed * 0.005) + ')',"
if old in content:
    content = content.replace(old, new)
    changes.append("5. Transform scale template literal")
    print("Fix 5: transform scale - OK")
else:
    print("Fix 5: transform scale - NOT FOUND")

# ==============================================================================
# FIX 6: Lines ~1573-1578 - multi-line filter template
# ==============================================================================
# Find and replace the entire multi-line filter template
# The pattern spans from "filter: `" to the closing backtick
filter_start = content.find("filter: `")
if filter_start >= 0:
    # Find the closing backtick
    filter_end = content.find("`", filter_start + 8)  # 8 = len("filter: `")
    if filter_end >= 0:
        # Check if it's multi-line
        filter_content = content[filter_start:filter_end+1]
        if '\n' in filter_content:
            # Multi-line - replace with single line filterStyle
            old = filter_content
            new = "filter: filterStyle"
            content = content.replace(old, new)
            changes.append("6. Multi-line filter template replaced with filterStyle")
            print(f"Fix 6: multi-line filter - OK (removed {filter_content.count(chr(10))} lines)")
        else:
            # Single-line filter template
            old = "filter: `...`"
            new = "filter: filterStyle"
            if old in content:
                content = content.replace(old, new)
                changes.append("6. Single-line filter template")
                print("Fix 6: filter template - OK (single-line)")
else:
    # Already replaced
    print("Fix 6: filter template - already replaced or not found")

# ==============================================================================
# FIX 7: Line ~1587 - backgroundSize template literal
# ==============================================================================
old = "backgroundSize: `${10 - (grainDensity * 0.08)}px ${10 - (grainDensity * 0.08)}px`,"
new = "backgroundSize: (10 - grainDensity * 0.08) + 'px ' + (10 - grainDensity * 0.08) + 'px',"
if old in content:
    content = content.replace(old, new)
    changes.append("7. BackgroundSize template literal")
    print("Fix 7: backgroundSize - OK")
else:
    print("Fix 7: backgroundSize - NOT FOUND")

# ==============================================================================
# FIX 8: Line ~1133 - progress value in metrics object
# ==============================================================================
old = "{ label: \"Completion\", value: `${job.progress || 0}%`, progress: job.progress, color: \"text-cyan-400\" },"
new = "{ label: \"Completion\", value: (job.progress || 0) + \"%\", progress: job.progress, color: \"text-cyan-400\" },"
if old in content:
    content = content.replace(old, new)
    changes.append("8. Progress value in metrics")
    print("Fix 8: progress value - OK")
else:
    print("Fix 8: progress value - NOT FOUND")

# ==============================================================================
# FIX 9: <style jsx global> replacement
# ==============================================================================
if '<style jsx global>' in content:
    # Replace with plain <style>
    content = content.replace('<style jsx global>{`', '<style>')
    content = content.replace('`}</style>', '</style>')
    changes.append("9. <style jsx global> replaced with plain <style>")
    print("Fix 9: style jsx global - OK")
else:
    print("Fix 9: style jsx global - already replaced or not found")

# ==============================================================================
# FIX 10: animationDelay template (if not already fixed)
# ==============================================================================
old = "style={{ animationDelay: `${idx * 0.3}s` }}"
new = "style={{ animationDelay: idx * 0.3 + 's' }}"
if old in content:
    content = content.replace(old, new)
    changes.append("10. animationDelay template literal")
    print("Fix 10: animationDelay - OK")
else:
    print("Fix 10: animationDelay - not found or already fixed")

# ==============================================================================
# ADD filterStyle useMemo after contrast declaration
# ==============================================================================
# First find the contrast useState line
contrast_pattern = "const [contrast, setContrast] = useState"
contrast_idx = content.find(contrast_pattern)
if contrast_idx >= 0:
    # Check if filterStyle already exists
    if 'const filterStyle = useMemo' not in content:
        # Find the end of this line
        line_end = content.find('\n', contrast_idx) + 1
        # Insert useMemo after this line
        useMemo_code = """

    // Filter style computed from style customizer state
    const filterStyle = useMemo(() => {
        const temp = colorTemp / 100;
        const contrastVal = 1 + (contrast - 50) / 50;
        const sepiaVal = temp * 30;
        return `contrast(${contrastVal.toFixed(2)}) sepia(${sepiaVal.toFixed(1)}%)`;
    }, [selectedStylePreset, colorTemp, contrast]);
"""
        content = content[:line_end] + useMemo_code + content[line_end:]
        changes.append("11. filterStyle useMemo added")
        print("Fix 11: filterStyle useMemo - OK")
    else:
        print("Fix 11: filterStyle useMemo - already exists")
else:
    print("Fix 11: filterStyle useMemo - contrast pattern not found!")

# ==============================================================================
# Write changes
# ==============================================================================
if content != original:
    with open(path, 'w') as f:
        f.write(content)
    print("\n=== WROTE CHANGES ===")
    print(f"Total fixes: {len(changes)}")
    for c in changes:
        print(f"  - {c}")
else:
    print("\nNo changes needed")