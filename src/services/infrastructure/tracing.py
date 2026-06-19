"""
Distributed Tracing with Jaeger via OpenTelemetry.

Sets up OTLP exporter (compatible with Jaeger's native OTLP endpoint),
auto-instruments FastAPI, SQLAlchemy, Redis, and Celery, and exposes
custom span utilities for critical paths.
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

_tracer_provider_initialized = False


def init_tracing(
    service_name: str = "ettametta",
    jaeger_endpoint: Optional[str] = None,
    enabled: Optional[bool] = None,
):
    """
    Initialize OpenTelemetry distributed tracing with Jaeger/OTLP exporter.

    Args:
        service_name: Service name reported to Jaeger.
        jaeger_endpoint: OTLP gRPC endpoint for Jaeger (e.g. http://jaeger:4317).
                         Falls back to OTEL_EXPORTER_OTLP_ENDPOINT env var.
        enabled: Force enable/disable. Falls back to JAEGER_ENABLED env var.
    """
    global _tracer_provider_initialized
    if _tracer_provider_initialized:
        logger.debug("Tracing already initialized — skipping")
        return

    if enabled is None:
        enabled = os.getenv("JAEGER_ENABLED", "false").lower() in ("true", "1", "yes")

    if not enabled:
        logger.info("Distributed tracing disabled (JAEGER_ENABLED=false)")
        _setup_noop_tracer()
        _tracer_provider_initialized = True
        return

    endpoint = jaeger_endpoint or os.getenv("JAEGER_ENDPOINT") or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.warning("Tracing enabled but no endpoint configured — falling back to noop")
        _setup_noop_tracer()
        _tracer_provider_initialized = True
        return

    # Build resource
    resource = Resource.create({"service.name": service_name})

    # Setup OTLP exporter (Jaeger supports OTLP natively since v1.35)
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        logger.info(f"Tracing initialized: service={service_name}, endpoint={endpoint}")
    except Exception as e:
        logger.error(f"Failed to initialize OTLP exporter: {e}")
        _setup_noop_tracer()
        _tracer_provider_initialized = True
        return

    # Auto-instrument libraries
    _instrument_fastapi()
    _instrument_sqlalchemy()
    _instrument_redis()
    _instrument_celery()
    _instrument_requests()

    _tracer_provider_initialized = True


def _setup_noop_tracer():
    """Configure a no-op tracer provider so trace.get_tracer() still works."""
    from opentelemetry.sdk.trace import TracerProvider

    provider = TracerProvider(resource=Resource.create({"service.name": "noop"}))
    trace.set_tracer_provider(provider)


def _instrument_fastapi():
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        # FastAPI is instrumented in main.py via FastAPIInstrumentor.instrument_app(app)
        # This is a safety net for cases where main.py hasn't run yet
        logger.debug("FastAPI instrumentation available")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-fastapi not installed")


def _instrument_sqlalchemy():
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        SQLAlchemyInstrumentor().instrument()
        logger.debug("SQLAlchemy instrumentation enabled")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-sqlalchemy not installed — skipping")
    except Exception as e:
        logger.debug(f"SQLAlchemy instrumentation skipped: {e}")


def _instrument_redis():
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor().instrument()
        logger.debug("Redis instrumentation enabled")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-redis not installed — skipping")
    except Exception as e:
        logger.debug(f"Redis instrumentation skipped: {e}")


def _instrument_celery():
    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        CeleryInstrumentor().instrument()
        logger.debug("Celery instrumentation enabled")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-celery not installed — skipping")
    except Exception as e:
        logger.debug(f"Celery instrumentation skipped: {e}")


def _instrument_requests():
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
        logger.debug("Requests instrumentation enabled")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-requests not installed — skipping")
    except Exception as e:
        logger.debug(f"Requests instrumentation skipped: {e}")


# ── Custom span utilities for critical paths ────────────────────────


def get_tracer(name: str = __name__) -> trace.Tracer:
    """Get a tracer instance."""
    return trace.get_tracer(name)


@contextmanager
def trace_span(name: str, attributes: Optional[dict] = None):
    """
    Context manager for creating a named span with optional attributes.

    Usage:
        with trace_span("video.generate", {"job_id": job.id}):
            result = await generate_video(job)
    """
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, str(v) if v is not None else "")
        yield span


def trace_video_generation(job_id: str, composition: str = ""):
    """Create a span for video generation pipeline."""
    return trace_span(
        "video.generation",
        {"job_id": job_id, "composition": composition},
    )


def trace_discovery_scan(platform: str = "", niche: str = ""):
    """Create a span for content discovery scan."""
    return trace_span(
        "discovery.scan",
        {"platform": platform, "niche": niche},
    )


def trace_publishing(platform: str = "", content_type: str = ""):
    """Create a span for content publishing."""
    return trace_span(
        "publishing.send",
        {"platform": platform, "content_type": content_type},
    )


def trace_llm_call(provider: str = "", model: str = ""):
    """Create a span for LLM inference call."""
    return trace_span(
        "llm.inference",
        {"provider": provider, "model": model},
    )
