#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# install-extension.sh
# Invoked by devcontainer postAttachCommand (runs every time VS Code attaches).
# Waits for the .vsix produced by build-extension.sh (which runs concurrently
# in postStartCommand) and installs it into the running VS Code Server instance.
# ─────────────────────────────────────────────────────────────────────────────
# Note: deliberately NOT using 'set -o pipefail' here — the 'code' CLI returns
# exit code 2 ("NoServer") when VS Code Server is still initialising; we handle
# that explicitly with a retry loop below.
set -eu

VSIX="/workspace/vscode-extension/ai-mutation-testing.vsix"
BUILD_TIMEOUT=120   # seconds to wait for build-extension.sh to produce .vsix
INSTALL_RETRIES=10  # attempts to run 'code --install-extension'
RETRY_DELAY=5       # seconds between install attempts

echo "──────────────────────────────────────────────────"
echo "▶ Installing AI Mutation Testing VS Code extension"
echo "──────────────────────────────────────────────────"

# ── Locate the 'code' CLI ────────────────────────────────────────────────────
# VS Code Server injects 'code' into PATH for interactive shells but not always
# for non-interactive lifecycle hooks.  Search well-known locations as a fallback.
if ! command -v code &>/dev/null; then
  for candidate in \
      /usr/local/bin/code \
      /usr/bin/code \
      /vscode/bin/remote-cli/code \
      /home/vscode/.vscode-server/bin/*/bin/code; do
    if [ -x "${candidate}" ]; then
      export PATH="$(dirname "${candidate}"):${PATH}"
      break
    fi
  done
fi

if ! command -v code &>/dev/null; then
  echo "⚠️  'code' CLI not found — extension will not be auto-installed."
  echo "   Once inside the container terminal run:"
  echo "   code --install-extension ${VSIX} --force"
  exit 0   # non-fatal: don't block the devcontainer from opening
fi

# ── Wait for build-extension.sh to produce the .vsix ────────────────────────
if [ ! -f "${VSIX}" ]; then
  echo "  Extension build in progress — waiting (up to ${BUILD_TIMEOUT}s)..."
  elapsed=0
  while [ "${elapsed}" -lt "${BUILD_TIMEOUT}" ]; do
    if [ -f "${VSIX}" ]; then
      break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
fi

if [ ! -f "${VSIX}" ]; then
  echo ""
  echo "⚠️  Timed out after ${BUILD_TIMEOUT}s waiting for ${VSIX}."
  echo "   In the container terminal run:"
  echo "   bash /workspace/.devcontainer/build-extension.sh"
  echo "   code --install-extension ${VSIX} --force"
  exit 0   # non-fatal
fi

# ── Install with retry (handles VS Code Server startup delay) ────────────────
# The 'code' CLI returns exit code 2 ("NoServer") when the server hasn't
# finished initialising.  Retrying resolves this within a few seconds.
echo "  Installing ${VSIX}..."
installed=0
for attempt in $(seq 1 "${INSTALL_RETRIES}"); do
  if code --install-extension "${VSIX}" --force 2>&1; then
    installed=1
    break
  fi
  rc=$?
  echo "  Attempt ${attempt}/${INSTALL_RETRIES} failed (exit ${rc}) — retrying in ${RETRY_DELAY}s..."
  sleep "${RETRY_DELAY}"
done

if [ "${installed}" -eq 0 ]; then
  echo ""
  echo "⚠️  Extension install failed after ${INSTALL_RETRIES} attempts."
  echo "   In the container terminal run:"
  echo "   code --install-extension ${VSIX} --force"
  exit 0   # non-fatal: container should still open
fi

echo ""
echo "✅ Extension installed.  Available commands:"
echo "   • Mutation: Run Baseline Tests"
echo "   • Mutation: Scan & Generate Mutants"
echo "   • Mutation: Execute Mutation Run"
echo "   • Mutation: Propose Test to Kill Survivor"
echo ""
echo "   Open the Mutation Explorer panel (beaker icon) in the Activity Bar."
