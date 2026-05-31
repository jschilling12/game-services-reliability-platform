# Runbook: Local Stack Start / Stop

## Start

```bash
./scripts/bootstrap.sh   # first time only
./scripts/start.sh
```

Expected output:
```
Stack is up:
  Gateway     -> http://localhost:80
  Prometheus  -> http://localhost:9090
  Grafana     -> http://localhost:3000
  Jaeger UI   -> http://localhost:16686
```

## Stop

```bash
./scripts/stop.sh
```

This tears down all containers **and removes named volumes**. Use
`docker compose down` (without `-v`) if you want to preserve data.

## Troubleshooting

| Symptom                        | Check                                                       |
|--------------------------------|-------------------------------------------------------------|
| Gateway returns 502            | `docker compose logs matchmaking session telemetry`         |
| No metrics in Prometheus       | Verify `/metrics` endpoints; check `prometheus.yml` targets |
| Grafana shows no data          | Confirm Prometheus datasource URL is `http://prometheus:9090` |
| Jaeger shows no traces         | Ensure OTLP endpoint env vars are set in services           |
