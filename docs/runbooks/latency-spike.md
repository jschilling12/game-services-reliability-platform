# Runbook: Latency Spike

## Symptoms
Users report slow join requests, Grafana p95 latency rises, or worker queue depth grows.

## First Dashboard
Open Grafana -> Game Backend -> Week 2 Observability.

## Prometheus Queries
- Request rate: `sum(rate(matchmaking_http_requests_total[5m]))`
- Error rate: `sum(rate(matchmaking_http_requests_total{status=~"5.."}[5m])) / sum(rate(matchmaking_http_requests_total[5m]))`
- p95 latency: `histogram_quantile(0.95, sum(rate(matchmaking_http_request_duration_seconds_bucket[5m])) by (le))`
- Queue depth: `max(matchmaking_queue_depth)`
- Worker throughput: `sum(rate(worker_matches_consumed_total[5m]))`

## Jaeger
Open `http://localhost:16686`, choose service `matchmaking-api`, search recent traces, then inspect spans for `request_id`, `match_request_id`, `player_id`, and `match_id`.

## Logs
Run:
`docker compose -f infra\compose\docker-compose.yml logs matchmaking-api worker`

Search for the same `request_id` in both services.

## Common Causes
- Postgres slow: DB spans are long.
- Redis queue growing: queue depth rises while worker throughput stays flat.
- Worker not keeping up: worker latency or failures increase.
- API errors increasing: error rate rises with 5xx logs.

## Recovery
Restart unhealthy services, reduce simulator load, inspect Postgres/Redis health, and compare the failing request across Grafana, Jaeger, and logs.