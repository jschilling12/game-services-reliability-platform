# Game Services Reliability Platform

A production-style reliability platform for game services. The active local stack runs a FastAPI matchmaking API, a Python background worker, nginx gateway routing, Postgres, Redis, load simulation, Prometheus/Grafana/Jaeger observability, and DevSecOps pipelines.

---

## Repository Layout

```text
game-services-reliability-platform/
|-- gateway/                  # nginx gateway and blue/green upstream configs
|-- services/
|   |-- matchmaking-api/      # FastAPI matchmaking API
|   |-- worker/               # Python Redis/Postgres background worker
|   |-- matchmaking/          # Go matchmaking service prototype
|   |-- session/              # Go session service prototype
|   `-- telemetry/            # Go telemetry service prototype
|-- simulator/                # Python load simulator
|-- infra/
|   |-- compose/              # Docker Compose stack and environment files
|   `-- terraform/            # Terraform AWS IaC scaffold
|-- observability/
|   |-- prometheus/           # Prometheus scrape config
|   |-- grafana/              # Provisioned datasources and dashboards
|   `-- jaeger/               # Tracing backend config
|-- security/
|   |-- trivy/                # Vulnerability scanner config
|   |-- syft/                 # SBOM generator config
|   `-- cosign/               # Image signing notes
|-- scripts/                  # bootstrap / start / stop / scan helpers
|-- docs/
|   |-- architecture/         # System overview and diagrams
|   |-- runbooks/             # Operational procedures
|   `-- incidents/            # Post-mortem templates
`-- .github/workflows/        # CI, security scan, release pipelines
```

---

## Quick Start

### Prerequisites

- Docker 24+ with the Compose plugin
- Python 3.12+ for local Python test/simulator work
- Go 1.22+ if you build or test the Go service prototypes

Windows users should run the `.ps1` scripts in PowerShell. Linux and macOS users should run the `.sh` scripts in bash.

### 1. Bootstrap

```powershell
.\scripts\bootstrap.ps1
```

```bash
./scripts/bootstrap.sh
```

Bootstrap checks Docker, copies `infra/compose/.env.example` to `infra/compose/.env` if needed, and builds the active dev images.

### 2. Start The Dev Stack

```powershell
.\scripts\start.ps1
```

```bash
./scripts/start.sh
```

The scripts start the merged Compose stack from `infra/compose/compose.yml` and `infra/compose/compose.dev.yml`.

| Endpoint | URL |
|----------|-----|
| Gateway | http://localhost:80 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| Jaeger UI | http://localhost:16686 |

### 3. Run The Simulator

```bash
docker compose -f infra/compose/compose.yml -f infra/compose/compose.dev.yml run --rm simulator \
  --rps 20 --duration 120
```

The simulator sends matchmaking traffic through the gateway at `/api/queue/join`.

### 4. Stop

```powershell
.\scripts\stop.ps1
```

```bash
./scripts/stop.sh
```

---

## Runtime Stack

- `gateway` routes `/api/*` traffic to the active matchmaking API upstream.
- `api_blue` is the default dev FastAPI matchmaking API instance.
- `worker` consumes Redis match jobs and marks matches ready in Postgres.
- `postgres` stores queued players and matches.
- `redis` backs the match-processing queue.
- `prometheus`, `grafana`, `jaeger`, and `nginx-exporter` provide local observability.

Staging Compose support lives in `infra/compose/compose.staging.yml` and adds `api_blue` plus `api_green` for blue-green or canary routing through `gateway/upstreams/*.conf`.

---

## CI / CD

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| [ci.yml](.github/workflows/ci.yml) | push / PR | Python syntax checks and Docker builds for `matchmaking-api` and `worker` |
| [security.yml](.github/workflows/security.yml) | push / PR / nightly | Trivy filesystem/image scans and Syft SBOMs |
| [release.yml](.github/workflows/release.yml) | `v*.*.*` tag | Build, push to GHCR, and cosign-sign active service images |

---

## Security

- Active service images are scanned with Trivy in CI.
- SBOMs are generated in SPDX format and uploaded as workflow artifacts.
- Release images are signed with cosign keyless signing.
- Go prototype Dockerfiles use `distroless/static-debian12` runtime images.

See [security/](security/) for scanner configuration files.

---

## Observability

- Traces: OpenTelemetry exports to Jaeger over OTLP on ports 4317 / 4318.
- Metrics: the matchmaking API exposes `/metrics`, the worker exposes metrics on port 9091, and nginx metrics come from `nginx-exporter`.
- Dashboards: Grafana is provisioned from `observability/grafana/provisioning/`.

See [docs/architecture/overview.md](docs/architecture/overview.md) for the broader system diagram and architecture notes.

---

## Contributing

1. Branch from `develop`.
2. Open a PR against `main`; all CI checks must pass.
3. Use the incident template in [docs/incidents/TEMPLATE.md](docs/incidents/TEMPLATE.md) for post-mortems.

---
