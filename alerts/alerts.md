# 🚨 Alerts & Observability Justification

This document outlines the observability features and alerting strategy used in the Rick & Morty FastAPI microservice.

---

## ✅ Metrics Exposed via Prometheus

| Metric Name                    | Type     | Description                                      | Justification                                      |
|-------------------------------|----------|--------------------------------------------------|----------------------------------------------------|
| `app_characters_processed_total` | Counter  | Number of filtered characters processed          | Detects abnormal drop in valid character processing |
| `app_cache_hits_total`           | Counter  | Number of Redis cache hits                       | Measures cache efficiency and potential cache issues |
| `app_request_latency_seconds`    | Summary  | Request processing time                          | Helps detect performance degradation or spikes      |

---

## ⏳ Rate Limiting

- **Limiter**: `100/minute` per client IP  
- **Tool**: [SlowAPI](https://github.com/laurentS/slowapi)

### Justification:
- Prevents abuse of the `/characters` endpoint
- Protects backend API and your Redis/Postgres infra from overload

---

## 📦 Caching with Redis

- **Keys**: Named as `characters_page_{page}_limit_{limit}_sortby_{sort_by}_order_{sort_order}`
- **TTL**: Configurable via `REDIS_TTL` (default: 3600s)

### Justification:
- Reduces latency and API cost
- Keeps responses fast and scalable under load

---

## 🛠 Health Checks

- **Endpoint**: `/healthcheck`
- **Checks**:
  - Redis `PING`
  - PostgreSQL `SELECT 1`

### Justification:
- Enables integration with Kubernetes liveness/readiness probes
- Returns `503` if any dependency is unhealthy

---

## 📊 OpenTelemetry Tracing

- **Exporter**: OTLP (HTTP) to Jaeger
- **Endpoint**: `http://jaeger:4318/v1/traces`

### Justification:
- Enables distributed tracing and latency bottleneck identification
- Integrates easily with Jaeger UI or any OTLP-compatible backend

---

## 🚧 Future Alerts You Can Add (via Prometheus Alertmanager):

| Alert Name            | Condition                             | Action                                       |
|-----------------------|----------------------------------------|----------------------------------------------|
| High Latency Alert    | `app_request_latency_seconds > 1s`     | Investigate backend/API performance issues   |
| Cache Miss Alert      | `rate(app_cache_hits_total[5m]) < 20`  | Redis may be unavailable or misconfigured    |
| 5xx Error Rate        | Too many 5xx over 1m window            | Indicates code or infra failures             |

---

## 📍 Recommendation

Ensure your `Prometheus` and `Alertmanager` instances are scraping `/metrics` and evaluating thresholds as per SLOs defined.

