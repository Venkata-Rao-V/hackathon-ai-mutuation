#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# install-extension.sh
# Invoked by devcontainer postAttachCommand (runs every time VS Code attaches).
# Waits for the .vsix produced by build-extension.sh (which runs concurrently
# in postStartCommand) and installs it into the running VS Code Server instance.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

VSIX="/workspace/vscode-extension/ai-mutation-testing.vsix"
TIMEOUT=120   # seconds to wait for the build before giving up

echo "──────────────────────────────────────────────────"
echo "▶ Installing AI Mutation Testing VS Code extension"
echo "──────────────────────────────────────────────────"

# ── Wait for build-extension.sh to produce the .vsix ────────────────────────
if [[ ! -f "${VSIX}" ]]; then
  echo "  Extension build in progress — waiting (up to ${TIMEOUT}s)..."
  for i in $(seq 1 "${TIMEOUT}"); do
    if [[ -f "${VSIX}" ]]; then
      break
    fi
    sleep 1
  done
fi

if [[ ! -f "${VSIX}" ]]; then
  echo ""
  echo "❌ Timed out after ${TIMEOUT}s waiting for ${VSIX}."
  echo "   Run 'bash /workspace/.devcontainer/build-extension.sh' in the terminal"
  echo "   and then 'code --install-extension ${VSIX} --force'."
  exit 1
fi

# ── Install ───────────────────────────────────────────────────────────────────
echo "  Installing ${VSIX}..."
code --install-extension "${VSIX}" --force

echo ""
echo "✅ Extension installed.  Available commands:"
echo "   • Mutation: Run Baseline Tests"
echo "   • Mutation: Scan & Generate Mutants"
echo "   • Mutation: Execute Mutation Run"
echo "   • Mutation: Propose Test to Kill Survivor"
echo ""
echo "   Open the Mutation Explorer panel (beaker icon) in the Activity Bar."
