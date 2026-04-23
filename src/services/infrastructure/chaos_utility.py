"""
ChaosUtility: Orchestrated Failure Injection Engine.

Supports individual fault injection AND coordinated multi-fault "Killer Combo"
scenarios for the Reality Run. All injections are metered via Prometheus.

Scenarios:
  - blackout:  Redis flush + API exhaustion + latency spike
  - cascade:   Sequential degradation (crash → latency → exhaustion)
  - storm:     Randomized burst of all fault types over 30s window
"""

import os
import signal
import random
import asyncio
import logging
import time
from typing import Any
from datetime import datetime
from src.api.utils.redis import get_redis
from src.services.infrastructure.resilience_metrics import (
    chaos_faults_injected,
    chaos_scenarios_run,
    chaos_active,
)

logger = logging.getLogger("ChaosUtility")


class ChaosUtility:
    """
    The Infrastructure Destroyer — with Orchestration.
    Injects controlled failures into the Ettametta distributed swarm.
    Supports single-fault injection AND multi-fault scenario playbooks.
    """

    def __init__(self):
        self.active_faults: dict[str, Any] = {}
        self.injection_history: list[dict[str, Any]] = []
        self._continuous_task: asyncio.Task | None = None
        self._stop_continuous = asyncio.Event()

    # ─── Individual Fault Injection ───────────────────────────────

    async def inject_latency(self, service_name: str, delay_ms: int):
        """Adds artificial delay to a specific service interaction."""
        logger.warning(f"💣 [Chaos] Injecting {delay_ms}ms latency to {service_name}")
        redis = await get_redis()
        await redis.set(f"chaos:latency:{service_name}", delay_ms, ex=300)

        self._record_injection("latency", {"service": service_name, "delay_ms": delay_ms})
        chaos_faults_injected.labels(fault_type="latency").inc()
        chaos_active.inc()

    async def simulate_worker_crash(self):
        """Simulates a worker crash event by triggering recovery signals."""
        try:
            pid = os.getpid()
            logger.error(
                f"💣 [Chaos] CRITICAL! Simulating Worker Crash (PID: {pid})"
            )
            # Signal all subscribers to reclaim stale messages
            redis = await get_redis()
            await redis.set("chaos:worker_crash", str(pid), ex=120)

            self._record_injection("crash", {"pid": pid})
            chaos_faults_injected.labels(fault_type="crash").inc()
            chaos_active.inc()
        except Exception as e:
            logger.error(f"Chaos crash simulation failed: {e}")

    async def induce_api_exhaustion(self, platform: str = "youtube"):
        """Mocks a 429 Rate Limit error state for a platform."""
        logger.warning(f"💣 [Chaos] Inducing API Exhaustion for {platform}")
        redis = await get_redis()
        await redis.set(f"chaos:exhaustion:{platform}", "429", ex=600)

        self._record_injection("exhaustion", {"platform": platform})
        chaos_faults_injected.labels(fault_type="exhaustion").inc()
        chaos_active.inc()

    async def clear_all_faults(self):
        """Removes all active chaos injections from Redis."""
        redis = await get_redis()
        keys = []
        async for key in redis.scan_iter("chaos:*"):
            keys.append(key)
        if keys:
            await redis.delete(*keys)
        self.active_faults.clear()
        chaos_active.set(0)
        logger.info(f"🧹 [Chaos] Cleared {len(keys)} active faults.")

    async def check_faults(self, service_name: str) -> str | None:
        """Utility for services to check if they are under chaos interference."""
        redis = await get_redis()
        latency = await redis.get(f"chaos:latency:{service_name}")
        if latency:
            logger.debug(f"🐢 [Chaos] Applying {latency}ms latency to {service_name}")
            await asyncio.sleep(int(latency) / 1000.0)

        exhaustion = await redis.get(f"chaos:exhaustion:{service_name}")
        if exhaustion:
            return exhaustion
        return None

    # ─── Orchestrated Scenarios (Killer Combos) ───────────────────

    async def run_scenario(self, scenario_name: str) -> dict[str, Any]:
        """
        Executes a named multi-fault scenario.
        Returns a report of what was injected and when.
        """
        scenarios = {
            "blackout": self._scenario_blackout,
            "cascade": self._scenario_cascade,
            "storm": self._scenario_storm,
        }

        handler = scenarios.get(scenario_name)
        if not handler:
            return {
                "error": f"Unknown scenario: {scenario_name}",
                "available": list(scenarios.keys()),
            }

        logger.error(
            f"🔥🔥🔥 [Chaos] EXECUTING SCENARIO: {scenario_name.upper()} 🔥🔥🔥"
        )
        chaos_scenarios_run.labels(scenario_name=scenario_name).inc()
        chaos_faults_injected.labels(fault_type="scenario").inc()

        start = time.time()
        events = await handler()
        elapsed = time.time() - start

        report = {
            "scenario": scenario_name,
            "events": events,
            "duration_s": round(elapsed, 2),
            "executed_at": datetime.now().isoformat(),
        }
        self._record_injection("scenario", report)
        return report

    async def _scenario_blackout(self) -> list[dict[str, Any]]:
        """
        THE BLACKOUT: Simultaneous multi-system failure.
        Redis hot state invalidation + API exhaustion + global latency spike.
        """
        events = []

        # 1. Flush Redis experiment cache keys (simulates Redis restart)
        redis = await get_redis()
        flushed = 0
        async for key in redis.scan_iter("active_batch:*"):
            await redis.delete(key)
            flushed += 1
        events.append({"action": "redis_cache_flush", "keys_flushed": flushed})

        # 2. Exhaust all platform APIs simultaneously
        for platform in ["youtube", "tiktok", "instagram"]:
            await self.induce_api_exhaustion(platform)
            events.append({"action": "api_exhaustion", "platform": platform})

        # 3. Global latency spike
        for service in ["discovery", "video_engine", "analytics"]:
            await self.inject_latency(service, random.randint(2000, 5000))
            events.append({"action": "latency_spike", "service": service})

        return events

    async def _scenario_cascade(self) -> list[dict[str, Any]]:
        """
        THE CASCADE: Sequential degradation over 15 seconds.
        Simulates a real-world failure where one system going down
        causes a chain reaction.
        """
        events = []

        # Phase 1: Worker crash (t=0)
        await self.simulate_worker_crash()
        events.append({"action": "worker_crash", "t_offset_s": 0})

        # Phase 2: Latency spike (t=5s)
        await asyncio.sleep(5)
        await self.inject_latency("video_engine", 3000)
        events.append({"action": "latency_spike", "service": "video_engine", "t_offset_s": 5})

        # Phase 3: API exhaustion (t=10s)
        await asyncio.sleep(5)
        await self.induce_api_exhaustion("youtube")
        events.append({"action": "api_exhaustion", "platform": "youtube", "t_offset_s": 10})

        # Phase 4: Second worker crash (t=15s)
        await asyncio.sleep(5)
        await self.simulate_worker_crash()
        events.append({"action": "worker_crash_2", "t_offset_s": 15})

        return events

    async def _scenario_storm(self) -> list[dict[str, Any]]:
        """
        THE STORM: Randomized burst of all fault types over 30s window.
        Each fault fires at a random offset to simulate unpredictable chaos.
        """
        events = []
        fault_pool = [
            ("latency", {"service": "discovery", "delay_ms": 2000}),
            ("latency", {"service": "analytics", "delay_ms": 4000}),
            ("exhaustion", {"platform": "youtube"}),
            ("exhaustion", {"platform": "tiktok"}),
            ("crash", {}),
            ("latency", {"service": "video_engine", "delay_ms": 3000}),
            ("exhaustion", {"platform": "instagram"}),
            ("crash", {}),
        ]

        random.shuffle(fault_pool)

        for i, (fault_type, params) in enumerate(fault_pool):
            delay = random.uniform(0.5, 4.0)
            await asyncio.sleep(delay)

            if fault_type == "latency":
                await self.inject_latency(params["service"], params["delay_ms"])
            elif fault_type == "exhaustion":
                await self.induce_api_exhaustion(params["platform"])
            elif fault_type == "crash":
                await self.simulate_worker_crash()

            events.append({
                "action": fault_type,
                "params": params,
                "t_offset_s": round(delay * (i + 1), 1),
            })

        return events

    # ─── Continuous Chaos Loop ────────────────────────────────────

    async def start_continuous_chaos(
        self, intensity: str = "medium", duration_minutes: int = 30
    ) -> dict[str, Any]:
        """
        Starts a background loop that randomly injects faults at the given intensity.
        intensity: "low" (every 60s), "medium" (every 30s), "high" (every 10s)
        """
        if self._continuous_task and not self._continuous_task.done():
            return {"error": "Continuous chaos already running"}

        interval_map = {"low": 60, "medium": 30, "high": 10}
        interval = interval_map.get(intensity, 30)

        self._stop_continuous.clear()
        self._continuous_task = asyncio.create_task(
            self._continuous_loop(interval, duration_minutes)
        )

        logger.error(
            f"🌪️ [Chaos] CONTINUOUS CHAOS STARTED. "
            f"Intensity: {intensity}, Duration: {duration_minutes}min"
        )
        return {
            "status": "started",
            "intensity": intensity,
            "interval_s": interval,
            "duration_minutes": duration_minutes,
        }

    async def stop_continuous_chaos(self) -> dict[str, Any]:
        """Stops the continuous chaos loop and clears all active faults."""
        self._stop_continuous.set()
        if self._continuous_task:
            self._continuous_task.cancel()
            self._continuous_task = None
        await self.clear_all_faults()
        return {"status": "stopped", "faults_cleared": True}

    async def _continuous_loop(self, interval: int, duration_minutes: int):
        """Background loop that fires random faults at the given interval."""
        end_time = time.time() + (duration_minutes * 60)
        fault_actions = [
            lambda: self.inject_latency(
                random.choice(["discovery", "video_engine", "analytics"]),
                random.randint(500, 5000),
            ),
            lambda: self.simulate_worker_crash(),
            lambda: self.induce_api_exhaustion(
                random.choice(["youtube", "tiktok", "instagram"])
            ),
        ]

        try:
            while not self._stop_continuous.is_set() and time.time() < end_time:
                action = random.choice(fault_actions)
                await action()
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("🛑 [Chaos] Continuous loop cancelled.")
        finally:
            logger.info(
                f"🏁 [Chaos] Continuous chaos loop ended after "
                f"{duration_minutes} minutes."
            )

    # ─── Reporting ────────────────────────────────────────────────

    def get_chaos_report(self) -> dict[str, Any]:
        """Returns current chaos state and recent injection history."""
        recent = self.injection_history[-20:]
        return {
            "active_faults": len(self.active_faults),
            "continuous_running": (
                self._continuous_task is not None
                and not self._continuous_task.done()
            ),
            "total_injections": len(self.injection_history),
            "recent_injections": recent,
        }

    def _record_injection(self, fault_type: str, details: dict[str, Any]):
        """Appends an injection event to the history buffer."""
        entry = {
            "type": fault_type,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.injection_history.append(entry)
        # Keep last 200 entries
        if len(self.injection_history) > 200:
            self.injection_history = self.injection_history[-200:]


# Singleton Instance
base_chaos_utility = ChaosUtility()
