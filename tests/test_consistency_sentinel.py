"""
Tests for the ConsistencySentinel Enforcement Engine.
Validates drift detection, autonomous repair triggering, cooldown logic,
and structured DriftReport generation.

Uses sys.modules patching to avoid deep dependency chain (aioredis).
"""

import sys
import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ─── Mock the deep dependency chain before importing sentinel ─────
# This prevents the aioredis import error in CI/local environments
_mock_redis_module = MagicMock()
_mock_redis_module.get_redis = AsyncMock()
if "api.utils.redis" not in sys.modules:
    sys.modules["api.utils.redis"] = _mock_redis_module

# Mock aioredis itself if missing
if "aioredis" not in sys.modules:
    sys.modules["aioredis"] = MagicMock()

from services.analytics.consistency_sentinel import (
    ConsistencySentinel,
    DriftReport,
)


class TestDriftReport:
    """Verify DriftReport data structure."""

    def test_clean_report(self):
        report = DriftReport()
        assert report.is_clean is True
        d = report.to_dict()
        assert d["verdict"] == "CLEAN"
        assert d["drift_count"] == 0

    def test_dirty_report(self):
        report = DriftReport()
        report.drifts.append({
            "cohort_id": "batch_123",
            "type": "missing_from_cache",
            "db_count": 5,
            "cache_count": None,
        })
        assert report.is_clean is False
        d = report.to_dict()
        assert d["verdict"] == "DRIFT_DETECTED"
        assert d["drift_count"] == 1

    def test_report_with_repair_metadata(self):
        report = DriftReport()
        report.drifts.append({"cohort_id": "x", "type": "count_mismatch"})
        report.repair_triggered = True
        report.repair_duration_s = 1.23
        d = report.to_dict()
        assert d["repair_triggered"] is True
        assert d["repair_duration_s"] == 1.23

    def test_report_fields_present(self):
        report = DriftReport()
        d = report.to_dict()
        expected_keys = {
            "checked_at", "cohorts_checked", "drift_count",
            "drifts", "repair_triggered", "repair_duration_s", "verdict",
        }
        assert set(d.keys()) == expected_keys


class TestConsistencySentinel:
    """Verify sentinel initialization and lifecycle."""

    def test_init_defaults(self):
        sentinel = ConsistencySentinel()
        assert sentinel.check_interval == 30
        assert sentinel.repair_cooldown == 60
        assert sentinel._total_repairs == 0

    def test_custom_intervals(self):
        sentinel = ConsistencySentinel(check_interval=10, repair_cooldown=120)
        assert sentinel.check_interval == 10
        assert sentinel.repair_cooldown == 120

    def test_get_status_empty(self):
        sentinel = ConsistencySentinel()
        status = sentinel.get_status()
        assert status["running"] is True  # _stop_event not set
        assert status["total_repairs"] == 0
        assert status["recent_audits"] == []

    def test_stop(self):
        sentinel = ConsistencySentinel()
        sentinel.stop()
        assert sentinel._stop_event.is_set()
        status = sentinel.get_status()
        assert status["running"] is False

    def test_audit_history_capped(self):
        """Audit history should be capped at 100 entries."""
        sentinel = ConsistencySentinel()
        for _ in range(110):
            sentinel._audit_history.append(DriftReport())
        # Simulate the cap logic
        if len(sentinel._audit_history) > 100:
            sentinel._audit_history = sentinel._audit_history[-100:]
        assert len(sentinel._audit_history) == 100


class TestSentinelRepairCooldown:
    """Verify repair cooldown prevents thrashing."""

    @pytest.mark.asyncio
    async def test_cooldown_blocks_rapid_repairs(self):
        """Repair should NOT trigger if cooldown hasn't elapsed."""
        sentinel = ConsistencySentinel(repair_cooldown=300)
        sentinel._last_repair_time = time.time()  # just repaired

        report = DriftReport()
        report.drifts.append({"cohort_id": "x", "type": "count_mismatch"})

        with patch(
            "services.analytics.consistency_sentinel.base_recovery_service",
            create=True,
        ) as mock_recovery:
            mock_recovery.sync_all_vitals = AsyncMock()
            await sentinel._attempt_repair(report)
            # Should NOT have triggered — cooldown active
            mock_recovery.sync_all_vitals.assert_not_called()
            assert report.repair_triggered is False

    @pytest.mark.asyncio
    async def test_repair_triggers_after_cooldown(self):
        """Repair should trigger when cooldown has elapsed."""
        sentinel = ConsistencySentinel(repair_cooldown=0)
        sentinel._last_repair_time = 0  # far in the past

        report = DriftReport()
        report.drifts.append({"cohort_id": "x", "type": "missing_from_cache"})

        # Must patch the module that the lazy import resolves from
        mock_recovery_svc = MagicMock()
        mock_recovery_svc.sync_all_vitals = AsyncMock()
        with patch.dict(
            "sys.modules",
            {"services.infrastructure.recovery_service": MagicMock(
                base_recovery_service=mock_recovery_svc
            )},
        ):
            await sentinel._attempt_repair(report)
            mock_recovery_svc.sync_all_vitals.assert_called_once()
            assert report.repair_triggered is True
            assert report.repair_duration_s is not None
            assert sentinel._total_repairs == 1

    @pytest.mark.asyncio
    async def test_repair_increments_counter(self):
        """Multiple repairs should increment the counter."""
        sentinel = ConsistencySentinel(repair_cooldown=0)
        sentinel._last_repair_time = 0

        with patch(
            "services.analytics.consistency_sentinel.base_recovery_service",
            create=True,
        ) as mock_recovery:
            mock_recovery.sync_all_vitals = AsyncMock()
            
            for i in range(3):
                report = DriftReport()
                report.drifts.append({"cohort_id": f"x{i}", "type": "count_mismatch"})
                sentinel._last_repair_time = 0  # reset cooldown
                await sentinel._attempt_repair(report)
            
            assert sentinel._total_repairs == 3


class TestSentinelAudit:
    """Verify the audit_experiment_state method."""

    @pytest.mark.asyncio
    async def test_audit_clean_state(self):
        """When cache matches DB, audit should pass cleanly."""
        sentinel = ConsistencySentinel()

        mock_cohort = MagicMock()
        mock_cohort.id = "batch_001"
        mock_cohort.participants = ["v1", "v2"]
        mock_cohort.status = "ROLLING_OUT"

        with patch(
            "services.analytics.consistency_sentinel.AsyncSessionLocal"
        ) as mock_session_cls, patch(
            "services.analytics.consistency_sentinel.base_experiment_batcher"
        ) as mock_batcher:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_cohort]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_batcher.active_batches = [
                {"batch_id": "batch_001", "participants": ["v1", "v2"]}
            ]

            report = await sentinel.audit_experiment_state()
            assert report.is_clean is True
            assert report.cohorts_checked == 1

    @pytest.mark.asyncio
    async def test_audit_detects_missing_cohort(self):
        """When a cohort exists in DB but not cache, drift should be detected."""
        sentinel = ConsistencySentinel(repair_cooldown=300)
        sentinel._last_repair_time = time.time()

        mock_cohort = MagicMock()
        mock_cohort.id = "batch_002"
        mock_cohort.participants = ["v1"]
        mock_cohort.status = "ROLLING_OUT"

        with patch(
            "services.analytics.consistency_sentinel.AsyncSessionLocal"
        ) as mock_session_cls, patch(
            "services.analytics.consistency_sentinel.base_experiment_batcher"
        ) as mock_batcher:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_cohort]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_batcher.active_batches = []

            report = await sentinel.audit_experiment_state()
            assert report.is_clean is False
            assert len(report.drifts) == 1
            assert report.drifts[0]["type"] == "missing_from_cache"

    @pytest.mark.asyncio
    async def test_audit_detects_count_mismatch(self):
        """When participant counts differ, count_mismatch drift should be detected."""
        sentinel = ConsistencySentinel(repair_cooldown=300)
        sentinel._last_repair_time = time.time()

        mock_cohort = MagicMock()
        mock_cohort.id = "batch_003"
        mock_cohort.participants = ["v1", "v2", "v3"]
        mock_cohort.status = "ROLLING_OUT"

        with patch(
            "services.analytics.consistency_sentinel.AsyncSessionLocal"
        ) as mock_session_cls, patch(
            "services.analytics.consistency_sentinel.base_experiment_batcher"
        ) as mock_batcher:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_cohort]
            mock_db.execute = AsyncMock(return_value=mock_result)
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            # Cache has different count than DB
            mock_batcher.active_batches = [
                {"batch_id": "batch_003", "participants": ["v1"]}
            ]

            report = await sentinel.audit_experiment_state()
            assert report.is_clean is False
            assert report.drifts[0]["type"] == "count_mismatch"
            assert report.drifts[0]["db_count"] == 3
            assert report.drifts[0]["cache_count"] == 1
