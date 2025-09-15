import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


def setup_tracing(app) -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    service_name = os.getenv("OTEL_SERVICE_NAME", "magazine-ai-api")
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    if endpoint:
        exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
        span_processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(span_processor)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
