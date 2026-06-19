#!/usr/bin/env python3
import re

path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    lines = f.readlines()

print(f"Original lines: {len(lines)}")

# Process each line and fix template literals inside JSX style={} blocks
# Track when we're inside a style={{ block
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this line opens a style={{ block
    if 'style={{' in line:
        new_lines.append(line)
        i += 1
        # Continue processing lines until we close the style block
        brace_depth = line.count('{') - line.count('}')
        while i < len(lines) and brace_depth > 0:
            line = lines[i]
            
            # Check for template literals in this line
            if '`' in line:
                # Single-line template literal with % - replace with string concat
                # Pattern: `something ${expr}%` or `something ${expr}s` or similar
                if '${' in line:
                    # Check if this is a closing line of multi-line template
                    # A multi-line template closing has only backtick and spaces
                    stripped = line.strip()
                    if stripped == '`' or stripped.startswith('`'):
                        # This is a closing backtick of multi-line template
                        # Find the opening backtick line above
                        # We need to go back and replace the filter: ` with filter: filterStyle
                        # Find the most recent "filter: `" line and replace just "filter: `"
                        # Actually, we already replaced filter: ` in the previous iteration
                        pass
                    
                    # Single-line template with ${...} - replace
                    # Pattern: transform: `scale(${...})` or backgroundSize: `${...}px ${...}px`
                    orig_line = line
                    
                    # transform: `scale(${1 + (kenBurnsSpeed * 0.005)})`,
                    if 'transform: `' in line and 'scale(${' in line:
                        line = line.replace(
                            '`scale(${1 + (kenBurnsSpeed * 0.005)})`',
                            "'scale(' + (1 + kenBurnsSpeed * 0.005) + ')'"
                        )
                        print(f"Line {i+1}: Fixed transform template")
                    
                    # backgroundSize: `${10 - (grainDensity * 0.08)}px ${10 - (grainDensity * 0.08)}px`,
                    elif 'backgroundSize: `' in line and 'px' in line:
                        line = line.replace(
                            '`${10 - (grainDensity * 0.08)}px ${10 - (grainDensity * 0.08)}px`',
                            "(10 - grainDensity * 0.08) + 'px ' + (10 - grainDensity * 0.08) + 'px'"
                        )
                        print(f"Line {i+1}: Fixed backgroundSize template")
                    
                    # width: `${job.progress || 0}%`
                    elif 'width: `' in line and 'progress' in line and '%' in line:
                        line = line.replace(
                            '`${job.progress || 0}%`',
                            "(job.progress || 0) + '%'"
                        )
                        print(f"Line {i+1}: Fixed width template")
                    
                    # left: `${x}%`, or top: `${y}%`,
                    elif 'left: `' in line and '${x}%' in line:
                        line = line.replace('`${x}%`', "x + '%'")
                        print(f"Line {i+1}: Fixed left template")
                    elif 'top: `' in line and '${y}%' in line:
                        line = line.replace('`${y}%`', "y + '%'")
                        print(f"Line {i+1}: Fixed top template")
                    
                    # animationDelay: `${idx * 0.3}s`
                    elif 'animationDelay: `' in line and 'idx * 0.3' in line:
                        line = line.replace(
                            '`${idx * 0.3}s`',
                            "idx * 0.3 + 's'"
                        )
                        print(f"Line {i+1}: Fixed animationDelay template")
                    
                    # height: `${h * 10}%`
                    elif 'height: `' in line and 'h * 10' in line and '%' in line:
                        line = line.replace(
                            '`${h * 10}%`',
                            "h * 10 + '%'"
                        )
                        print(f"Line {i+1}: Fixed height template")
                
                # Check if this line is the OPENING of multi-line filter template
                # filter: ` then next lines have contrast, sepia, etc.
                elif 'filter: `' in line and i + 1 < len(lines):
                    # Check if next non-empty line has the filter content
                    if i + 1 < len(lines) and 'contrast(' in lines[i+1]:
                        # This is the opening of multi-line filter
                        # Replace "filter: `" with "filter: filterStyle"
                        line = line.replace('filter: `', 'filter: filterStyle')
                        print(f"Line {i+1}: Fixed filter opening (multi-line)")
                        
                        # Find the closing backtick line and remove it
                        # It should be a few lines later
                        j = i + 1
                        while j < len(lines):
                            if lines[j].strip() == '`' or lines[j].strip().startswith('`'):
                                # This is the closing line - remove it
                                print(f"Line {j+1}: Removing filter closing backtick")
                                # Replace the line with empty or just indentation
                                lines[j] = ''
                                break
                            j += 1
                        # We still need to add useMemo for filterStyle
                        # It will be added after fixing all lines
            
            new_lines.append(line)
            brace_depth += line.count('{') - line.count('}')
            i += 1
    else:
        new_lines.append(line)
        i += 1

# Now add the useMemo for filterStyle before the component's return statement
# Find the right place - after all the useState hooks, before any other useMemo
output = ''.join(new_lines)

# Find insertion point - after the last useState
# Look for "const [grainDensity" which is around line 107
marker = "    const [grainDensity, setGrainDensity] = useState<number>(20);"
idx = output.find(marker)
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
    output = output[:insert_at] + useMemo_code + output[insert_at:]
    print("Added filterStyle useMemo")
else:
    print("WARNING: Could not find grainDensity insertion point!")

with open(path, 'w') as f:
    f.write(output)

# Verify
with open(path) as f:
    verify = f.read()
new_lines_v = verify.split('\n')
print(f"\nFinal lines: {len(new_lines_v)}")
print("\nRemaining backtick lines:")
for i, line in enumerate(new_lines_v, 1):
    if '`' in line:
        print(f"  Line {i}: {repr(line.strip()[:150])}")