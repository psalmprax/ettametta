#!/usr/bin/env python3

path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    content = f.read()

original = content

# FIX: Line 508 - progress bar width inside style={{}}
content = content.replace(
    '<div className="h-full bg-cyan-500" style={{ width: `${job.progress || 0}%` }} />',
    '<div className="h-full bg-cyan-500" style={{ width: (job.progress || 0) + "%" }} />'
)
print("Fix 1 (width): " + str('width: (job.progress' in content))

# FIX: Line 1341 - animationDelay
content = content.replace(
    'style={{ animationDelay: `${idx * 0.3}s` }}',
    "style={{ animationDelay: idx * 0.3 + 's' }}"
)
print("Fix 2 (animationDelay): " + str("animationDelay: idx * 0.3 + 's'" in content))

# FIX: Lines 1366 and 1379 - histogram bar heights
content = content.replace(
    'style={{ height: `${h * 10}%` }}',
    "style={{ height: h * 10 + '%' }}"
)
print("Fix 3 (height): " + str("height: h * 10 + '%'" in content))

# FIX: Clean up the blank line left by removing multi-line filter closing backtick
# The closing backtick line was removed but left a blank line
# Remove consecutive blank lines in the style block area
content = content.replace(
    '                                                        filter: filterStyle\n\n                                                ',
    '                                                        filter: filterStyle\n                                                '
)
print("Fix 4 (cleanup blank line): done")

# FIX: Line 1135 - the value field in progress object (inside JSX expression, not style={})
# This one is trickier: `{ label: "Completion", value: `${job.progress || 0}%`, ...`
# This is inside a JSX expression context, not a style={} block, so might be OK
# But let me check if it's inside any JSX attribute
# Actually looking at line 1135 context - it's a value in a display object, not a style
# Let me fix it too just to be safe
content = content.replace(
    'value: `${job.progress || 0}%`',
    'value: (job.progress || 0) + "%"'
)
print("Fix 5 (progress value): " + str('value: (job.progress' in content))

if content != original:
    with open(path, 'w') as f:
        f.write(content)
    print("\nFile written!")
else:
    print("\nNo changes!")

# Verify remaining template literals in style={} blocks
with open(path) as f:
    lines = f.readlines()

print("\nRemaining template literals:")
for i, line in enumerate(lines, 1):
    if '`' in line:
        print(f"  Line {i}: {repr(line.strip()[:150])}")