# Chaos Engineering Report

## Test Objective
- Validate resilience of `rickmorty-api` when Redis is disrupted

## Scenario
- Kill Redis pod every 5 minutes for 30 seconds

## Observations
- API `/healthcheck` returned 503 during Redis outage
- `/characters` endpoint handled Redis downtime with fallback logic
- No crash observed in main application pod

## Recommendations
- Add Redis retry logic if needed
- Extend caching fallback in `/characters` during Redis failure
