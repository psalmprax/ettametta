import logging
import sys
import os
try:
    from pythonjsonlogger import json as jsonlogger
    HAS_JSON_LOGGER = True  # alias: pythonjsonlogger.json is the new path
except ImportError:
    HAS_JSON_LOGGER = False
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

def setup_observability(service_name: str):
    """
    Initialize OpenTelemetry and Structured Logging.
    """
    # 1. Setup Structured Logging
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if HAS_JSON_LOGGER:
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(trace_id)s %(span_id)s',
            rename_fields={"levelname": "level", "asctime": "timestamp"},
            timestamp=True
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # 2. Setup OpenTelemetry
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)
    
    logging.info(f"Observability initialized for {service_name}", extra={"otel_enabled": bool(otlp_endpoint)})

def get_logger(name: str):
    """
    Returns a logger that is compatible with structured logging.
    In the future, this can be extended to automatically inject trace context.
    """
    return logging.getLogger(name)

class TraceContextFilter(logging.Filter):
    """
    Injects trace_id and span_id into log records for OTEL correlation.
    """
    def filter(self, record):
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            record.trace_id = format(span.get_span_context().trace_id, '032x')
            record.span_id = format(span.get_span_context().span_id, '016x')
        else:
            record.trace_id = None
            record.span_id = None
        return True
