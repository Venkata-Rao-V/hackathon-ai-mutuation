# ─────────────────────────────────────────────────────────────
# AI Mutation Testing — Dev Container Image
# Base: Ubuntu 22.04 devcontainer base (non-root vscode user)
# Bundles: Python 3.11, Node 20, g++/gcc, vsce, all pip & npm deps
# ─────────────────────────────────────────────────────────────
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

ARG DEBIAN_FRONTEND=noninteractive

# ── System packages ───────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-dev \
        python3.11-venv \
        python3-pip \
        build-essential \
        g++ \
        gcc \
        cmake \
        make \
        git \
        curl \
        jq \
    && rm -rf /var/lib/apt/lists/*

# Canonical python / pip symlinks
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python  python  /usr/bin/python3.11 1 \
    && python3 -m pip install --upgrade pip setuptools wheel

# ── Node.js 20 (LTS) ─────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# ── VS Code Extension CLI (vsce) ─────────────────────────────
RUN npm install -g @vscode/vsce

# ── Python runtime dependencies (cached layer) ───────────────
# Copy only requirements so this layer is re-used when source changes.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ── Extension Node dependencies (cached layer) ───────────────
COPY vscode-extension/package.json vscode-extension/package-lock.json /tmp/vscode-ext/
RUN cd /tmp/vscode-ext \
    && npm ci \
    && echo "Extension npm deps pre-cached"

# ── Non-root user already provided by base image ─────────────
USER vscode
