import os
import re

production_root = "/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src"
excludes = [
    re.compile(r'/__tests__/'),
    re.compile(r'/_rule-fixture\.ts$'),
    re.compile(r'/scratch/'),
    re.compile(r'/test-utils/'),
]

prod_decl_re = re.compile(r'^(type|const|interface)\s+([A-Z][A-Za-z0-9_]*)\b')
marker_phrase = "Module-internal — do not consume from outside."

def count_internal_usages(lines, decl_idx, name):
    pattern = re.compile(r'\b' + re.escape(name) + r'\b')
    count = 0
    for i in range(decl_idx + 1, len(lines)):
        raw = lines[i]
        trimmed = raw.strip()
        if not trimmed:
            continue
        # Skip pure comments
        if re.match(r'^(\*|/\*|\*/|//)', trimmed):
            continue
        # Strip inline comment
        code_only = re.sub(r'//.*$', '', raw)
        if pattern.search(code_only):
            count += 1
    return count

# Walk production files
ts_files = []
for root, dirs, files in os.walk(production_root):
    for file in files:
        if not (file.endswith('.ts') or file.endswith('.tsx')):
            continue
        abs_path = os.path.join(root, file)
        # Check excludes
        if any(rx.search(abs_path) for rx in excludes):
            continue
        ts_files.append(abs_path)

print(f"Found {len(ts_files)} TypeScript files to scan.")

modified_count = 0
for filepath in ts_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    
    new_lines = []
    i = 0
    modified = False
    while i < len(lines):
        ln = lines[i]
        # Skip export or import lines
        if ln.startswith("export ") or ln.startswith("import "):
            new_lines.append(ln)
            i += 1
            continue
            
        m = prod_decl_re.match(ln)
        if m:
            kind, name = m.group(1), m.group(2)
            usages = count_internal_usages(lines, i, name)
            if usages >= 1:
                # Check for marker in the preceding lines
                start_check = max(0, len(new_lines) - 8)
                has_marker = any(marker_phrase in l for l in new_lines[start_check:])
                if not has_marker:
                    new_lines.append("/** " + marker_phrase + " */")
                    modified = True
                    modified_count += 1
                    print(f"Added marker in {os.path.relpath(filepath, production_root)} before `{kind} {name}` (usages={usages})")
        new_lines.append(ln)
        i += 1
        
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

print(f"Done! Modified {modified_count} declarations.")
