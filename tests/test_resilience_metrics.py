"""
Tests for the Resilience Metrics module.
Validates that Prometheus counters, histograms, and gauges are properly
defined and can be incremented/observed without errors.
"""

from services.infrastructure.resilience_metrics import (
    jobs_submitted,
    jobs_completed,
    jobs_failed,
    jobs_duplicate_blocked,
    state_drift_detected,
    state_repairs_triggered,
    recovery_duration,
    sentinel_audit_pass,
    sentinel_audit_fail,
    chaos_faults_injected,
    chaos_scenarios_run,
    chaos_active,
    event_bus_messages_processed,
    event_bus_dlq_total,
)


class TestResilienceMetrics:
    """Verify all Prometheus metrics are properly wired and functional."""

    def test_job_counters_increment(self):
        """Job lifecycle counters should increment without error."""
        before = jobs_submitted._value.get()
        jobs_submitted.inc()
        assert jobs_submitted._value.get() == before + 1

        jobs_completed.inc()
        jobs_failed.inc()
        jobs_duplicate_blocked.inc()

    def test_state_drift_labeled_counter(self):
        """State drift counter should accept drift_type labels."""
        state_drift_detected.labels(drift_type="missing_from_cache").inc()
        state_drift_detected.labels(drift_type="count_mismatch").inc()
        # No exception = pass

    def test_repairs_counter(self):
        """Repairs counter should increment."""
        before = state_repairs_triggered._value.get()
        state_repairs_triggered.inc()
        assert state_repairs_triggered._value.get() == before + 1

    def test_recovery_duration_histogram(self):
        """Recovery duration histogram should accept observations."""
        recovery_duration.observe(0.5)
        recovery_duration.observe(2.3)
        recovery_duration.observe(0.01)
        # No exception = pass

    def test_sentinel_audit_counters(self):
        """Sentinel audit pass/fail counters should increment."""
        sentinel_audit_pass.inc()
        sentinel_audit_fail.inc()

    def test_chaos_labeled_counters(self):
        """Chaos injection counters should accept fault_type labels."""
        chaos_faults_injected.labels(fault_type="latency").inc()
        chaos_faults_injected.labels(fault_type="crash").inc()
        chaos_faults_injected.labels(fault_type="exhaustion").inc()
        chaos_faults_injected.labels(fault_type="scenario").inc()

    def test_chaos_scenario_counter(self):
        """Chaos scenario counter should accept scenario_name labels."""
        chaos_scenarios_run.labels(scenario_name="blackout").inc()
        chaos_scenarios_run.labels(scenario_name="cascade").inc()
        chaos_scenarios_run.labels(scenario_name="storm").inc()

    def test_chaos_active_gauge(self):
        """Active faults gauge should support inc/dec/set."""
        chaos_active.set(0)
        chaos_active.inc()
        chaos_active.inc()
        chaos_active.dec()
        assert chaos_active._value.get() == 1.0

    def test_event_bus_counters(self):
        """Event bus counters should accept stream labels."""
        event_bus_messages_processed.labels(stream="content_events").inc()
        event_bus_dlq_total.labels(stream="content_events").inc()
