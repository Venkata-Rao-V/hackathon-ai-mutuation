#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# build-extension.sh
# Invoked by devcontainer postStartCommand (runs on every container start).
# Compiles the TypeScript extension and packs a .vsix ready for installation.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

EXT_DIR="/workspace/vscode-extension"
VSIX_OUT="${EXT_DIR}/ai-mutation-testing.vsix"
CACHE_MODULES="/tmp/vscode-ext/node_modules"

echo "──────────────────────────────────────────────────"
echo "▶ Building AI Mutation Testing VS Code extension"
echo "──────────────────────────────────────────────────"

cd "${EXT_DIR}"

# ── Step 1: Resolve node_modules ─────────────────────────────────────────────
# Prefer the Dockerfile-baked cache (/tmp/vscode-ext) to avoid a slow npm ci
# over the network.  Only fall back to npm ci when neither the workspace
# node_modules nor the baked cache exist (e.g. fully clean environment).
echo "  [1/3] Resolving npm dependencies..."
if [[ ! -d "${EXT_DIR}/node_modules" ]]; then
  if [[ -d "${CACHE_MODULES}" ]]; then
    echo "        Restoring from Dockerfile layer cache..."
    cp -r "${CACHE_MODULES}" "${EXT_DIR}/node_modules"
  else
    echo "        No cache found — running npm ci (requires network)..."
    npm ci
  fi
else
  echo "        node_modules already present — skipping install."
fi

# ── Step 2: Compile TypeScript → out/ ────────────────────────────────────────
echo "  [2/3] Compiling TypeScript..."
npm run compile

# ── Step 3: Pack .vsix ───────────────────────────────────────────────────────
# --no-dependencies: marketplace deps are installed via customizations.vscode.extensions
echo "  [3/3] Packaging .vsix..."
vsce package --no-dependencies --out "${VSIX_OUT}"

echo ""
echo "✅ Extension built: ${VSIX_OUT}"
echo "   install-extension.sh will install it once VS Code has attached."
