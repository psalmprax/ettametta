#!/usr/bin/env python3

path = '/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/page.tsx'
with open(path, 'r') as f:
    content = f.read()

# Fix the dependency array - remove hueShift and colorEffect which don't exist
old = "    }, [selectedStylePreset, colorTemp, contrast, hueShift, colorEffect]);"
new = "    }, [selectedStylePreset, colorTemp, contrast]);"
if old in content:
    content = content.replace(old, new)
    print("Fixed dependency array - removed hueShift and colorEffect")
else:
    print("Could not find the dependency array to fix")

with open(path, 'w') as f:
    f.write(content)
print("File written")