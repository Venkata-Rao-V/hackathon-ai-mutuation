#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start-core-service.sh
# Invoked by devcontainer postStartCommand (runs every time the container starts).
# Starts the FastAPI core mutation service on port 8000 in the background.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

LOGFILE="/tmp/core-mutation-service.log"
PIDFILE="/tmp/core-mutation-service.pid"
SERVICE_SCRIPT="/workspace/agent/services/core_mutation_service.py"

# ── Already running? ─────────────────────────────────────────────────────────
if [[ -f "${PIDFILE}" ]]; then
  PID=$(cat "${PIDFILE}")
  if kill -0 "${PID}" 2>/dev/null; then
    echo "ℹ️  Core Mutation Service already running (PID ${PID}) — skipping start."
    exit 0
  fi
  rm -f "${PIDFILE}"
fi

# ── Start service ─────────────────────────────────────────────────────────────
echo "──────────────────────────────────────────────────"
echo "▶ Starting Core Mutation Service on :8000"
echo "   log → ${LOGFILE}"
echo "──────────────────────────────────────────────────"

cd /workspace
nohup python3 "${SERVICE_SCRIPT}" > "${LOGFILE}" 2>&1 &
echo $! > "${PIDFILE}"

# ── Wait for health check ─────────────────────────────────────────────────────
echo "   Waiting for /health endpoint..."
for i in $(seq 1 20); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Core service is up (PID $(cat "${PIDFILE}"))."
    exit 0
  fi
  sleep 1
done

echo "⚠️  Core service did not respond within 20 s. Check logs: ${LOGFILE}"
exit 1
