#!/usr/bin/env python3
"""
Validate that test file patch() targets use the correct base_* singleton naming.

Detects the pattern where a test patches an alias name like:
    patch("src.services.langchain.service.langchain_service")
when the actual module-level export is:
    base_langchain_service = LangChainService()

Such mismatches cause the patch to be a no-op, meaning real API calls or
database queries will be attempted instead of being mocked.

Usage:
    python scripts/validate_patch_targets.py              # check only
    python scripts/validate_patch_targets.py --fix         # auto-fix mismatches
    python scripts/validate_patch_targets.py --staged      # check only staged test files
    python scripts/validate_patch_targets.py --verbose     # show all singletons found
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Matches module-level assignments like:
#   base_langchain_service = LangChainService()
#   base_unified_llm_service = UnifiedLLMService()
BASE_ASSIGN_RE = re.compile(r'^base_(\w+)\s*=')

# Matches patch("some.path.attr") calls
PATCH_STRING_RE = re.compile(r"patch\(\s*['\"]([^'\"]+)['\"]\s*\)")

# Suffixes that typically indicate a service/manager singleton
SERVICE_LIKE_SUFFIXES = (
    '_service', '_engine', '_manager', '_client', '_publisher',
    '_scanner', '_generator', '_orchestrator', '_controller',
    '_monitor', '_processor', '_mixer', '_compiler', '_scheduler',
    '_adapter', '_planner', '_simulator', '_critic', '_strategist',
    '_loop', '_hub', '_sentinel', '_detector', '_analyst', '_bridge',
    '_pipeline', '_optimizer',
)


def normalize_module(path: str) -> str:
    """Normalize a Python dotted module path to match our singleton index.
    
    Both 'src.services.foo.bar' and 'services.foo.bar' are mapped to
    the canonical 'src.services.foo.bar' form.
    """
    if not path.startswith('src.'):
        # Try prepending src. -- some tests use the shorter path
        candidate = 'src.' + path
        # Return the canonical form; the caller will check both
        return candidate
    return path


def collect_singletons() -> Dict[str, Dict[str, str]]:
    """Walk src/ and collect all base_X module-level singleton declarations.
    
    Returns:
        module_map: canonical_module_path -> { short_name: full_base_name }
        e.g. "src.services.langchain.service" -> {"langchain_service": "base_langchain_service"}
    """
    module_map: Dict[str, Dict[str, str]] = {}

    for root, dirs, files in os.walk(SRC_DIR):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']

        for f in files:
            if not f.endswith('.py'):
                continue
            # Skip test files (they're consumers, not producers of singletons)
            if f.startswith('test_'):
                continue

            filepath = os.path.join(root, f)
            rel_path = os.path.relpath(filepath, PROJECT_ROOT)
            mod_path = rel_path.replace('.py', '').replace('/', '.')

            try:
                with open(filepath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except (OSError, UnicodeDecodeError):
                continue

            for line in content.splitlines():
                m = BASE_ASSIGN_RE.match(line.strip())
                if m:
                    short_name = m.group(1)            # e.g. "langchain_service"
                    full_name = f"base_{short_name}"    # e.g. "base_langchain_service"
                    if mod_path not in module_map:
                        module_map[mod_path] = {}
                    module_map[mod_path][short_name] = full_name

    return module_map


def find_mismatches(
    module_map: Dict[str, Dict[str, str]],
    singletons_short: Dict[str, str],
) -> List[Dict]:
    """Scan all test files for patch() targets that mismatch the base_ naming.
    
    Args:
        module_map: full module_map from collect_singletons()
        singletons_short: flat map of short_name -> canonical_module.full_name
                          e.g. "langchain_service" -> "src.services.langchain.service.base_langchain_service"
    
    Returns:
        List of issue dicts with keys: test_file, line, patch_target, expected
    """
    issues: List[Dict] = []

    for root, dirs, files in os.walk(SRC_DIR):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']

        for f in files:
            if not f.endswith('.py') or not f.startswith('test_'):
                continue

            filepath = os.path.join(root, f)
            rel_path = os.path.relpath(filepath, PROJECT_ROOT)

            try:
                with open(filepath, 'r', encoding='utf-8') as fh:
                    lines = fh.readlines()
            except (OSError, UnicodeDecodeError):
                continue

            for lineno, raw_line in enumerate(lines, 1):
                for m in PATCH_STRING_RE.finditer(raw_line):
                    target = m.group(1)
                    _check_patch_target(target, rel_path, lineno, module_map, singletons_short, issues)

    return issues


def _check_patch_target(
    target: str,
    test_file: str,
    lineno: int,
    module_map: Dict[str, Dict[str, str]],
    singletons_short: Dict[str, str],
    issues: List[Dict],
):
    """Examine a single patch string and record an issue if it's a naming mismatch."""
    # Split "a.b.c.attr" into module parts + attribute
    *parts, attr = target.rsplit('.', 1)
    if not parts:
        return  # unusual, skip
    module_path = '.'.join(parts)

    # Skip if attribute already uses the base_ prefix
    if attr.startswith('base_'):
        return

    # Skip short names that don't look service-like (prevents false positives
    # on things like patch("redis.Redis"), patch("os.getenv"), etc.)
    if not attr.endswith(SERVICE_LIKE_SUFFIXES):
        # Also accept if the short name appears in the singleton index
        if attr not in singletons_short:
            return

    # --- Check the canonical (src.) module path ---
    canonical = normalize_module(module_path)
    if canonical in module_map:
        for short_name, full_name in module_map[canonical].items():
            if short_name == attr:
                expected = f"{canonical}.{full_name}"
                issues.append({
                    'test_file': test_file,
                    'line': lineno,
                    'patch_target': target,
                    'expected': expected,
                })
                return  # one issue per patch target

    # --- Also check the raw (non-src.) module path ---
    if canonical != module_path:
        if module_path in module_map:
            for short_name, full_name in module_map[module_path].items():
                if short_name == attr:
                    expected = f"{module_path}.{full_name}"
                    issues.append({
                        'test_file': test_file,
                        'line': lineno,
                        'patch_target': target,
                        'expected': expected,
                    })
                    return

    # No flat fallback check here. Module-path lookups above are sufficient
    # for all real cases. A flat index lookup across modules could produce
    # false positives if multiple modules share the same short name.


def print_report(issues: List[Dict], verbose: bool = False) -> bool:
    """Print validation results. Returns True if no issues."""
    if not issues:
        print("✅  All test patch targets correctly use base_* singleton naming.")
        return True

    print(f"❌  Found {len(issues)} mismatched patch target(s):\n")
    for issue in sorted(issues, key=lambda x: (x['test_file'], x['line'])):
        print(f"  {issue['test_file']}:{issue['line']}")
        print(f"      patch(\"{issue['patch_target']}\")")
        print(f"      → should be: patch(\"{issue['expected']}\")")
        print()

    return False


def fix_issues(issues: List[Dict]) -> int:
    """Auto-fix mismatched patch targets in-place. Returns count of files modified."""
    if not issues:
        return 0

    by_file: Dict[str, List[Dict]] = {}
    for issue in issues:
        by_file.setdefault(issue['test_file'], []).append(issue)

    fixed_count = 0
    for filepath, file_issues in sorted(by_file.items()):
        abs_path = PROJECT_ROOT / filepath
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            print(f"  ⚠ Could not read {filepath}: {e}", file=sys.stderr)
            continue

        # Sort by line descending to avoid offset issues
        applied = 0
        for issue in sorted(file_issues, key=lambda x: -x['line']):
            old_target = issue['patch_target']
            new_target = issue['expected']
            # Use string replace on the full line context for safety
            old_str = f'patch("{old_target}")'
            new_str = f'patch("{new_target}")'
            if old_str in content:
                content = content.replace(old_str, new_str, 1)
                applied += 1

        if applied > 0:
            try:
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"  ✓ {filepath} — {applied} fix(es) applied")
            except OSError as e:
                print(f"  ⚠ Could not write {filepath}: {e}", file=sys.stderr)

    return fixed_count


def _get_staged_test_files() -> List[str]:
    """Get paths of staged test files (relative to PROJECT_ROOT)."""
    import subprocess
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        print("⚠  Could not list staged files (not a git repo?)", file=sys.stderr)
        return []

    staged = []
    for line in result.stdout.splitlines():
        line = line.strip()
        # Only consider test files under src/
        if line.startswith("src/") and line.endswith(".py"):
            filename = os.path.basename(line)
            if filename.startswith("test_"):
                staged.append(line)
    return staged


def find_mismatches_in_files(
    file_paths: List[str],
    module_map: Dict[str, Dict[str, str]],
    singletons_short: Dict[str, str],
) -> List[Dict]:
    """Like find_mismatches(), but only scans the given file paths."""
    issues: List[Dict] = []

    for rel_path in file_paths:
        abs_path = PROJECT_ROOT / rel_path
        try:
            with open(abs_path, 'r', encoding='utf-8') as fh:
                lines = fh.readlines()
        except (OSError, UnicodeDecodeError):
            continue

        for lineno, raw_line in enumerate(lines, 1):
            for m in PATCH_STRING_RE.finditer(raw_line):
                target = m.group(1)
                _check_patch_target(target, rel_path, lineno, module_map, singletons_short, issues)

    return issues


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate test patch() targets use correct base_* singleton naming"
    )
    parser.add_argument('--fix', action='store_true', help='Auto-fix mismatched patch targets')
    parser.add_argument('--staged', action='store_true', help='Only check staged test files (git)')
    parser.add_argument('--verbose', action='store_true', help='Show all singletons found')
    args = parser.parse_args()

    print("🔍  Scanning for base_* singleton declarations...", end=' ')
    module_map = collect_singletons()
    total_singletons = sum(len(v) for v in module_map.values())
    print(f"found {total_singletons} singletons in {len(module_map)} modules")

    # Build a flat short_name -> canonical_full_path index for fast lookup
    singletons_short: Dict[str, str] = {}
    for mod_path, short_names in module_map.items():
        for short_name, full_name in short_names.items():
            canonical_path = f"{mod_path}.{full_name}"
            # Prefer the src.-prefixed path as canonical
            if short_name not in singletons_short:
                singletons_short[short_name] = canonical_path

    if args.verbose:
        print("\n--- Singleton Index ---")
        for mod_path in sorted(module_map):
            for short_name, full_name in sorted(module_map[mod_path].items()):
                print(f"  {mod_path}.{full_name}")
        print()

    if args.staged:
        file_paths = _get_staged_test_files()
        if not file_paths:
            print("📋  No staged test files to validate.")
            sys.exit(0)
        print(f"📋  Scanning {len(file_paths)} staged test file(s)...", end=' ')
        issues = find_mismatches_in_files(file_paths, module_map, singletons_short)
    else:
        print("🔍  Scanning test files for patch() targets...", end=' ')
        issues = find_mismatches(module_map, singletons_short)

    count = len(issues)
    print(f"found {count} issue(s)" if count else "done")

    success = print_report(issues, verbose=args.verbose)

    if args.fix and issues:
        print("🔧  Auto-fixing mismatches...")
        fixed = fix_issues(issues)
        print(f"✅  Fixed {fixed} file(s).")
        success = True
    elif not success:
        print("💡  Tip: run with --fix to auto-correct all mismatches.")

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
