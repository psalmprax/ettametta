#!/usr/bin/env python3
"""Properly fix the multi-line filter template in nexus/page.tsx"""

path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    content = f.read()

original = content

# Find the multi-line filter block:
# filter: `
#   contrast(...)
#   sepia(...)
#   hue-rotate(...)
#   grayscale(...)
# `

# Strategy: find "filter: `" then find the line that contains ONLY backtick (the closing)
filter_marker = "filter: `"
filter_start = content.find(filter_marker)
if filter_start < 0:
    print("filter: ` not found at all - already replaced?")
else:
    print(f"Found filter: ` at position {filter_start}")
    
    # Find the line that contains just backtick after the marker
    # The multi-line block starts with "filter: `" and ends with a line that is just "`"
    # Let's search for the closing backtick by looking for a line that's just "`"
    search_from = filter_start + len(filter_marker)
    
    # Method: find the next newline after filter_start, then search from there for a line that is just "`"
    first_newline = content.find('\n', filter_start)
    if first_newline > 0:
        # Search for a line that starts with spaces then "`" after the first newline
        # The pattern is: whitespace followed by backtick at the start of a line
        search_pos = first_newline
        max_search = filter_start + 2000  # safety limit
        
        found_closing = False
        while search_pos < max_search:
            # Look for backtick
            bt_pos = content.find('`', search_pos)
            if bt_pos < 0 or bt_pos > max_search:
                break
            
            # Check if this backtick is at the start of a line (possibly with leading whitespace)
            line_start = content.rfind('\n', search_pos, bt_pos) + 1
            line_content = content[line_start:bt_pos].strip()
            
            if line_content == '`':
                # Found closing backtick line!
                print(f"Found closing backtick at position {bt_pos}")
                # The block is from filter_start to bt_pos+1 (inclusive)
                block_to_remove = content[filter_start:bt_pos+1]
                print(f"Block length: {len(block_to_remove)} chars, {block_to_remove.count(chr(10))} lines")
                
                # Replace with single line
                replacement = "filter: filterStyle"
                content = content.replace(block_to_remove, replacement)
                found_closing = True
                print("Multi-line filter block REPLACED!")
                break
            
            search_pos = bt_pos + 1
    
    if not found_closing:
        print("ERROR: Could not find closing backtick for multi-line filter!")

# Write changes
if content != original:
    with open(path, 'w') as f:
        f.write(content)
    print("Wrote changes!")
else:
    print("No changes made")