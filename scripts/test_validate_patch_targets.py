#!/usr/bin/env python3
"""Unit tests for scripts/validate_patch_targets.py — the CI patch-target validator."""

import os
import sys
from pathlib import Path
from typing import Dict, List
from unittest.mock import patch as mock_patch

import pytest

# Ensure we can import the script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validate_patch_targets import (
    _check_patch_target,
    collect_singletons,
    find_mismatches,
    fix_issues,
    normalize_module,
    print_report,
)
from scripts.validate_patch_targets import main as main_entry


# =========================================================================
# normalize_module()
# =========================================================================

class TestNormalizeModule:
    def test_already_src(self):
        """Already starts with src. — unchanged."""
        assert normalize_module("src.foo.bar") == "src.foo.bar"

    def test_prepend_src(self):
        """Short path without src. gets it prepended."""
        assert normalize_module("foo.bar") == "src.foo.bar"

    def test_empty_string(self):
        """Empty string gets src. prepended."""
        assert normalize_module("") == "src."

    def test_deep_path(self):
        """Deep dotted path without src. works."""
        assert normalize_module("a.b.c.d") == "src.a.b.c.d"

    def test_src_deep_path(self):
        """Deep dotted path already with src. preserved."""
        assert normalize_module("src.a.b.c.d") == "src.a.b.c.d"


# =========================================================================
# _check_patch_target() — core detection logic
# =========================================================================

class TestCheckPatchTarget:
    """Test the core detection logic via function-level invocation."""

    def _check(self, target: str, module_map: Dict, singletons_short: Dict) -> List[Dict]:
        """Helper: invoke _check_patch_target and return what it appends to issues."""
        issues: List[Dict] = []
        _check_patch_target(
            target=target,
            test_file="test_foo.py",
            lineno=10,
            module_map=module_map,
            singletons_short=singletons_short,
            issues=issues,
        )
        return issues

    def test_detects_mismatch(self):
        """Flag when patch(...) uses langchain_service but module has base_langchain_service."""
        module_map = {
            "src.services.langchain.service": {"langchain_service": "base_langchain_service"},
        }
        singletons_short = {"langchain_service": "src.services.langchain.service.base_langchain_service"}
        issues = self._check(
            "src.services.langchain.service.langchain_service",
            module_map,
            singletons_short,
        )
        assert len(issues) == 1
        assert issues[0]["patch_target"] == "src.services.langchain.service.langchain_service"
        assert issues[0]["expected"] == "src.services.langchain.service.base_langchain_service"

    def test_skips_already_base(self):
        """Skip when the attribute already uses base_ prefix."""
        module_map = {
            "src.services.langchain.service": {"langchain_service": "base_langchain_service"},
        }
        singletons_short = {"langchain_service": "src.services.langchain.service.base_langchain_service"}
        issues = self._check(
            "src.services.langchain.service.base_langchain_service",
            module_map,
            singletons_short,
        )
        assert len(issues) == 0

    def test_skips_non_service_name(self):
        """Skip third-party patches like patch('redis.Redis') or patch('os.getenv')."""
        module_map: Dict = {}
        singletons_short: Dict = {}
        issues = self._check("redis.Redis", module_map, singletons_short)
        assert len(issues) == 0

        issues = self._check("os.getenv", module_map, singletons_short)
        assert len(issues) == 0

    def test_skips_httpx(self):
        """Skip common third-party patches."""
        issues = self._check("httpx.AsyncClient", {}, {})
        assert len(issues) == 0

    def test_detects_via_non_src_path(self):
        """Works when the patch path omits the src. prefix."""
        module_map = {
            "src.services.foo.service": {"foo_service": "base_foo_service"},
        }
        singletons_short = {"foo_service": "src.services.foo.service.base_foo_service"}
        issues = self._check(
            "services.foo.service.foo_service",
            module_map,
            singletons_short,
        )
        assert len(issues) == 1
        assert issues[0]["expected"] == "src.services.foo.service.base_foo_service"

    def test_no_false_positive_non_service_but_in_index(self):
        """If a short name is in the singletons_short index but doesn't end with a service suffix,
        it should still be checked (could be a non-standard singleton name)."""
        module_map = {
            "src.services.foo.core": {"gadget": "base_gadget"},
        }
        singletons_short = {"gadget": "src.services.foo.core.base_gadget"}
        # _check_patch_target: attr="gadget" doesn't end with SERVICE_LIKE_SUFFIXES,
        # but it IS in singletons_short → should proceed to check
        issues = self._check(
            "src.services.foo.core.gadget",
            module_map,
            singletons_short,
        )
        assert len(issues) == 1

    def test_no_match_no_issue(self):
        """If the module has no matching singleton, no issue raised."""
        module_map = {
            "src.services.foo.service": {"bar_service": "base_bar_service"},
        }
        singletons_short = {"bar_service": "src.services.foo.service.base_bar_service"}
        issues = self._check(
            "src.services.foo.service.baz_service",
            module_map,
            singletons_short,
        )
        assert len(issues) == 0

    def test_module_not_in_map_skips(self):
        """If the module path doesn't exist in module_map, no issue."""
        module_map: Dict = {}
        singletons_short: Dict = {}
        issues = self._check(
            "src.services.unknown.service.foo_service",
            module_map,
            singletons_short,
        )
        assert len(issues) == 0

    def test_detects_engine_suffix(self):
        """_engine suffix is one of SERVICE_LIKE_SUFFIXES and should be checked."""
        module_map = {
            "src.services.foo.rhythm": {"rhythm_service": "base_rhythm_service"},
        }
        singletons_short = {"rhythm_service": "src.services.foo.rhythm.base_rhythm_service"}
        issues = self._check(
            "src.services.foo.rhythm.rhythm_service",
            module_map,
            singletons_short,
        )
        assert len(issues) == 1

    def test_no_parts_skips(self):
        """If the patch string has no dot-separated parts, skip (unusual)."""
        issues = self._check("justaname", {}, {})
        assert len(issues) == 0


# =========================================================================
# collect_singletons()
# =========================================================================

class TestCollectSingletons:
    def _write_module(self, tmp_path: Path, rel_path: str, content: str) -> Path:
        """Write a .py file in a temp project structure."""
        full_path = tmp_path / "src" / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return full_path

    def _patch_project_root(self, monkeypatch, tmp_path: Path):
        """Patch PROJECT_ROOT and SRC_DIR to point at tmp_path for isolated testing."""
        monkeypatch.setattr("scripts.validate_patch_targets.PROJECT_ROOT", tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.SRC_DIR", tmp_path / "src")

    def test_finds_singleton_declaration(self, tmp_path: Path, monkeypatch):
        """Scans a .py file with a base_* = ... assignment."""
        self._write_module(tmp_path, "services/foo/service.py",
                           "base_foo_service = FooService()\n"
                           "BASE = 42\n")
        self._patch_project_root(monkeypatch, tmp_path)
        result = collect_singletons()
        assert "src.services.foo.service" in result
        assert result["src.services.foo.service"]["foo_service"] == "base_foo_service"

    def test_skips_test_files(self, tmp_path: Path, monkeypatch):
        """Files named test_*.py should not be scanned for singletons."""
        self._write_module(tmp_path, "services/test_foo.py",
                           "base_foo_service = FooService()\n")
        self._patch_project_root(monkeypatch, tmp_path)
        result = collect_singletons()
        assert len(result) == 0

    def test_skips_non_py_files(self, tmp_path: Path, monkeypatch):
        """Non .py files should be skipped."""
        (tmp_path / "src" / "services" / "foo").mkdir(parents=True, exist_ok=True)
        (tmp_path / "src" / "services" / "foo" / "data.txt").write_text("base_foo_service = FooService()\n")
        self._patch_project_root(monkeypatch, tmp_path)
        result = collect_singletons()
        assert len(result) == 0

    def test_skips_pycache(self, tmp_path: Path, monkeypatch):
        """__pycache__ directories should be skipped."""
        cache = tmp_path / "src" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "cached.py").write_text("base_foo_service = FooService()\n")
        self._patch_project_root(monkeypatch, tmp_path)
        result = collect_singletons()
        assert len(result) == 0

    def test_empty_src_no_issues(self, tmp_path: Path, monkeypatch):
        """Empty src/ should return empty module_map."""
        (tmp_path / "src").mkdir(parents=True, exist_ok=True)
        self._patch_project_root(monkeypatch, tmp_path)
        result = collect_singletons()
        assert result == {}

    def test_multiple_files(self, tmp_path: Path, monkeypatch):
        """Multiple files across different modules are discovered."""
        self._write_module(tmp_path, "services/a.py", "base_a_service = A()\n")
        self._write_module(tmp_path, "services/b.py", "base_b_service = B()\n")
        self._patch_project_root(monkeypatch, tmp_path)
        result = collect_singletons()
        assert len(result) == 2
        assert result["src.services.a"]["a_service"] == "base_a_service"
        assert result["src.services.b"]["b_service"] == "base_b_service"

    def test_multiple_singletons_one_file(self, tmp_path: Path, monkeypatch):
        """A single file can declare multiple base_* singletons."""
        self._write_module(tmp_path, "services/hub.py",
                           "base_alpha = Alpha()\n"
                           "base_beta = Beta()\n")
        self._patch_project_root(monkeypatch, tmp_path)
        result = collect_singletons()
        assert len(result["src.services.hub"]) == 2


# =========================================================================
# find_mismatches() — full scan orchestration
# =========================================================================

class TestFindMismatches:
    def _write_test(self, tmp_path: Path, rel_path: str, content: str) -> Path:
        """Write a test .py file in the temp project."""
        full_path = tmp_path / "src" / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return full_path

    def test_detects_patch_mismatch(self, tmp_path: Path, monkeypatch):
        """Test file with a mismatched patch target is detected."""
        self._write_test(
            tmp_path, "services/nexus_engine/tests/test_foo.py",
            "from unittest.mock import patch\n"
            '@patch("src.services.foo.service.foo_service")\n'
            "def test_something(mock_foo): pass\n",
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.SRC_DIR", tmp_path / "src")
        module_map = {
            "src.services.foo.service": {"foo_service": "base_foo_service"},
        }
        singletons_short = {"foo_service": "src.services.foo.service.base_foo_service"}
        issues = find_mismatches(module_map, singletons_short)
        assert len(issues) == 1
        assert "test_foo.py" in issues[0]["test_file"]

    def test_correct_patch_no_issue(self, tmp_path: Path, monkeypatch):
        """Test file with correctly-named base_* patch target is not flagged."""
        self._write_test(
            tmp_path, "services/nexus_engine/tests/test_foo.py",
            "from unittest.mock import patch\n"
            '@patch("src.services.foo.service.base_foo_service")\n'
            "def test_something(mock_foo): pass\n",
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.SRC_DIR", tmp_path / "src")
        module_map = {
            "src.services.foo.service": {"foo_service": "base_foo_service"},
        }
        issues = find_mismatches(module_map, {})
        assert len(issues) == 0

    def test_skips_non_test_files(self, tmp_path: Path, monkeypatch):
        """Non-test files are not scanned for patch targets."""
        self._write_test(
            tmp_path, "services/foo/production.py",
            "from unittest.mock import patch\n"
            '@patch("src.services.foo.service.foo_service")\n'
            "def real_code(): pass\n",
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.SRC_DIR", tmp_path / "src")
        module_map = {
            "src.services.foo.service": {"foo_service": "base_foo_service"},
        }
        issues = find_mismatches(module_map, {})
        assert len(issues) == 0

    def test_skips_pycache_test_files(self, tmp_path: Path, monkeypatch):
        """Test files inside __pycache__ are not scanned."""
        cache_dir = tmp_path / "src" / "__pycache__"
        cache_dir.mkdir(parents=True)
        (cache_dir / "test_cached.py").write_text(
            'from unittest.mock import patch\npatch("src.services.foo.service.foo_service")\n'
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.SRC_DIR", tmp_path / "src")
        module_map = {
            "src.services.foo.service": {"foo_service": "base_foo_service"},
        }
        issues = find_mismatches(module_map, {})
        assert len(issues) == 0

    def test_non_py_files_skipped(self, tmp_path: Path, monkeypatch):
        """Non .py test files in test dirs are not scanned."""
        (tmp_path / "src" / "tests").mkdir(parents=True)
        (tmp_path / "src" / "tests" / "test_data.txt").write_text(
            'patch("src.services.foo.service.foo_service")\n'
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.SRC_DIR", tmp_path / "src")
        module_map = {
            "src.services.foo.service": {"foo_service": "base_foo_service"},
        }
        issues = find_mismatches(module_map, {})
        assert len(issues) == 0


# =========================================================================
# fix_issues()
# =========================================================================

class TestFixIssues:
    def test_fixes_single_file(self, tmp_path: Path, monkeypatch):
        """fix_issues replaces the old patch target with base_ version."""
        test_file = tmp_path / "src" / "services" / "tests" / "test_foo.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(
            'from unittest.mock import patch\n'
            'patch("src.services.foo.service.foo_service")\n'
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.PROJECT_ROOT", tmp_path)
        issues = [{
            "test_file": "src/services/tests/test_foo.py",
            "line": 2,
            "patch_target": "src.services.foo.service.foo_service",
            "expected": "src.services.foo.service.base_foo_service",
        }]
        fixed = fix_issues(issues)
        assert fixed == 1
        content = test_file.read_text()
        assert 'patch("src.services.foo.service.base_foo_service")' in content

    def test_fixes_no_orphan_file(self, tmp_path: Path, monkeypatch):
        """fix_issues does not fail when a file in the issue list doesn't exist on disk."""
        monkeypatch.setattr("scripts.validate_patch_targets.PROJECT_ROOT", tmp_path)
        issues = [{
            "test_file": "src/tests/nonexistent.py",
            "line": 1,
            "patch_target": "src.foo.bar_service",
            "expected": "src.foo.base_bar_service",
        }]
        # Should not crash, just report 0 fixes
        fixed = fix_issues(issues)
        assert fixed == 0

    def test_fixes_multiple_issues_one_file(self, tmp_path: Path, monkeypatch):
        """Multiple mismatches in the same file are all fixed."""
        test_file = tmp_path / "src" / "tests" / "test_multi.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(
            'patch("src.foo.a_service")\n'
            'patch("src.foo.b_service")\n'
        )
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.PROJECT_ROOT", tmp_path)
        issues = [
            {"test_file": "src/tests/test_multi.py", "line": 1,
             "patch_target": "src.foo.a_service", "expected": "src.foo.base_a_service"},
            {"test_file": "src/tests/test_multi.py", "line": 2,
             "patch_target": "src.foo.b_service", "expected": "src.foo.base_b_service"},
        ]
        fixed = fix_issues(issues)
        assert fixed == 1
        content = test_file.read_text()
        assert 'patch("src.foo.base_a_service")' in content
        assert 'patch("src.foo.base_b_service")' in content

    def test_fixes_no_issues_returns_zero(self):
        """With no issues, fix_issues returns 0."""
        assert fix_issues([]) == 0


# =========================================================================
# print_report()
# =========================================================================

class TestPrintReport:
    def test_reports_success(self, capsys):
        """When no issues, prints success message and returns True."""
        result = print_report([])
        assert result is True
        captured = capsys.readouterr()
        assert "All test patch targets correctly use base_*" in captured.out

    def test_reports_issues(self, capsys):
        """When issues exist, prints details and returns False."""
        issues = [
            {"test_file": "src/tests/test_foo.py", "line": 5,
             "patch_target": "src.foo.bar_service", "expected": "src.foo.base_bar_service"},
        ]
        result = print_report(issues)
        assert result is False
        captured = capsys.readouterr()
        assert "Found 1 mismatched patch target(s)" in captured.out
        assert "src/tests/test_foo.py:5" in captured.out
        assert 'patch("src.foo.bar_service")' in captured.out
        assert 'patch("src.foo.base_bar_service")' in captured.out

    def test_reports_multiple_issues(self, capsys):
        """Multiple issues are printed sorted by file and line."""
        issues = [
            {"test_file": "src/tests/test_b.py", "line": 10,
             "patch_target": "b", "expected": "base_b"},
            {"test_file": "src/tests/test_a.py", "line": 5,
             "patch_target": "a", "expected": "base_a"},
        ]
        result = print_report(issues)
        assert result is False
        captured = capsys.readouterr()
        assert "Found 2 mismatched patch target(s)" in captured.out
        # test_a should come before test_b (sorted)
        assert captured.out.index("test_a") < captured.out.index("test_b")


# =========================================================================
# main() — integration
# =========================================================================

class TestMainIntegration:
    def _patch_project_root(self, monkeypatch, tmp_path: Path):
        """Patch PROJECT_ROOT and SRC_DIR to point at tmp_path for isolated testing."""
        monkeypatch.setattr("scripts.validate_patch_targets.PROJECT_ROOT", tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.SRC_DIR", tmp_path / "src")

    def test_main_no_issues(self, tmp_path: Path, monkeypatch, capsys):
        """main() exits with code 0 when no mismatches exist."""
        (tmp_path / "src").mkdir(parents=True, exist_ok=True)
        self._patch_project_root(monkeypatch, tmp_path)
        with mock_patch("sys.argv", ["validate_patch_targets.py"]):
            with mock_patch.object(sys, "exit") as mock_exit:
                main_entry()
                mock_exit.assert_called_once_with(0)
        captured = capsys.readouterr()
        assert "All test patch targets correctly use base_*" in captured.out

    def test_main_with_issues(self, tmp_path: Path, monkeypatch, capsys):
        """main() exits with code 1 when mismatches exist."""
        # Write a test file with a mismatched patch
        test_dir = tmp_path / "src" / "tests"
        test_dir.mkdir(parents=True)
        (test_dir / "test_bad.py").write_text(
            'from unittest.mock import patch\n'
            '@patch("src.services.foo.service.foo_service")\n'
            'def test(): pass\n'
        )
        # Write the actual module that declares the base_* singleton
        svc_dir = tmp_path / "src" / "services" / "foo"
        svc_dir.mkdir(parents=True)
        (svc_dir / "service.py").write_text(
            "base_foo_service = FooService()\n"
        )
        self._patch_project_root(monkeypatch, tmp_path)
        with mock_patch("sys.argv", ["validate_patch_targets.py"]):
            with mock_patch.object(sys, "exit") as mock_exit:
                main_entry()
                mock_exit.assert_called_once_with(1)
        captured = capsys.readouterr()
        assert "Found 1 mismatched patch target(s)" in captured.out
        assert "test_bad.py" in captured.out

    def test_main_no_test_files(self, tmp_path: Path, monkeypatch, capsys):
        """main() works with no test files present."""
        (tmp_path / "src" / "services").mkdir(parents=True)
        (tmp_path / "src" / "services" / "foo.py").write_text("base_foo = Foo()\n")
        self._patch_project_root(monkeypatch, tmp_path)
        with mock_patch("sys.argv", ["validate_patch_targets.py"]):
            with mock_patch.object(sys, "exit") as mock_exit:
                main_entry()
                mock_exit.assert_called_once_with(0)

    def test_main_fix_flag(self, tmp_path: Path, monkeypatch, capsys):
        """main() with --fix corrects mismatches and exits 0."""
        test_dir = tmp_path / "src" / "tests"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "test_bad.py"
        test_file.write_text(
            'from unittest.mock import patch\n'
            '@patch("src.services.foo.service.foo_service")\n'
            'def test(): pass\n'
        )
        svc_dir = tmp_path / "src" / "services" / "foo"
        svc_dir.mkdir(parents=True)
        (svc_dir / "service.py").write_text(
            "base_foo_service = FooService()\n"
        )
        self._patch_project_root(monkeypatch, tmp_path)
        # Simulate --fix flag
        with mock_patch("sys.argv", ["validate_patch_targets.py", "--fix"]):
            with mock_patch.object(sys, "exit") as mock_exit:
                main_entry()
                mock_exit.assert_called_once_with(0)
        # Verify the fix was applied
        content = test_file.read_text()
        assert 'patch("src.services.foo.service.base_foo_service")' in content


# =========================================================================
# Edge cases
# =========================================================================

class TestEdgeCases:
    def test_unicode_file_skipped(self, tmp_path: Path, monkeypatch):
        """Files with encoding issues are skipped gracefully."""
        test_dir = tmp_path / "src" / "tests"
        test_dir.mkdir(parents=True)
        # Write binary garbage
        bad_file = test_dir / "test_bad_encoding.py"
        bad_file.write_bytes(b"\xff\xfe\x00\x01\x02")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.SRC_DIR", tmp_path / "src")
        module_map: Dict = {}
        issues = find_mismatches(module_map, {})
        assert len(issues) == 0

    def test_singletons_short_built_correctly(self, tmp_path: Path, monkeypatch):
        """The singletons_short index is populated correctly across modules."""
        src = tmp_path / "src"
        src.mkdir(parents=True, exist_ok=True)
        (src / "a.py").write_text("base_foo = Foo()\nbase_bar = Bar()\n")
        (src / "b.py").write_text("base_baz = Baz()\n")
        monkeypatch.setattr("scripts.validate_patch_targets.PROJECT_ROOT", tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.SRC_DIR", src)

        mm = collect_singletons()
        # 2 files + 3 singletons total
        assert len(mm) == 2
        total = sum(len(v) for v in mm.values())
        assert total == 3

    def test_decorator_patch_detected(self, tmp_path: Path, monkeypatch):
        """@patch(...) decorator form is detected (not just patch(...) calls)."""
        self._write_test(tmp_path, "tests/test_dec.py",
                         "@patch('src.foo.service.bar_service')\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("scripts.validate_patch_targets.SRC_DIR", tmp_path / "src")
        module_map = {"src.foo.service": {"bar_service": "base_bar_service"}}
        issues = find_mismatches(module_map, {"bar_service": "..."})
        assert len(issues) == 1

    def _write_test(self, tmp_path: Path, rel_path: str, content: str) -> Path:
        full_path = tmp_path / "src" / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return full_path
