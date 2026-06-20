#!/usr/bin/env python3
"""Replace remaining duplicated login blocks with shared loginAsTestUser helper.
V3: Fixed quote matching."""
import re
import glob

# Pattern with single double-quotes (matching actual file content)
LOGIN_BLOCK = re.compile(
    r"(\s*)test\.beforeEach\(async \(\{ page \}\) => \{[^\n]*\n"
    r"\s*//?[^\n]*\n?"  # optional comment line
    r"\s*await page\.goto\('/login'\);\s*\n"
    r"\s*await page\.fill\('input\[name=\"email\"\]', 'test@example\.com'\);\s*\n"
    r"\s*await page\.fill\('input\[name=\"password\"\]', 'testpassword'\);\s*\n"
    r"\s*await page\.click\('button\[type=\"submit\"\]'\);\s*\n"
    r"\s*await page\.waitForURL\('/'\);\s*\n"
    r"\s*\}\);",
    re.MULTILINE,
)

# Also handle inline login blocks (not in beforeEach)
INLINE_LOGIN = re.compile(
    r"(\s*)// ?[Ll]ogin before.*\n"
    r"\s*await page\.goto\('/login'\);\s*\n"
    r"\s*await page\.fill\('input\[name=\"email\"\]', 'test@example\.com'\);\s*\n"
    r"\s*await page\.fill\('input\[name=\"password\"\]', 'testpassword'\);\s*\n"
    r"\s*await page\.click\('button\[type=\"submit\"\]'\);\s*\n"
    r"\s*await page\.waitForURL\('/'\);\s*\n",
    re.MULTILINE,
)

def get_rel_import(filepath: str) -> str:
    parts = filepath.split("/")
    tests_idx = parts.index("tests")
    depth = len(parts) - tests_idx - 2
    prefix = "../" * (depth + 1)
    return f"import {{ loginAsTestUser }} from '{prefix}helpers/auth';"

count = 0
files_modified = 0

for f in sorted(glob.glob("src/tests/e2e/tests/**/*.spec.ts", recursive=True)):
    try:
        content = open(f).read()
    except FileNotFoundError:
        continue
    
    original = content
    
    # Replace beforeEach login blocks
    def beforeEach_replacer(m):
        indent = m.group(1)
        return f"{indent}test.beforeEach(async ({{ page }}) => {{\n{indent}    await loginAsTestUser(page);\n{indent}}});"
    
    content = LOGIN_BLOCK.sub(beforeEach_replacer, content)
    
    # Replace inline login blocks (inside test bodies)
    def inline_replacer(m):
        indent = m.group(1)
        return f"{indent}await loginAsTestUser(page);\n"
    
    content = INLINE_LOGIN.sub(inline_replacer, content)
    
    if content == original:
        continue
    
    # Add import if not already present
    if "loginAsTestUser" not in original:
        rel = get_rel_import(f)
        lines = content.split("\n")
        last_import = 0
        for i, line in enumerate(lines):
            if line.startswith("import "):
                last_import = i
        lines.insert(last_import + 1, rel)
        content = "\n".join(lines)
    
    block_count = content.count("loginAsTestUser") - original.count("loginAsTestUser")
    
    with open(f, "w") as fh:
        fh.write(content)
    
    count += max(block_count, 1)
    files_modified += 1
    print(f"  Updated {f} ({max(block_count, 1)} blocks)")

print(f"\nTotal: {count} login blocks replaced in {files_modified} files")
