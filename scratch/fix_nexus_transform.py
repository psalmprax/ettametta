#!/usr/bin/env python3
"""Fix the broken transform line and style block in nexus/page.tsx"""

path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    content = f.read()

original = content

# The transform line was broken - missing closing ')',
# It currently reads: transform: 'scale(' + (1 + kenBurnsSpeed * 0.005) + ',
# Should be: transform: 'scale(' + (1 + kenBurnsSpeed * 0.005) + ')',
content = content.replace(
    "transform: 'scale(' + (1 + kenBurnsSpeed * 0.005) + ',",
    "transform: 'scale(' + (1 + kenBurnsSpeed * 0.005) + ')',"
)
print(f"Fixed transform: {'+' in content.split('transform')[1][:50] if 'transform' in content else 'not found'}")

# The style block is malformed with orphaned }} on its own line
# Current: "filter: filterStyle\n                                                \n\n                                                    }}"
# Should be: proper inline style closure
# Let's look for the specific pattern and fix it

# First fix: remove double blank line before }}
content = content.replace(
    'filter: filterStyle\n                                                \n\n                                                    }}',
    'filter: filterStyle\n                                                    }}'
)

# Second fix: if the transform line still has trailing comma issue, fix it
# The style block should be:
# style={{
#     backgroundImage: "...",
#     transform: 'scale(' + (1 + kenBurnsSpeed * 0.005) + ')',
#     filter: filterStyle
# }}
# NOT split across weird lines

# Let's verify the line count change
if content != original:
    old_lines = original.count('\n')
    new_lines = content.count('\n')
    with open(path, 'w') as f:
        f.write(content)
    print(f"Fixed! Wrote changes. Lines: {old_lines} -> {new_lines}")
else:
    print("No changes needed")