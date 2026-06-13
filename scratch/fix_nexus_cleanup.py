#!/usr/bin/env python3

path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    content = f.read()

original = content

# ISSUE 1: Remove the partially-removed multi-line filter block
# The block has "filter: filterStyle" on one line, and then lines with contrast(, sepia(, etc. that weren't removed
# We need to remove lines from "filter: filterStyle" through the "grayscale(...)" line
# Find the block and remove it entirely

# First, let's find what remains of the multi-line filter
# The filter: filterStyle line is followed by lines with contrast, sepia, hue-rotate, grayscale
# We need to remove ALL of these lines and keep only "filter: filterStyle" on one line

# Find the block starting with "filter: filterStyle"
filter_start = content.find('                                                        filter: filterStyle')
if filter_start >= 0:
    # Find the end - after grayscale(...)% line, there's a blank line then backgroundImage
    # Look for the line after grayscale that has something like: grayscale(0%)` or similar
    # Actually looking at original: grayscale(${gray}%)\n                                                        `
    # So after filter: filterStyle we have lines with contrast(, sepia(, hue-rotate(, grayscale(
    # And then a line with just ` (the closing backtick that was already removed)
    
    # Find the next line with `grayscale(` and remove up to the blank line after it
    gray_line_start = content.find('                                                            grayscale(', filter_start)
    if gray_line_start >= 0:
        # Find the end of this block - after grayscale line there's a blank line with spaces
        # then ` (which was the closing backtick - already removed but left blank)
        # The block ends before "                                                "
        block_start = filter_start
        # Find the blank line after grayscale line
        after_gray = content.find('\n                                                        \n', gray_line_start)
        if after_gray >= 0:
            block_end = after_gray + len('\n                                                        \n')
            old_block = content[block_start:block_end]
            # Replace with just "filter: filterStyle" on one line + blank line
            new_block = '                                                        filter: filterStyle\n                                                \n'
            content = content.replace(old_block, new_block)
            print("Fixed multi-line filter block removal")
        else:
            print("Could not find end of filter block (after grayscale)")
    else:
        print("Could not find grayscale line")
else:
    print("Could not find filter: filterStyle line")

# ISSUE 2: Move the filterStyle useMemo to after contrast declaration
# First, find where the filterStyle useMemo currently is
useMemo_old = """
    // Filter style computed from style customizer state
    const filterStyle = useMemo(() => {
        const preset = selectedStylePreset;
        const temp = colorTemp / 100;
        const contrastVal = 1 + (contrast - 50) / 50;
        const sepiaVal = temp * 30;
        return `contrast(${contrastVal.toFixed(2)}) sepia(${sepiaVal.toFixed(1)}%)`;
    }, [selectedStylePreset, colorTemp, contrast]);
"""

# Remove it from current location
if useMemo_old in content:
    content = content.replace(useMemo_old, '')
    print("Removed filterStyle useMemo from old location")
else:
    print("Could not find useMemo at old location")
    # Try without leading newline
    useMemo_old2 = useMemo_old.lstrip()
    if useMemo_old2 in content:
        content = content.replace(useMemo_old2, '')
        print("Removed filterStyle useMemo (no leading newline)")
    else:
        print("WARNING: Could not find useMemo to remove")

# Find the right insertion point - after contrast useState
marker = "    const [contrast, setContrast] = useState<number>(50);"
idx = content.find(marker)
if idx >= 0:
    insert_at = idx + len(marker)
    useMemo_new = """

    // Filter style computed from style customizer state
    const filterStyle = useMemo(() => {
        const preset = selectedStylePreset;
        const temp = colorTemp / 100;
        const contrastVal = 1 + (contrast - 50) / 50;
        const sepiaVal = temp * 30;
        return `contrast(${contrastVal.toFixed(2)}) sepia(${sepiaVal.toFixed(1)}%)`;
    }, [selectedStylePreset, colorTemp, contrast]);
"""
    content = content[:insert_at] + useMemo_new + content[insert_at:]
    print("Inserted filterStyle useMemo after contrast declaration")
else:
    print("WARNING: Could not find contrast useState marker!")

if content != original:
    with open(path, 'w') as f:
        f.write(content)
    print("\nFile written!")
    
    # Verify
    with open(path) as f:
        verify = f.read()
    lines = verify.split('\n')
    print(f"Total lines: {len(lines)}")
    
    # Check for remaining template literals in style={} blocks
    print("\nRemaining template literals:")
    for i, line in enumerate(lines, 1):
        if '`' in line:
            print(f"  Line {i}: {repr(line.strip()[:150])}")
    
    # Check filterStyle is defined and used correctly
    print("\nfilterStyle definition check:")
    if 'const filterStyle = useMemo' in verify:
        print("  filterStyle useMemo defined: YES")
    else:
        print("  filterStyle useMemo defined: NO")
    if 'filter: filterStyle' in verify:
        print("  filter: filterStyle used: YES")
    else:
        print("  filter: filterStyle used: NO")
    
    # Check order - filterStyle should come after colorTemp and contrast
    colorTemp_pos = verify.find('const [colorTemp')
    contrast_pos = verify.find('const [contrast')
    filterStyle_pos = verify.find('const filterStyle = useMemo')
    
    if colorTemp_pos >= 0 and contrast_pos >= 0 and filterStyle_pos >= 0:
        print("\nOrder check (should be: colorTemp < contrast < filterStyle):")
        print(f"  colorTemp pos: {colorTemp_pos}")
        print(f"  contrast pos: {contrast_pos}")
        print(f"  filterStyle pos: {filterStyle_pos}")
        if colorTemp_pos < contrast_pos < filterStyle_pos:
            print("  ORDER: CORRECT")
        else:
            print("  ORDER: INCORRECT")
else:
    print("\nNo changes!")