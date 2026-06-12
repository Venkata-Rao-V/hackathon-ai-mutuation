# Dev Container — Build, Run & Export Guide

## Overview

The dev container packages the complete AI Mutation Testing stack into a single, reproducible environment:

| Container | Image | Port | Purpose |
|---|---|---|---|
| `devcontainer` | custom Dockerfile | 8000 | Python 3.11 + Node 20 + g++ dev shell; runs the FastAPI core service |
| `prometheus` | `prom/prometheus:v2.52.0` | 9090 | Scrapes `/metrics` from the core service every 15 s |
| `grafana` | `grafana/grafana:10.4.2` | 3000 | Dashboards; Prometheus datasource auto-provisioned |

The VS Code extension is built from source inside the container and automatically installed into VS Code Server each time you attach.

---

## Prerequisites

| Tool | Minimum version | Install |
|---|---|---|
| Docker Engine | 24+ | https://docs.docker.com/engine/install/ |
| Docker Compose | v2 (plugin) | bundled with Docker Desktop / `apt install docker-compose-plugin` |
| VS Code | 1.85+ | https://code.visualstudio.com |
| Dev Containers extension | any | `ms-vscode-remote.remote-containers` |

---

## First-time setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd hackathon-ai-mutuation
```

### 2. Set API keys (optional — needed for AI kill-test generation)
Export keys in your host shell **before** opening the container. They are forwarded via `remoteEnv` and never written to disk inside the container.

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or create a `.env` file next to `docker-compose.yml`:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Open in VS Code
```
Ctrl+Shift+P → Dev Containers: Reopen in Container
```

VS Code will:
1. **Build** the Docker image (first run takes ~3–5 min; subsequent opens are instant via layer cache).
2. **Start** all three containers (`devcontainer`, `prometheus`, `grafana`).
3. Run `onCreateCommand` → compiles TypeScript and packs `ai-mutation-testing.vsix`.
4. Run `postStartCommand` → starts the FastAPI core service on port 8000.
5. Run `postAttachCommand` → installs the `.vsix` into the VS Code Server instance.
6. Auto-install companion marketplace extensions (`ms-python.python`, `ms-vscode.cpptools`, …).

---

## Building the container image manually

Use this when you want to pre-build the image before distributing it or before a demo.

```bash
# From the project root
docker compose -f .devcontainer/docker-compose.yml build

# Build with no layer cache (forces a clean rebuild)
docker compose -f .devcontainer/docker-compose.yml build --no-cache
```

---

## Running the stack without VS Code

```bash
# Start all services in detached mode
docker compose -f .devcontainer/docker-compose.yml up -d

# Follow core service logs
docker exec -it devcontainer tail -f /tmp/core-mutation-service.log

# Stop everything
docker compose -f .devcontainer/docker-compose.yml down
```

Open in browser:
- **Core service API docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana** (user: `admin` / pass: `admin`): http://localhost:3000

---

## Exporting the image as a portable archive

### Export a single image (devcontainer only)

```bash
# 1. Build the image
docker compose -f .devcontainer/docker-compose.yml build devcontainer

# 2. Find the image tag that was created
docker images | grep devcontainer

# 3. Save to a .tar archive
docker save hackathon-ai-mutuation-devcontainer:latest \
  | gzip > ai-mutation-testing-devcontainer.tar.gz
```

### Export the full stack (all three images)

```bash
docker save \
  hackathon-ai-mutuation-devcontainer:latest \
  prom/prometheus:v2.52.0 \
  grafana/grafana:10.4.2 \
  | gzip > ai-mutation-testing-stack.tar.gz
```

### Import on another machine

```bash
# Load images
docker load < ai-mutation-testing-stack.tar.gz

# Start the stack (no build needed — images are already loaded)
docker compose -f .devcontainer/docker-compose.yml up -d
```

---

## Rebuilding after source changes

### Only Python dependencies changed (`requirements.txt`)
```bash
docker compose -f .devcontainer/docker-compose.yml build --no-cache devcontainer
```

### Only extension source changed (TypeScript / package.json)
No rebuild needed. The extension is compiled and re-packed at container start via `onCreateCommand`. In VS Code:
```
Ctrl+Shift+P → Dev Containers: Rebuild Container
```
Or from the terminal inside the container:
```bash
bash /workspace/.devcontainer/build-extension.sh
code --install-extension /workspace/vscode-extension/ai-mutation-testing.vsix --force
```

---

## Verifying the stack

Run these from inside the dev container terminal:

```bash
# Core service health
curl http://localhost:8000/health

# Prometheus metrics endpoint
curl http://localhost:8000/metrics | head -20

# Prometheus scrape targets (should show devcontainer:8000 as UP)
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health'

# Extension installed
code --list-extensions | grep hackathon-ai
```

---

## Directory layout

```
.devcontainer/
├── Dockerfile                              # Custom image: Python 3.11, Node 20, g++, vsce
├── docker-compose.yml                      # Three-service stack with mutation-net bridge
├── devcontainer.json                       # VS Code devcontainer manifest
├── prometheus.yml                          # Prometheus scrape config
├── build-extension.sh                     # onCreateCommand: compile + pack .vsix
├── start-core-service.sh                  # postStartCommand: start FastAPI on :8000
└── grafana/
    └── provisioning/
        └── datasources/
            └── prometheus.yml              # Auto-provisioned Prometheus datasource
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Extension not installed after attach | Run `bash /workspace/.devcontainer/build-extension.sh` then `Ctrl+Shift+P → Dev Containers: Rebuild Container` |
| Core service not starting | Check `/tmp/core-mutation-service.log` inside the container |
| Prometheus shows `devcontainer:8000` as DOWN | Ensure the core service is running: `curl localhost:8000/health` |
| Grafana has no datasource | Verify the provisioning volume is mounted: `docker inspect grafana` |
| Port 8000/3000/9090 already in use on host | Change the host-side port in `docker-compose.yml` (e.g. `"18000:8000"`) |
| `vsce` not found during build | Image needs rebuilding: `docker compose build --no-cache devcontainer` |
