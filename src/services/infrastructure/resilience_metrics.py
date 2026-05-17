"""
Resilience Metrics: Production-Grade Prometheus KPIs.

Exposes business-critical resilience counters, gauges, and histograms
that power the Grafana "Reality Run" dashboard. Every subsystem
(Sentinel, ChaosUtility, RecoveryService) increments these atomically.
"""

from prometheus_client import Counter, Histogram, Gauge

# ─── Job Lifecycle ────────────────────────────────────────────────
jobs_submitted = Counter(
    "ettametta_jobs_submitted_total",
    "Total content jobs submitted to the pipeline",
)
jobs_completed = Counter(
    "ettametta_jobs_completed_total",
    "Total content jobs that completed successfully",
)
jobs_failed = Counter(
    "ettametta_jobs_failed_total",
    "Total content jobs that failed permanently",
)
jobs_duplicate_blocked = Counter(
    "ettametta_jobs_duplicate_total",
    "Duplicate job execution attempts that were blocked by idempotency guard",
)

# ─── State Consistency ────────────────────────────────────────────
state_drift_detected = Counter(
    "ettametta_state_drift_detected_total",
    "Number of Redis↔Postgres state drift events detected by Sentinel",
    ["drift_type"],  # "missing_from_cache", "count_mismatch"
)
state_repairs_triggered = Counter(
    "ettametta_state_repairs_total",
    "Number of autonomous repair cycles triggered by Sentinel",
)
recovery_duration = Histogram(
    "ettametta_recovery_duration_seconds",
    "Time taken for a full state recovery cycle",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# ─── Sentinel Auditing ───────────────────────────────────────────
sentinel_audit_pass = Counter(
    "ettametta_sentinel_audit_pass_total",
    "Number of audit cycles that found zero drift",
)
sentinel_audit_fail = Counter(
    "ettametta_sentinel_audit_fail_total",
    "Number of audit cycles that detected drift",
)

# ─── Chaos Engineering ───────────────────────────────────────────
chaos_faults_injected = Counter(
    "ettametta_chaos_faults_injected_total",
    "Total fault injection events by type",
    ["fault_type"],  # "latency", "crash", "exhaustion", "scenario"
)
chaos_scenarios_run = Counter(
    "ettametta_chaos_scenarios_total",
    "Orchestrated chaos scenarios executed",
    ["scenario_name"],
)
chaos_active = Gauge(
    "ettametta_chaos_active_faults",
    "Number of currently active chaos fault injections",
)

# ─── Event Bus Health ─────────────────────────────────────────────
event_bus_messages_processed = Counter(
    "ettametta_event_bus_messages_processed_total",
    "Total messages processed by the distributed event bus",
    ["stream"],
)
event_bus_dlq_total = Counter(
    "ettametta_event_bus_dlq_total",
    "Messages sent to the Dead Letter Queue after max retries",
    ["stream"],
)

# ─── Remotion Rendering Engine ─────────────────────────────────────
remotion_render_duration = Histogram(
    "ettametta_remotion_render_duration_seconds",
    "Time taken for a video render job",
    ["composition_id"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)
remotion_renders = Counter(
    "ettametta_remotion_renders_total",
    "Total video render attempts by status and composition",
    ["composition_id", "status"],  # status: "success", "transient_failure", "fatal_failure", "cancelled"
)
remotion_circuit_breaker_state = Gauge(
    "ettametta_remotion_circuit_breaker_state",
    "Current state of the Remotion circuit breaker (0=Closed, 1=Half-Open, 2=Open)",
)

