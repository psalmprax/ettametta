#!/usr/bin/env python3

path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    content = f.read()

original = content

# The <style jsx global>{`...`}</style> block is a known Turbopack-unfriendly pattern
# Replace it with a plain <style> tag or move to CSS module
# Find the style jsx global block
style_start = '<style jsx global>{`'
style_end = '`}</style>'

start_idx = content.find(style_start)
if start_idx >= 0:
    end_idx = content.find(style_end, start_idx)
    if end_idx >= 0:
        end_idx += len(style_end)
        old_block = content[start_idx:end_idx]
        
        # Extract the CSS content (between `{`` and `}`)
        css_start = old_block.find('{`') + 2
        css_end = old_block.find('`}', css_start)
        css_content = old_block[css_start:css_end]
        
        # Replace with plain style tag (no jsx, no template literal)
        new_block = f'''<style>{css_content}</style>'''
        
        content = content.replace(old_block, new_block)
        print("Replaced <style jsx global> with plain <style>")
        print(f"CSS content length: {len(css_content)}")
    else:
        print("Could not find style jsx global end")
else:
    print("Could not find style jsx global start")

if content != original:
    with open(path, 'w') as f:
        f.write(content)
    print("File written!")
    
    # Verify
    with open(path) as f:
        verify = f.read()
    if '<style jsx global>' in verify:
        print("WARNING: <style jsx global> still exists!")
    else:
        print("<style jsx global> removed: YES")
    if '<style>' in verify:
        print("Plain <style> present: YES")
else:
    print("No changes!")