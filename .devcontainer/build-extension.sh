#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# build-extension.sh
# Invoked by devcontainer onCreateCommand (runs once after container creation).
# Compiles the TypeScript extension and packs a .vsix ready for installation.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

EXT_DIR="/workspace/vscode-extension"
VSIX_OUT="${EXT_DIR}/ai-mutation-testing.vsix"

echo "──────────────────────────────────────────────────"
echo "▶ Building AI Mutation Testing VS Code extension"
echo "──────────────────────────────────────────────────"

cd "${EXT_DIR}"

# Install / sync Node dependencies (uses cached node_modules from Dockerfile layer
# if package-lock.json hasn't changed, otherwise updates them).
echo "  [1/3] Installing npm dependencies..."
npm ci

# Compile TypeScript → out/
echo "  [2/3] Compiling TypeScript..."
npm run compile

# Pack the extension into a self-contained .vsix archive.
# --no-dependencies skips listing marketplace dependencies (they are auto-installed
# from customizations.vscode.extensions in devcontainer.json instead).
echo "  [3/3] Packaging .vsix..."
vsce package --no-dependencies --out "${VSIX_OUT}"

echo ""
echo "✅ Extension built: ${VSIX_OUT}"
echo "   It will be installed automatically when VS Code attaches (postAttachCommand)."
