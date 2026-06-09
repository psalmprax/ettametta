#!/usr/bin/env python3

path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    content = f.read()

original = content

# FIX 1: Line 499 - progress bar width
content = content.replace(
    "style={{ width: `${job.progress || 0}%` }}",
    "style={{ width: (job.progress || 0) + '%' }}"
)
print("Fix 1 (width %): " + str('width: (job.progress' in content))

# FIX 2: Lines 799-800 - radar chart left/top percentages
content = content.replace("left: `${x}%`,", "left: x + '%',")
content = content.replace("top: `${y}%`,", "top: y + '%',")
print("Fix 2 (left/top %): " + str('left: x + ' in content))

# FIX 3: Line 1332 - animationDelay (no %, just s)
content = content.replace(
    "style={{ animationDelay: `${idx * 0.3}s` }}",
    "style={{ animationDelay: idx * 0.3 + 's' }}"
)
print("Fix 3 (animationDelay): " + str('animationDelay: idx * 0.3 + ' in content))

# FIX 4: Lines 1357 and 1370 - histogram bar heights
content = content.replace(
    "style={{ height: `${h * 10}%` }}",
    "style={{ height: h * 10 + '%' }}"
)
print("Fix 4 (height %): " + str('height: h * 10 + ' in content))

# FIX 5: Line 1572 - transform scale
content = content.replace(
    "                                                        transform: `scale(${1 + (kenBurnsSpeed * 0.005)})`,",
    "                                                        transform: 'scale(' + (1 + kenBurnsSpeed * 0.005) + '),"
)
print("Fix 5 (transform scale): " + str('scale(' in content))

# FIX 6: Lines 1573-1578 - multi-line filter template
start_marker = '                                                        filter: `'
start_idx = content.find(start_marker)
if start_idx >= 0:
    end_search = content.find('\n                                                        `', start_idx)
    if end_search >= 0:
        end_idx = end_search + len('\n                                                        `')
        old_block = content[start_idx:end_idx]
        if 'contrast(' in old_block and 'sepia(' in old_block:
            new_block = '                                                        filter: filterStyle'
            content = content.replace(old_block, new_block)
            print("Fix 6 (filter multi-line): " + str('filter: filterStyle' in content))
        else:
            print("Fix 6 FAILED - unexpected block content")
    else:
        print("Fix 6 FAILED - could not find end marker")
else:
    print("Fix 6 FAILED - could not find filter start")

# FIX 7: Line 1587 - backgroundSize
content = content.replace(
    "                                                        backgroundSize: `${10 - (grainDensity * 0.08)}px ${10 - (grainDensity * 0.08)}px`,",
    "                                                        backgroundSize: (10 - grainDensity * 0.08) + 'px ' + (10 - grainDensity * 0.08) + 'px',"
)
print("Fix 7 (backgroundSize): " + str('backgroundSize: (10 - grainDensity' in content))

# Add useMemo for filterStyle before const declarations
useMemo_block = """const [filterStyle] = useMemo(() => {
    const contrast = selectedStylePreset === 'cinematic' ? 1.2
        : selectedStylePreset === 'documentary' ? 1.15
        : selectedStylePreset === 'viral' ? 1.3
        : 1;
    const sepia = colorTemp === 'warm' ? 15 : colorTemp === 'cool' ? 5 : 0;
    const hue = hueShift || 0;
    const gray = colorEffect === 'bwcapture' ? 100 : colorEffect === 'grain' ? 25 : 0;
    return `contrast(${contrast}) sepia(${sepia}%) hue-rotate(${hue}deg) grayscale(${gray}%)`;
}, [selectedStylePreset, colorTemp, hueShift, colorEffect]);

"""

insert_before = 'const [jobs, setJobs]'
insert_idx = content.find(insert_before)
if insert_idx >= 0:
    content = content[:insert_idx] + useMemo_block + content[insert_idx:]
    print("useMemo inserted: " + str('useMemo' in content and 'filterStyle' in content))
else:
    print("useMemo insertion point not found!")

if content != original:
    with open(path, 'w') as f:
        f.write(content)
    print("\nFile written successfully!")
    # Verify
    with open(path) as f:
        verify = f.read()
    lines = verify.split('\n')
    print("Total lines now: " + str(len(lines)))
    print("\nRemaining backtick lines:")
    for i, line in enumerate(lines, 1):
        if '`' in line:
            print("  Line " + str(i) + ": " + repr(line.strip()[:150]))
else:
    print("\nNo changes made!")