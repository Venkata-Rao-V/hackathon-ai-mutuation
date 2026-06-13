#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# install-extension.sh
# Invoked by devcontainer postAttachCommand (runs every time VS Code attaches).
#
# Strategy: bypass 'code --install-extension' entirely.
# That CLI requires a local desktop VS Code installation and prints
# "code or code-insiders is not installed" when run inside a container.
# Instead, extract the .vsix (which is a ZIP archive) directly into the
# VS Code Server extensions directory — no CLI, no IPC socket needed.
# ─────────────────────────────────────────────────────────────────────────────
set -eu

VSIX="/workspace/vscode-extension/ai-mutation-testing.vsix"
BUILD_TIMEOUT=120   # seconds to wait for build-extension.sh to produce .vsix

# Extension identity (must match package.json publisher / name / version)
PUBLISHER="hackathon-ai"
EXT_NAME="ai-mutation-testing"
VERSION="1.0.0"
EXT_ID="${PUBLISHER}.${EXT_NAME}-${VERSION}"

echo "──────────────────────────────────────────────────"
echo "▶ Installing AI Mutation Testing VS Code extension"
echo "──────────────────────────────────────────────────"

# ── Wait for build-extension.sh to produce the .vsix ────────────────────────
if [ ! -f "${VSIX}" ]; then
  echo "  Extension build in progress — waiting (up to ${BUILD_TIMEOUT}s)..."
  elapsed=0
  while [ "${elapsed}" -lt "${BUILD_TIMEOUT}" ]; do
    if [ -f "${VSIX}" ]; then break; fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
fi

if [ ! -f "${VSIX}" ]; then
  echo ""
  echo "⚠️  Timed out after ${BUILD_TIMEOUT}s waiting for ${VSIX}."
  echo "   In the container terminal run:"
  echo "     bash /workspace/.devcontainer/build-extension.sh"
  exit 0   # non-fatal: don't block the devcontainer from opening
fi

# ── Locate VS Code Server extensions directory ───────────────────────────────
# VSCODE_AGENT_FOLDER is injected by VS Code Server when it starts the shell.
# Fall back to the canonical ~/.vscode-server path.
if [ -n "${VSCODE_AGENT_FOLDER:-}" ]; then
  EXT_INSTALL_DIR="${VSCODE_AGENT_FOLDER}/extensions"
else
  # Search under HOME for an existing vscode-server extensions directory;
  # create the default path if none found.
  EXT_INSTALL_DIR=$(find "${HOME}" -maxdepth 5 \
    -type d -name "extensions" \
    -path "*vscode-server*" 2>/dev/null | head -1)
  if [ -z "${EXT_INSTALL_DIR}" ]; then
    EXT_INSTALL_DIR="${HOME}/.vscode-server/extensions"
  fi
fi

mkdir -p "${EXT_INSTALL_DIR}"
echo "  Extensions directory: ${EXT_INSTALL_DIR}"

# ── Extract VSIX → extensions directory ─────────────────────────────────────
# A .vsix is a ZIP archive whose extension content lives under extension/.
# python3 is guaranteed to be available (installed in Dockerfile).
WORK_DIR="/tmp/vsix-install-$$"
mkdir -p "${WORK_DIR}"

echo "  Extracting ${VSIX}..."
python3 - "${VSIX}" "${WORK_DIR}" <<'PYEOF'
import sys, zipfile
vsix_path, dest = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(vsix_path) as z:
    members = [m for m in z.namelist() if m.startswith("extension/")]
    z.extractall(dest, members)
PYEOF

TARGET="${EXT_INSTALL_DIR}/${EXT_ID}"
rm -rf "${TARGET}"
mv "${WORK_DIR}/extension" "${TARGET}"
rm -rf "${WORK_DIR}"

echo ""
echo "✅ Extension installed to:"
echo "   ${TARGET}"
echo ""
echo "   Reload VS Code to activate: Ctrl+Shift+P → Developer: Reload Window"
echo ""
echo "   Available commands:"
echo "   • Mutation: Run Baseline Tests"
echo "   • Mutation: Scan & Generate Mutants"
echo "   • Mutation: Execute Mutation Run"
echo "   • Mutation: Propose Test to Kill Survivor"
echo ""
echo "   Open the Mutation Explorer panel (beaker icon) in the Activity Bar."
