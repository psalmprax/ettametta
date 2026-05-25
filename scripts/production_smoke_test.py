#!/usr/bin/env python3
"""Production smoke test runner for the ettametta golden path.

The checks are intentionally staged from cheap infrastructure probes to heavier
production workflow tests. By default the script is non-destructive and only
checks public/read-only surfaces. Use explicit flags for browser E2E and video
render verification.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_API_URL = "http://localhost:7201"
DEFAULT_DASHBOARD_URL = "http://localhost:7200"
REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    duration_ms: int


class SmokeRunner:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.results: list[CheckResult] = []

    def add(self, name: str, status: str, detail: str, started: float) -> None:
        elapsed = int((time.monotonic() - started) * 1000)
        self.results.append(CheckResult(name, status, detail, elapsed))
        marker = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skip": "SKIP"}[
            status
        ]
        print(f"[{marker}] {name}: {detail} ({elapsed}ms)")

    def http_json(self, url: str, timeout: int = 20) -> tuple[int, Any, str]:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "ettametta-smoke/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                try:
                    parsed: Any = json.loads(body)
                except json.JSONDecodeError:
                    parsed = body
                return response.status, parsed, body
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = body
            return exc.code, parsed, body

    def http_text(self, url: str, timeout: int = 20) -> tuple[int, str]:
        req = urllib.request.Request(
            url, headers={"User-Agent": "ettametta-smoke/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace")

    def run_command(
        self,
        name: str,
        command: list[str],
        timeout: int,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        required: bool = True,
    ) -> None:
        started = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                cwd=str(cwd or REPO_ROOT),
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError:
            status = "fail" if required else "skip"
            self.add(name, status, f"{command[0]} is not installed", started)
            return
        except subprocess.TimeoutExpired:
            self.add(name, "fail", f"timed out after {timeout}s", started)
            return

        output = " ".join(proc.stdout.strip().split())[:500]
        if proc.returncode == 0:
            self.add(name, "pass", output or "command completed", started)
        else:
            status = "fail" if required else "warn"
            self.add(name, status, output or f"exit code {proc.returncode}", started)

    def check_http_json(
        self,
        name: str,
        url: str,
        expected_statuses: set[int] | None = None,
        required_keys: set[str] | None = None,
    ) -> None:
        started = time.monotonic()
        expected_statuses = expected_statuses or {200}
        try:
            status, parsed, raw = self.http_json(url)
        except Exception as exc:
            self.add(name, "fail", f"{type(exc).__name__}: {exc}", started)
            return

        if status not in expected_statuses:
            self.add(name, "fail", f"HTTP {status}: {raw[:240]}", started)
            return
        if required_keys and not isinstance(parsed, dict):
            self.add(name, "fail", "response is not a JSON object", started)
            return
        if required_keys and not required_keys.issubset(parsed.keys()):
            missing = ", ".join(sorted(required_keys - set(parsed.keys())))
            self.add(name, "fail", f"missing keys: {missing}", started)
            return
        self.add(name, "pass", f"HTTP {status}", started)

    def check_dashboard(self) -> None:
        started = time.monotonic()
        try:
            status, body = self.http_text(self.args.dashboard_url)
        except Exception as exc:
            self.add(
                "dashboard html",
                "fail",
                f"{type(exc).__name__}: {exc}",
                started,
            )
            return

        if status != 200:
            self.add("dashboard html", "fail", f"HTTP {status}", started)
            return
        if "<html" not in body.lower():
            self.add("dashboard html", "warn", "HTTP 200 but no HTML marker", started)
            return
        self.add("dashboard html", "pass", "dashboard returned HTML", started)

    def check_openapi_paths(self) -> None:
        started = time.monotonic()
        try:
            status, parsed, _raw = self.http_json(f"{self.args.api_url}/openapi.json")
        except Exception as exc:
            self.add("openapi golden paths", "fail", f"{type(exc).__name__}: {exc}", started)
            return

        if status != 200 or not isinstance(parsed, dict):
            self.add("openapi golden paths", "fail", f"HTTP {status}", started)
            return

        paths = set((parsed.get("paths") or {}).keys())
        required_paths = {
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/discovery/search",
            "/api/v1/discovery/scan",
            "/api/v1/video/generate",
            "/api/v1/nexus/compose",
            "/api/v1/publish/platforms",
            "/api/v1/analytics/stats/summary",
        }
        missing = sorted(required_paths - paths)
        if missing:
            self.add("openapi golden paths", "fail", f"missing {', '.join(missing)}", started)
            return
        self.add("openapi golden paths", "pass", f"{len(required_paths)} main routes present", started)

    def check_env_contract(self) -> None:
        expected = [
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY",
            "INTERNAL_API_TOKEN",
            "GROQ_API_KEY",
            "YOUTUBE_API_KEY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_STORAGE_BUCKET_NAME",
        ]
        if not self.args.check_env:
            started = time.monotonic()
            self.add("production env contract", "skip", "use --check-env to inspect process env", started)
            return

        started = time.monotonic()
        missing = [key for key in expected if not os.getenv(key)]
        if missing:
            self.add("production env contract", "warn", f"missing {', '.join(missing)}", started)
        else:
            self.add("production env contract", "pass", "required env vars are present", started)

    def check_docker(self) -> None:
        if not self.args.docker:
            started = time.monotonic()
            self.add("docker compose services", "skip", "use --docker to inspect containers", started)
            return
        self.run_command(
            "docker compose services",
            ["docker", "compose", "ps", "--format", "json"],
            timeout=30,
            required=True,
        )

    def check_playwright(self) -> None:
        if not self.args.e2e:
            started = time.monotonic()
            self.add("playwright e2e", "skip", "use --e2e to run browser tests", started)
            return
        if not shutil.which("npx"):
            started = time.monotonic()
            self.add("playwright e2e", "fail", "npx is not installed", started)
            return
        env = os.environ.copy()
        env["BASE_URL"] = self.args.dashboard_url
        env["SKIP_WEB_SERVER"] = "1"
        self.run_command(
            "playwright e2e",
            ["npx", "playwright", "test", *self.args.e2e_specs],
            cwd=REPO_ROOT / "src/tests/e2e",
            env=env,
            timeout=self.args.e2e_timeout,
            required=True,
        )

    def check_video_render(self) -> None:
        if self.args.video_scenario is None:
            started = time.monotonic()
            self.add("video render smoke", "skip", "use --video-scenario N to render video", started)
            return
        self.run_command(
            "video render smoke",
            [
                sys.executable,
                "scratch/test_full_production.py",
                str(self.args.video_scenario),
            ],
            timeout=self.args.video_timeout,
            required=True,
        )

    def run(self) -> int:
        print("ettametta production smoke test")
        print(f"api_url={self.args.api_url}")
        print(f"dashboard_url={self.args.dashboard_url}")
        print()

        self.check_http_json("api root", f"{self.args.api_url}/", required_keys={"message", "version"})
        self.check_http_json("api direct health", f"{self.args.api_url}/health")
        self.check_http_json("api versioned health", f"{self.args.api_url}/api/v1/health")
        self.check_http_json("dashboard api proxy health", f"{self.args.dashboard_url}/api/v1/health")
        self.check_dashboard()
        self.check_openapi_paths()
        self.check_env_contract()
        self.check_docker()
        self.check_playwright()
        self.check_video_render()

        failing = [result for result in self.results if result.status == "fail"]
        warning = [result for result in self.results if result.status == "warn"]
        print()
        print("summary")
        print(f"passed={sum(r.status == 'pass' for r in self.results)}")
        print(f"warned={len(warning)}")
        print(f"skipped={sum(r.status == 'skip' for r in self.results)}")
        print(f"failed={len(failing)}")

        if self.args.json:
            payload = [result.__dict__ for result in self.results]
            print(json.dumps(payload, indent=2))

        return 1 if failing else 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run staged production smoke tests against ettametta."
    )
    parser.add_argument("--api-url", default=os.getenv("API_URL", DEFAULT_API_URL))
    parser.add_argument(
        "--dashboard-url",
        default=os.getenv("DASHBOARD_URL", DEFAULT_DASHBOARD_URL),
    )
    parser.add_argument("--check-env", action="store_true")
    parser.add_argument("--docker", action="store_true")
    parser.add_argument("--e2e", action="store_true")
    parser.add_argument(
        "--e2e-specs",
        nargs="*",
        default=[
            "tests/auth",
            "tests/discovery",
            "tests/creation",
            "tests/publishing",
            "tests/analytics",
        ],
    )
    parser.add_argument("--e2e-timeout", type=int, default=900)
    parser.add_argument("--video-scenario", type=int)
    parser.add_argument("--video-timeout", type=int, default=1200)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    return SmokeRunner(args).run()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
