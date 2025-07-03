import os
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_tracer(app):
    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({SERVICE_NAME: "rickmorty-api"})
        )
    )

    # Use OTEL_EXPORTER_OTLP_ENDPOINT env var if defined
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)

    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
    FastAPIInstrumentor.instrument_app(app)
