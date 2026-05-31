# Architecture Overview

## System Diagram

```
                        ┌──────────────────────────────────────────────┐
                        │                  Gateway (nginx)              │
                        │                   :80                         │
                        └───────┬─────────────┬──────────────┬─────────┘
                                │             │              │
                         /matchmaking/   /session/     /telemetry/
                                │             │              │
                    ┌───────────┘   ┌─────────┘   ┌─────────┘
                    ▼               ▼              ▼
             ┌──────────┐   ┌──────────┐   ┌──────────┐
             │matchmaking│   │ session  │   │telemetry │
             │  :8080    │   │  :8081   │   │  :8082   │
             └──────────┘   └──────────┘   └──────────┘

                               ┌────────┐
                               │ worker │  (background jobs, no HTTP port)
                               └────────┘

                    ┌──────────────────────────────────┐
                    │         Observability            │
                    │  Prometheus :9090                │
                    │  Grafana    :3000                │
                    │  Jaeger     :16686               │
                    └──────────────────────────────────┘
```

## Services

| Service      | Port | Responsibility                          |
|--------------|------|-----------------------------------------|
| matchmaking  | 8080 | Player queue management & match creation |
| session      | 8081 | Active game session lifecycle            |
| telemetry    | 8082 | Event ingestion & metrics export         |
| worker       | —    | Background jobs (cleanup, notifications) |

## Data Flow

1. **Clients hit the nginx gateway on port 80.**  
   Port 80 is the standard HTTP port and requires no custom port in a URL. TLS termination (port 443) is intentionally deferred to the gateway layer in production so that backend services communicate unencrypted inside the private Docker network, avoiding double-encryption overhead without sacrificing confidentiality.

2. **The gateway routes by path prefix.**  
   Three prefixes are defined in `gateway/nginx.conf`:

   | Prefix | Upstream service | Internal port |
   |--------|-----------------|---------------|
   | `/matchmaking/` | matchmaking | 8080 |
   | `/session/` | session | 8081 |
   | `/telemetry/` | telemetry | 8082 |

   Ports 8080–8082 are conventional unprivileged HTTP ports (above 1024). Each service gets a unique port so they can all run on the same host without conflict during local development. The nginx `proxy_pass` strips the prefix before forwarding, so `matchmaking` only ever sees paths like `/queue`, not `/matchmaking/queue`.

3. **Services emit OpenTelemetry traces to Jaeger (OTLP on ports 4317 / 4318).**  
   OTLP (OpenTelemetry Protocol) is the vendor-neutral wire format for traces, metrics, and logs. Jaeger's all-in-one image listens on:
   - **4317** — OTLP over gRPC (preferred; binary, lower overhead)
   - **4318** — OTLP over HTTP/protobuf (easier to use from languages without a good gRPC library)

   These are the IANA-assigned standard ports for OTLP and are used by every major OTEL-compatible backend, making it straightforward to swap Jaeger for Tempo or a managed collector later.

4. **Services expose `/metrics` endpoints scraped by Prometheus.**  
   Each Go service will expose a `/metrics` handler returning text in Prometheus exposition format. Prometheus polls these endpoints on the interval set in `observability/prometheus/prometheus.yml` (15 s by default) and stores the time-series data locally. The pull model means services do not need to know where Prometheus is; they just expose the endpoint and Prometheus discovers them via the static config.

5. **Grafana visualises Prometheus metrics and Jaeger traces.**  
   Grafana is provisioned automatically with two datasources (`observability/grafana/provisioning/datasources/datasources.yml`):
   - **Prometheus** at `http://prometheus:9090` for metric graphs and alerting rules.
   - **Jaeger** at `http://jaeger:16686` for distributed trace search and flame graphs.

   Linking the two lets an engineer jump from a slow-request spike on a Grafana panel directly to the individual trace in Jaeger without leaving the UI.

6. **The worker runs periodic background tasks without exposing an HTTP port.**  
   The worker is a long-running Go process driven by a `time.Ticker`. It does not serve external traffic, so binding a port would add attack surface for no benefit. Planned background jobs include:
   - **Match expiry cleanup** — remove stale matchmaking queue entries older than a configurable TTL.
   - **Session heartbeat enforcement** — mark sessions as abandoned when no heartbeat has been received within the timeout window.
   - **Telemetry aggregation** — batch-flush raw events to long-term storage or an analytics sink.
   - **Notifications** — emit post-match result events (score summaries, rank updates) to a message queue.

   Each job is intended to be registered as a named handler called on every ticker interval, making it straightforward to add, remove, or reschedule individual jobs independently.

## Technology Choices

| Concern          | Choice                         | Reason                                   |
|------------------|--------------------------------|------------------------------------------|
| Language         | Go 1.22                        | Low latency, small binaries, easy Docker |
| Base image       | distroless/static-debian12     | Minimal attack surface                   |
| Reverse proxy    | nginx 1.27                     | Battle-tested, low overhead              |
| Metrics          | Prometheus + Grafana           | Industry standard                        |
| Tracing          | Jaeger (OTLP)                  | Open source, OTEL native                 |
| Container scan   | Trivy                          | Fast, SBOM-aware                         |
| SBOM             | Syft                           | SPDX / CycloneDX output                  |
| Image signing    | cosign                         | Sigstore keyless or key-based            |
| IaC (week 4)     | Terraform                      | AWS provider, remote state               |
