#!/usr/bin/env python3

path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    content = f.read()

original = content

# FIX 1: Line 499 - progress bar width
content = content.replace(
    '<div className="h-full bg-cyan-500" style={{ width: `${job.progress || 0}%` }} />',
    '<div className="h-full bg-cyan-500" style={{ width: (job.progress || 0) + "%" }} />'
)
print("Fix 1 (width): " + str('width: (job.progress' in content))

# FIX 2: Lines 799-800 - radar chart left/top percentages
content = content.replace("left: `${x}%`,", "left: x + '%',")
content = content.replace("top: `${y}%`,", "top: y + '%',")
print("Fix 2 (left/top): " + str("left: x + '%'" in content))

# FIX 3: Line 1332 - animationDelay (s, not %)
content = content.replace(
    "style={{ animationDelay: `${idx * 0.3}s` }}",
    "style={{ animationDelay: idx * 0.3 + 's' }}"
)
print("Fix 3 (animationDelay): " + str("animationDelay: idx * 0.3 + 's'" in content))

# FIX 4: Lines 1357 and 1370 - histogram bar heights
content = content.replace(
    "style={{ height: `${h * 10}%` }}",
    "style={{ height: h * 10 + '%' }}"
)
print("Fix 4 (height): " + str("height: h * 10 + '%'" in content))

# FIX 5: Line 1572 - transform scale
content = content.replace(
    "                                                        transform: `scale(${1 + (kenBurnsSpeed * 0.005)})`,",
    "                                                        transform: 'scale(' + (1 + kenBurnsSpeed * 0.005) + '),"
)
print("Fix 5 (transform): " + str("transform: 'scale('" in content))

# FIX 6: Lines 1573-1578 - multi-line filter template
# The block spans from "filter: `" through the closing backtick on its own line
# We need to find this block and replace it entirely with "filter: filterStyle"
# The block looks like:
#   filter: `
#       contrast(...) 
#       sepia(...)%
#       hue-rotate(...)deg)
#       grayscale(...)%
#   `   (at 56 spaces indentation)

# Find the start of the multi-line filter block
filter_block_start = '                                                        filter: `\n                                                            contrast('
start_idx = content.find(filter_block_start)
if start_idx < 0:
    print("WARNING: Could not find multi-line filter start")
else:
    # Find the end - the closing backtick is on a line with 56 spaces + `
    # Looking for: '\n                                                        `'
    after_start = start_idx + len(filter_block_start)
    end_backtick = content.find('\n                                                        `', after_start)
    if end_backtick < 0:
        print("WARNING: Could not find filter block closing backtick")
    else:
        # Include the backtick line itself
        end_idx = end_backtick + len('\n                                                        `')
        old_block = content[start_idx:end_idx]
        
        # Verify this is the correct block by checking content
        if 'sepia(' in old_block and 'hue-rotate(' in old_block and 'grayscale(' in old_block:
            new_block = '                                                        filter: filterStyle\n                                                \n'
            content = content.replace(old_block, new_block)
            print("Fix 6 (multi-line filter): " + str('filter: filterStyle' in content))
        else:
            print("WARNING: Filter block content unexpected")
            print("Block content: " + repr(old_block[:200]))

# FIX 7: Line 1587 - backgroundSize
content = content.replace(
    "                                                        backgroundSize: `${10 - (grainDensity * 0.08)}px ${10 - (grainDensity * 0.08)}px`,",
    "                                                        backgroundSize: (10 - grainDensity * 0.08) + 'px ' + (10 - grainDensity * 0.08) + 'px',"
)
print("Fix 7 (backgroundSize): " + str('backgroundSize: (10 - grainDensity' in content))

# FIX 8: Progress value in display object (line 1126) - same pattern as width
content = content.replace(
    'value: `${job.progress || 0}%`',
    'value: (job.progress || 0) + "%"'
)
print("Fix 8 (progress value): " + str('value: (job.progress' in content))

# ADD useMemo for filterStyle after contrast declaration
# Find "const [contrast, setContrast] = useState<number>(50);"
marker = "    const [contrast, setContrast] = useState<number>(50);"
idx = content.find(marker)
if idx >= 0:
    insert_at = idx + len(marker)
    useMemo_code = """

    // Filter style computed from style customizer state
    const filterStyle = useMemo(() => {
        const preset = selectedStylePreset;
        const temp = colorTemp / 100;
        const contrastVal = 1 + (contrast - 50) / 50;
        const sepiaVal = temp * 30;
        return `contrast(${contrastVal.toFixed(2)}) sepia(${sepiaVal.toFixed(1)}%)`;
    }, [selectedStylePreset, colorTemp, contrast]);
"""
    content = content[:insert_at] + useMemo_code + content[insert_at:]
    print("Added filterStyle useMemo after contrast declaration")
else:
    print("WARNING: Could not find contrast useState marker")

if content != original:
    with open(path, 'w') as f:
        f.write(content)
    print("\nFile written!")
    
    # Verify
    with open(path) as f:
        verify = f.read()
    lines = verify.split('\n')
    print(f"Total lines: {len(lines)}")
    
    # Check for remaining template literals
    print("\nRemaining template literals:")
    for i, line in enumerate(lines, 1):
        if '`' in line:
            print(f"  Line {i}: {repr(line.strip()[:150])}")
    
    # Order check
    colorTemp_pos = verify.find('const [colorTemp')
    contrast_pos = verify.find('const [contrast')
    filterStyle_pos = verify.find('const filterStyle = useMemo')
    
    if colorTemp_pos >= 0 and contrast_pos >= 0 and filterStyle_pos >= 0:
        print(f"\nOrder: colorTemp({colorTemp_pos}) < contrast({contrast_pos}) < filterStyle({filterStyle_pos})")
        if colorTemp_pos < contrast_pos < filterStyle_pos:
            print("ORDER: CORRECT")
        else:
            print("ORDER: POTENTIAL ISSUE")
    
    # Verify filter: filterStyle is in the right place (inside the style block)
    filter_style_usage = verify.find('filter: filterStyle')
    if filter_style_usage >= 0:
        # Check context - should be inside style={{ }}
        context = verify[max(0, filter_style_usage-200):filter_style_usage+50]
        if 'style={{' in context and 'backgroundImage' in context:
            print("filter: filterStyle is in correct style block context: YES")
        else:
            print("WARNING: filter: filterStyle may not be in style block context")
else:
    print("\nNo changes made!")