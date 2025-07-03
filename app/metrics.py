from prometheus_client import Counter, Summary, Histogram, Gauge ,REGISTRY
from prometheus_fastapi_instrumentator import Instrumentator

# --- Prometheus FastAPI Instrumentation ---
instrumentator = Instrumentator()

# --- Application Metrics ---
REQUEST_COUNT = Counter(
    "request_count_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Histogram of HTTP request latency",
    ["endpoint"]
)

request_latency = Summary(
    "app_request_latency_seconds",
    "Time spent processing request"
)

# --- Business Metrics ---
character_processed = Counter(
    "app_characters_processed_total",
    "Number of characters processed after filtering"
)

cache_hits = Counter(
    "app_cache_hits_total",
    "Number of times the Redis cache was hit"
)

cache_misses = Counter(
    "app_cache_misses_total",
    "Number of times the Redis cache was missed"
)

redis_failures = Counter(
    "app_redis_failures_total",
    "Number of Redis failures (e.g., during chaos experiments)"
)

cache_hit_ratio = Gauge(
    "app_cache_hit_ratio",
    "Cache hit ratio = hits / (hits + misses)"
)


# --- Register business metrics ---
REGISTRY.register(cache_hits)
REGISTRY.register(cache_misses)
REGISTRY.register(character_processed)
REGISTRY.register(redis_failures)
REGISTRY.register(cache_hit_ratio)