#!/usr/bin/env python3
"""Fix deprecation warnings across the codebase.

Handles:
1. datetime.utcnow() → datetime.now(timezone.utc) / datetime.datetime.now(datetime.timezone.utc)
2. pydantic class Config → model_config = ConfigDict()
"""
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_python_files(root_dir):
    """Get all .py files recursively, skipping .git, venv, node_modules."""
    matches = []
    for root, dirs, files in os.walk(root_dir):
        skip = {'__pycache__', '.git', 'venv', 'node_modules', 'env', '.venv'}
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if f.endswith('.py'):
                matches.append(os.path.join(root, f))
    return matches


def fix_datetime_utcnow(content: str) -> tuple[str, bool]:
    """Replace datetime.utcnow() with timezone-aware equivalents."""
    original = content
    has_module_import = bool(re.search(r'^import datetime\b', content, re.MULTILINE))
    has_from_import = bool(re.search(r'^from datetime import', content, re.MULTILINE))

    if not has_module_import and not has_from_import:
        # Suspect datetime.utcnow but no import — skip, could be dynamic
        if 'datetime.utcnow' in content or 'datetime.datetime.utcnow' in content:
            print("  ⚠️  'datetime.utcnow' found but no datetime import detected — needs manual check")
        return content, False

    if has_module_import:
        # Pattern: import datetime → use datetime.datetime.now(datetime.timezone.utc)
        # datetime.utcnow() → datetime.datetime.now(datetime.timezone.utc)
        content = re.sub(
            r'datetime\.datetime\.utcnow\(\)',
            'datetime.datetime.now(datetime.timezone.utc)',
            content
        )
        # Bare datetime.utcnow() (module-level call)
        content = re.sub(
            r'(?<!\w)(?<!\.)datetime\.utcnow\(\)',
            'datetime.datetime.now(datetime.timezone.utc)',
            content
        )
        # datetime.utcnow (bare reference, e.g. default=datetime.utcnow)
        content = re.sub(
            r'(default|onupdate)=datetime\.utcnow(?![(\w])',
            lambda m: f'{m.group(1)}=lambda: datetime.datetime.now(datetime.timezone.utc)',
            content
        )
    elif has_from_import:
        # Pattern: from datetime import ... → use datetime.now(timezone.utc)
        # Add timezone to import if not present
        def add_timezone_import(m):
            existing = m.group(1)
            if 'timezone' not in existing:
                return f'from datetime import {existing}, timezone'
            return m.group(0)

        content = re.sub(
            r'^from datetime import (.+)$',
            add_timezone_import,
            content,
            count=1,
            flags=re.MULTILINE
        )

        # lambda: datetime.utcnow() → lambda: datetime.now(timezone.utc)
        content = content.replace('lambda: datetime.utcnow()', 'lambda: datetime.now(timezone.utc)')

        # default=datetime.utcnow or onupdate=datetime.utcnow (bare ref)
        content = re.sub(
            r'(default|onupdate)=datetime\.utcnow(?![(\w])',
            lambda m: f'{m.group(1)}=lambda: datetime.now(timezone.utc)',
            content
        )

        # default_factory=datetime.utcnow → default_factory=lambda: datetime.now(timezone.utc)
        content = content.replace('default_factory=datetime.utcnow', 'default_factory=lambda: datetime.now(timezone.utc)')

        # datetime.utcnow() → datetime.now(timezone.utc)
        content = content.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')

        # datetime.datetime.utcnow() → datetime.datetime.now(datetime.timezone.utc) 
        # (for files with both import datetime and from datetime import)
        content = content.replace('datetime.datetime.utcnow()', 'datetime.datetime.now(datetime.timezone.utc)')

    return content, content != original


def fix_class_config(content: str) -> tuple[str, bool]:
    """Replace pydantic v1-style 'class Config:' with model_config = ConfigDict().

    Only fixes classes inside files that import from pydantic.
    """
    original = content
    is_pydantic_file = bool(re.search(r'from\s+pydantic\s+import', content)) or \
                       bool('pydantic_settings' in content)

    if not is_pydantic_file:
        return content, False

    if 'class Config:' not in content:
        return content, False

    # Check if ConfigDict is already imported
    if 'ConfigDict' not in content:
        content = re.sub(
            r'^from\s+pydantic\s+import\s+(.+)$',
            lambda m: f'from pydantic import {m.group(1)}, ConfigDict'
                     if 'ConfigDict' not in m.group(1) else m.group(0),
            content,
            count=1,
            flags=re.MULTILINE
        )

        # Also handle pydantic_settings imports
        content = re.sub(
            r'^from\s+pydantic_settings\s+import\s+(.+)$',
            lambda m: f'from pydantic_settings import {m.group(1)}, ConfigDict'
                     if 'ConfigDict' not in m.group(1) else m.group(0),
            content,
            count=1,
            flags=re.MULTILINE
        )

    # Replace class Config: blocks with model_config = ConfigDict()
    # Match: "    class Config:\n        attr=val\n        attr=val\n"
    # The class Config is at some indentation level
    def replace_config_block(match):
        indent = match.group(1)
        body = match.group(2)
        attrs = []
        for line in body.strip().split('\n'):
            line = line.strip()
            if '=' in line:
                key, val = line.split('=', 1)
                attrs.append(f"{key.strip()}={val.strip()}")

        if attrs:
            config_str = ', '.join(attrs)
            return f'{indent}model_config = ConfigDict({config_str})\n'
        else:
            return f'{indent}model_config = ConfigDict()\n'

    content = re.sub(
        r'(\s+)class\s+Config:\n((?:\1\s+\w+\s*=\s*.+\n?)*)',
        replace_config_block,
        content,
        re.MULTILINE
    )

    return content, content != original


def process_file(filepath: str) -> int:
    """Process a single file. Returns 1 if changed, 0 if not."""
    relpath = os.path.relpath(filepath, PROJECT_ROOT)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"  ❌ Error reading {relpath}: {e}")
        return 0

    orig = content

    # Fix 1: datetime.utcnow
    content, changed_utc = fix_datetime_utcnow(content)

    # Fix 2: pydantic class Config
    content, changed_config = fix_class_config(content)

    if content == orig:
        return 0

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        changes = []
        if changed_utc:
            changes.append('datetime.utcnow')
        if changed_config:
            changes.append('class Config')
        print(f"  ✓ {relpath} — fixed: {', '.join(changes)}")
        return 1
    except Exception as e:
        print(f"  ❌ Error writing {relpath}: {e}")
        return 0


def main():
    target_dirs = sys.argv[1:] if len(sys.argv) > 1 else [
        os.path.join(PROJECT_ROOT, 'src'),
        os.path.join(PROJECT_ROOT, 'scripts'),
        os.path.join(PROJECT_ROOT, 'scratch'),
    ]

    files = []
    for d in target_dirs:
        if os.path.isdir(d):
            files.extend(get_python_files(d))
        elif os.path.isfile(d):
            files.append(d)

    if not files:
        print("No Python files found in the specified paths.")
        return 1

    # First, find files that need attention
    files_to_process = []
    for fpath in files:
        relpath = os.path.relpath(fpath, PROJECT_ROOT)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if 'datetime.utcnow' in content or \
           ('class Config:' in content and ('from pydantic' in content or 'pydantic_settings' in content)):
            files_to_process.append(fpath)
            print(f"  → {relpath} needs updates")

    print(f"\nFound {len(files_to_process)} files to process\n")

    changed = 0
    for fpath in files_to_process:
        changed += process_file(fpath)

    print(f"\n{'='*50}")
    print(f"Done! {changed} files updated.")
    return 0 if changed >= 0 else 1


if __name__ == '__main__':
    sys.exit(main())
