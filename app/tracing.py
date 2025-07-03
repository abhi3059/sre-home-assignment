import os
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_tracer(app):
    # Use OTEL standard environment variable for endpoint
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector.fastapi:4318")

    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({SERVICE_NAME: "rickmorty-api"})
        )
    )

    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)

    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
    FastAPIInstrumentor.instrument_app(app)
