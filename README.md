# AI-Powered Mutation Testing Platform

This platform integrates AI-driven mutation testing into developer workflows, seamlessly exposing APIs web-ready and delivering a VS Code extension, custom AST parsing, container execution, and automated test-case generators.

## 🚀 Workspace Components

1. **`agent/`**: Core back-end orchestration logic, unit tests, and FastAPI-based services.
   - `core_mutation_service.py`: FastAPI server exposing REST and Server-Sent Events interfaces.
   - `parser.py`: Language-agnostic pluggable transformer adapters.
   - `test_runner.py`: Isolation sandbox execution wrapper.
   - `ai_engine.py`: Mutator selection & automated test generator integration with OpenAI and Ollama.
   - `run_agents.py`: End-to-end multi-agent orchestration cli.
2. **`vscode-extension/`**: Visual Studio Code Extension workspace built in TypeScript.
   - `src/extension.ts`: Client orchestration logic.
   - `src/mutationTree.ts`: Multi-state sidebar explorer tree view.
3. **`.devcontainer/`**: Docker container configuration sidecars.
   - `devcontainer.json`: Installs standard NodeJS & Python feature platforms and preloads VS Code configurations.
   - `docker-compose.yml`: Launches continuous Prometheus and Grafana background monitoring services.

---

## ⚙️ Quick Start backend & validation

### 1. Requirements Setup
```bash
pip install -r requirements.txt
```

### 2. Verify Backend Core Flow
Run the full test simulation script. This starts the FastAPI daemon, performs a "Golden Master" baseline runs, scans target abstract trees, validates sandbox runs, and generates tests to kill survivors:
```bash
python run_all.py
```

---

## 🛠️ How to Check & Verify the VS Code Extension

To compile, load, and manually test the extension directly within visual studio code:

1.  **Open Extension Workspace:**
    Open the nested directory `vscode-extension/` in a fresh VS Code window or open terminal inside it.
2.  **Install development dependencies:**
    Run package installers to fetch extension dependencies:
    ```bash
    cd vscode-extension
    npm install
    ```
3.  **Compile & Launch Debug Runner:**
    Press **`F5`** (or go to *Run and Debug* tab in VS Code and click *Launch Extension*). This launches a new sandboxed window named **[Extension Development Host]**.
4.  **How to interact:**
    *   Open `agent/hello.py` in the new window.
    *   Open command palette (`Ctrl+Shift+P` on Windows/Linux or `Cmd+Shift+P` on macOS) and run `Mutation: Run Baseline Tests` to verify tests configuration health.
    *   Run `Mutation: Scan & Generate Mutants` to explore logical mutant coordinates.
    *   Check out the **Mutation Explorer** panel inside your Activity Bar (beaker icon). Click any custom nodes to verify side-by-side **Diff Editor** alignments.
    *   Execute `Mutation: Execute Mutation Run` to spawn background sandboxes.
    *   If any mutant survives, write your AI protection tests inside `agent/test_hello.py` using `Mutation: Propose Test to Kill Survivor`.

---

## 🐳 How to Test the Dev Container Locally

To prove that the extension and metrics collectors run natively inside container interfaces out-of-the-box:

1.  **Ensure prerequisites:**
    Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and the [Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) in your VS Code.
2.  **Open Workspace Container:**
    Open command palette (`Ctrl+Shift+P`) and choose **`Dev Containers: Reopen in Container`**.
3.  **Automatic Environment Initialization:**
    The feature script reads `.devcontainer/devcontainer.json` to:
    *   Provision complete NodeJS (20), Python (3.11), and Docker-in-Docker components.
    *   Run `onCreateCommand` to load python dependency structures (`requirements.txt`).
    *   Expose backend uvicorn ports (`8000`), Grafana (`3000`), and Prometheus (`9090`).
    *   Launches the FastAPI backend service automatically in the background.
4.  **Monitoring metrics:**
    Once loaded, telemetry metrics can be monitored:
    *   Prometheus target metrics: View [http://localhost:9090](http://localhost:9090).
    *   Grafana Metrics Dashboards: Load [http://localhost:3000](http://localhost:3000) (User/Pass: `admin` / `admin`).
    *   Active `/metrics` endpoint data: Check [http://localhost:8000/metrics](http://localhost:8000/metrics).

---

## 🏆 Current Progress & Visual UX Upgrades (June 2026)

All phases of the platform have been achieved and feature **100% full implementation coverage**:

1.  **Friendly Mutant Representation & Symbol Translation:** Mutated AST operators now represent cleanly in tree listings as readable mathematical structures (e.g., `'==' ➜ '!='`) rather than internal program class strings (e.g., `'NotEq'`), providing unparalleled UX clarity.
2.  **Sleek Diff Editor Actions Toolbar:** Added fully integrated **Accept Mutant** and **Reject Mutant** commands mapped to the actual VS Code diff title-bar header. No interruptive prompts or popovers interfere with file-focus.
3.  **Dynamic Session Reset & Data Clean-up:** Added a **"Clear Mutation Data"** action (`$(trash)` icon) at the top of the Mutation Explorer, allowing developer groups to wipe cached results on local arrays and backend registries instantly.
4.  **Themed Categorized Telemetry Dashboard:** Designed structural metrics grouping (Platform Security Indicators vs. Sandbox Job Pipeline Stats) and minimized bounding block styles to provide highly-efficient views mapping Grafana streams natively without scroll overflows.

