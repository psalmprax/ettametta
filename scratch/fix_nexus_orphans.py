#!/usr/bin/env python3
"""Remove orphaned filter CSS function lines from nexus/page.tsx"""


path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    content = f.read()

original = content

# The multi-line filter block was partially removed - the opening `filter: `` was replaced
# with `filter: filterStyle` and the closing backtick line was removed, but the intermediate
# CSS function lines are still there. Remove them.

# These orphaned lines start with lots of spaces and contain CSS function calls
orphaned_patterns = [
    r'\n[ ]*contrast\rét\raisé',  # indent + contrast(...)

    # Actually let me use the exact content from the file
]

# More robust: find the style block context and remove orphaned CSS lines
# Look for the pattern: after "filter: filterStyle" followed by indented CSS lines

# First, let's find and remove orphaned contrast line
orphaned_contrast = '\n                                                            contrast('
orphaned_sepia = '\n                                                            sepia('
orphaned_hue = '\n                                                            hue-rotate('
orphaned_gray = '\n                                                            grayscale('

removed = 0
for pattern in [orphaned_contrast, orphaned_sepia, orphaned_hue, orphaned_gray]:
    if pattern in content:
        content = content.replace(pattern, '\n')
        removed += 1
        print(f"Removed: {repr(pattern[:50])}")

# Also fix the style block that has "transform: 'scale(' + ... + ','\n                                                filter: filterStyle"
# followed by orphaned lines and then "}}" - remove the blank line issue

# If we have "filter: filterStyle\n                                                \n\n                                                    }}"
# we want "filter: filterStyle\n                                                    }}"

# Fix duplicate blank lines in style block
content = content.replace('filter: filterStyle\n                                                \n\n                                                    }}',
                          'filter: filterStyle\n                                                    }}')

if content != original:
    with open(path, 'w') as f:
        f.write(content)
    print("\nFixed! Wrote changes.")
    print(f"Removed {removed} orphaned lines")
else:
    print("No changes needed")