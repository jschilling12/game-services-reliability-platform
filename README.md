# Game Services Reliability Platform

A production-style platform for reliable game services, composed of four microservices, a reverse-proxy gateway, a load simulator, full observability, and a DevSecOps pipeline.

---

## Repository Layout

```
game-services-reliability-platform/
├── gateway/                  # nginx reverse-proxy config
├── services/
│   ├── matchmaking/          # Go service — player queue & match creation
│   ├── session/              # Go service — game session lifecycle
│   ├── telemetry/            # Go service — event ingestion & metrics
│   └── worker/               # Go service — background jobs
├── simulator/                # Python load simulator
├── infra/
│   ├── compose/              # docker-compose stack (local dev)
│   └── terraform/            # AWS IaC (week 4)
├── observability/
│   ├── prometheus/           # Scrape config
│   ├── grafana/              # Provisioned datasources & dashboards
│   └── jaeger/               # Tracing backend config
├── security/
│   ├── trivy/                # Vulnerability scanner config
│   ├── syft/                 # SBOM generator config
│   └── cosign/               # Image signing (optional)
├── scripts/                  # bootstrap / start / stop / scan helpers
├── docs/
│   ├── architecture/         # System overview & diagrams
│   ├── runbooks/             # Operational procedures
│   └── incidents/            # Post-mortem templates
└── .github/workflows/        # CI, security scan, release pipelines
```

---

## Quick Start

### Prerequisites

- Docker ≥ 24 with the Compose plugin
- Go 1.22+ (for local builds / tests)
- Python 3.12+ (for the simulator)

> **Windows users:** run the `.ps1` scripts in PowerShell. Linux / macOS users run the `.sh` equivalents in bash.

### 1 — Bootstrap (first time only)

```powershell
# PowerShell (Windows)
.\scripts\bootstrap.ps1
```

```bash
# bash (Linux / macOS)
./scripts/bootstrap.sh
```

This checks tool availability, copies `.env.example` → `.env`, and builds all images.

### 2 — Start the stack

```powershell
# PowerShell (Windows)
.\scripts\start.ps1
```

```bash
# bash (Linux / macOS)
./scripts/start.sh
```

| Endpoint         | URL                        |
|------------------|----------------------------|
| Gateway          | http://localhost:80         |
| Prometheus       | http://localhost:9090       |
| Grafana          | http://localhost:3000       |
| Jaeger UI        | http://localhost:16686      |

### 3 — Run the simulator

```bash
docker compose -f infra/compose/docker-compose.yml run --rm simulator \
  --rps 20 --duration 120
```

### 4 — Stop

```powershell
# PowerShell (Windows)
.\scripts\stop.ps1
```

```bash
# bash (Linux / macOS)
./scripts/stop.sh
```

---

## CI / CD

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| [ci.yml](.github/workflows/ci.yml) | push / PR | Build + test all services |
| [security.yml](.github/workflows/security.yml) | push / PR / nightly | Trivy scan + Syft SBOM |
| [release.yml](.github/workflows/release.yml) | `v*.*.*` tag | Build, push to GHCR, cosign sign |

---

## Security

- All service images are built on `distroless/static-debian12` (minimal attack surface).
- Trivy scans run on every PR; critical/high fixable CVEs fail the pipeline.
- SBOMs are generated in SPDX format and attached as workflow artifacts.
- Release images are signed with cosign (Sigstore keyless by default).

See [security/](security/) for scanner configuration files.

---

## Observability

- Traces: OpenTelemetry → Jaeger (OTLP ports 4317 / 4318)
- Metrics: Prometheus scrapes `/metrics` on each service
- Dashboards: Grafana provisioned automatically from `observability/grafana/provisioning/`

See [docs/architecture/overview.md](docs/architecture/overview.md) for the full system diagram.

---

## Contributing

1. Branch from `develop`.
2. Open a PR against `main`; all CI checks must pass.
3. Use the incident template in [docs/incidents/TEMPLATE.md](docs/incidents/TEMPLATE.md) for post-mortems.

---

## License

MIT
