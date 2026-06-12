"""
core_mutation_service.py — FastAPI Mutation Web Service (API-First Core)
========================================================================
Exposes rest communication channels for local VS Code integration and future web dashboards,
housing state registries, parallel workers pools, and metrics collectors.
"""

import os
import uuid
import tempfile
from typing import Dict, Any, List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local modules
from parser import PythonASTAdapter, CppASTAdapter
from test_runner import PytestRunnerAdapter, CppRunnerAdapter
from ai_engine import AIEngine

CPP_EXTENSIONS = [".cpp", ".cc", ".cxx", ".hpp", ".h", ".c"]


def is_cpp_source(file_path: str) -> bool:
    return os.path.splitext(file_path)[1].lower() in CPP_EXTENSIONS


def detect_language_from_targets(workspace_dir: str, target_files: Optional[List[str]]) -> str:
    for file_path in target_files or []:
        candidate = file_path if os.path.isabs(file_path) else os.path.join(workspace_dir, file_path)
        if os.path.splitext(candidate)[1].lower() == ".c":
            return "c"
        if is_cpp_source(candidate):
            return "cpp"
    return "python"


def detect_language_from_file_path(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".c":
        return "c"
    if ext in CPP_EXTENSIONS:
        return "cpp"
    return "python"


def ai_config_for_language(language: str) -> Dict[str, Any]:
    if language == "c":
        return APP_CONFIG.get("ai_engine_c", APP_CONFIG.get("ai_engine_cpp", APP_CONFIG.get("ai_engine", {})))
    if language == "cpp":
        return APP_CONFIG.get("ai_engine_cpp", APP_CONFIG.get("ai_engine", {}))
    return APP_CONFIG.get("ai_engine_python", APP_CONFIG.get("ai_engine", {}))


def build_ai_engine(language: str, provider_override: Optional[str], api_key: Optional[str]) -> AIEngine:
    ai_cfg = ai_config_for_language(language)
    provider = provider_override or ai_cfg.get("provider", "mock")
    return AIEngine(provider=provider, api_key=api_key, config=ai_cfg)

def get_adapter_for_file(filePath: str):
    ext = os.path.splitext(filePath)[1].lower()
    if ext in CPP_EXTENSIONS:
        return CppASTAdapter()
    return PythonASTAdapter()

def get_runner_for_file(filePath: str):
    ext = os.path.splitext(filePath)[1].lower()
    if ext in CPP_EXTENSIONS:
        return CppRunnerAdapter()
    return PytestRunnerAdapter()

def get_runner_for_workspace(workspace_dir: str, target_files: Optional[List[str]] = None, requested_runner: Optional[str] = None):
    if requested_runner:
        req_lower = requested_runner.lower()
        if req_lower == "c" or "g++" in req_lower or "cpp" in req_lower or "gcc" in req_lower or "gtest" in req_lower:
            return CppRunnerAdapter()
        elif "pytest" in req_lower or "python" in req_lower:
            return PytestRunnerAdapter()

    if target_files:
        for f in target_files:
            if os.path.splitext(f)[1].lower() in CPP_EXTENSIONS:
                return CppRunnerAdapter()
    if os.path.exists(os.path.join(workspace_dir, "agent", "hello.cpp")) or os.path.exists(os.path.join(workspace_dir, "hello.cpp")) or os.path.exists(os.path.join(workspace_dir, "agent", "hello.c")) or os.path.exists(os.path.join(workspace_dir, "hello.c")):
        config_path = os.path.join(workspace_dir, "mutation_config.yml")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "hello.cpp" in content or "hello.c" in content or "test_runner: g++" in content or "test_runner: gcc" in content or "test_runner: cpp" in content or "test_runner: c" in content:
                    return CppRunnerAdapter()
                elif "hello.py" in content:
                    return PytestRunnerAdapter()
            except Exception:
                pass
        return CppRunnerAdapter()
    return PytestRunnerAdapter()

app = FastAPI(
    title="AI-Mutation Core Service",
    description="Stateless and language-agnostic rest API service for compiling code mutations.",
    version="1.0.0"
)

# Enable CORS for VS Code Webviews and external browser client panels
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════
# In-Memory Database Registry (Synchronized via cache endpoints)
# ══════════════════════════════════════════════════════════════
DATABASE = {
    "projects": {},
    "mutations_cache": {},   # mutant_id -> mutant dict
    "mutation_runs": {},     # run_id -> run status dict
    "active_acceptance": {}, # mutant_id -> "ACCEPTED" | "REJECTED" | "PENDING"
}


# ══════════════════════════════════════════════════════════════
# Pydantic Schemas
# ══════════════════════════════════════════════════════════════

class BaselineRequest(BaseModel):
    workspaceDir: str = Field(..., description="Root absolute directory path")
    testRunner: str = "pytest"


class MutationGenerateRequest(BaseModel):
    workspaceDir: str
    targetFiles: List[str]
    operators: List[str] = ["arithmetic", "conditional_boundary", "logical"]
    aiEngineProvider: Optional[str] = None
    aiApiKey: Optional[str] = None


class TestRunExecuteRequest(BaseModel):
    workspaceDir: str
    mutantIds: List[str]
    parallelWorkers: int = 4
    useIncrementalCache: bool = True


class TestGenerateRequest(BaseModel):
    workspaceDir: str
    survivingMutantIds: List[str]
    targetFiles: List[str]
    testFile: str
    aiEngineProvider: Optional[str] = None
    aiApiKey: Optional[str] = None


# ══════════════════════════════════════════════════════════════
# REST Endpoints
# ══════════════════════════════════════════════════════════════

@app.get("/health")
def api_health():
    return {"status": "ONLINE", "engine": "FastAPI", "version": "1.0.0"}


@app.post("/api/v1/projects/{projectId}/test-runs/baseline")
def execute_baseline(projectId: str, payload: BaselineRequest):
    """Establish unmodified tests 'Golden Master' baseline metrics."""
    # Support mixed workspaces where both C++ and Python elements are scanned and run
    print(payload)
    runners_to_run = []
    
    req_runner = payload.testRunner.lower() if payload.testRunner else "all"
    
    pytest_runner = PytestRunnerAdapter()
    cpp_runner = CppRunnerAdapter()
    
    has_pytest = pytest_runner.detect_workspace(payload.workspaceDir)
    has_cpp = cpp_runner.detect_workspace(payload.workspaceDir)
    
    print(has_pytest)
    print(req_runner)
    
    if req_runner in ["pytest", "python"]:
        if has_pytest:
            runners_to_run.append(("python", pytest_runner))
    elif req_runner in ["g++", "cpp", "c", "gcc", "gtest"]:
        if has_cpp:
            runners_to_run.append(("cpp", cpp_runner))
    else:  # "all", "both" or automatic detection
        if has_pytest:
            runners_to_run.append(("python", pytest_runner))
        if has_cpp:
            runners_to_run.append(("cpp", cpp_runner))

    if not runners_to_run:
        # fallback to what is detected
        if has_pytest:
            runners_to_run.append(("python", pytest_runner))
        if has_cpp:
            runners_to_run.append(("cpp", cpp_runner))
            
    if not runners_to_run:
        raise HTTPException(
            status_code=400,
            detail="Specified workspace does not contain matching pytest or C++ dynamic configurations."
        )

    tests_merged = []
    total_tests = 0
    duration_ms = 0
    overall_status = "TESTS_PASSED"
    
    for lang, runner in runners_to_run:
        temp_sandbox = os.path.join(tempfile_dir_root(), f"baseline-{lang}-{uuid.uuid4().hex[:8]}")
        if lang == "cpp":
            primary_file = os.path.join(payload.workspaceDir, "agent", "hello.cpp")
            if not os.path.exists(primary_file):
                primary_file = os.path.join(payload.workspaceDir, "hello.cpp")
            if not os.path.exists(primary_file):
                primary_file = os.path.join(payload.workspaceDir, "agent", "hello.c")
            if not os.path.exists(primary_file):
                primary_file = os.path.join(payload.workspaceDir, "hello.c")
        else:
            primary_file = os.path.join(payload.workspaceDir, "agent", "hello.py")

        res_lang = runner.execute_suite(
            workspace_root=payload.workspaceDir,
            sandbox_dir=temp_sandbox,
            target_file=primary_file,
            mutated_code=None
        )
        
        if res_lang.get("overallStatus") != "TESTS_PASSED":
            overall_status = "TESTS_FAILED"
            
        total_tests += res_lang.get("totalTests", 0)
        duration_ms += res_lang.get("durationMs", 0)
        tests_merged.extend(res_lang.get("tests", []))

    final_res = {
        "overallStatus": overall_status,
        "killingTest": None,
        "failureOutput": "",
        "durationMs": duration_ms,
        "testsPassed": total_tests if overall_status == "TESTS_PASSED" else max(0, total_tests - 1),
        "testsFailed": 0 if overall_status == "TESTS_PASSED" else 1,
        "totalTests": total_tests,
        "tests": tests_merged
    }

    DATABASE["projects"][projectId] = {
        "workspace": payload.workspaceDir,
        "baseline": final_res
    }

    # Increment baseline run details inside the memory registry
    DATABASE["baseline_runs_count"] = DATABASE.get("baseline_runs_count", 0) + 1
    if overall_status == "TESTS_PASSED":
        DATABASE["baseline_runs_passed"] = DATABASE.get("baseline_runs_passed", 0) + 1
    else:
        DATABASE["baseline_runs_failed"] = DATABASE.get("baseline_runs_failed", 0) + 1

    return {
        "runId": f"base_{uuid.uuid4().hex[:8]}",
        "status": "SUCCESS" if overall_status == "TESTS_PASSED" else "FAIL",
        "totalTests": total_tests,
        "durationMs": duration_ms,
        "details": final_res
    }


@app.post("/api/v1/projects/{projectId}/mutations/generate")
def generate_mutations(projectId: str, payload: MutationGenerateRequest):
    """Scan and generate logical AST mutation candidates."""
    all_mutants = []

    for file_rel in payload.targetFiles:
        # Resolve target files cleanly to handle potential nested or absolute paths on Windows
        if os.path.isabs(file_rel):
            full_path = file_rel
        else:
            full_path = os.path.join(payload.workspaceDir, file_rel)
            
        if not os.path.exists(full_path):
            # Fallback to local files if path mismatch
            fallback_name = os.path.basename(file_rel)
            fallback_path = os.path.join(payload.workspaceDir, "agent", fallback_name)
            if os.path.exists(fallback_path):
                full_path = fallback_path
            else:
                raise HTTPException(status_code=404, detail=f"Target file not found: {file_rel}")

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        adapter = get_adapter_for_file(full_path)
        file_candidates = adapter.parse_mutations(file_rel, content)
        all_mutants.extend(file_candidates)

    # Apply AI Intelligence selection weighting and prioritization
    language = detect_language_from_targets(payload.workspaceDir, payload.targetFiles)
    ai_engine = build_ai_engine(language, payload.aiEngineProvider, payload.aiApiKey)
    prioritized_list = ai_engine.prioritize_mutants(all_mutants)

    # Cache mutant schemas to server database register
    for m in prioritized_list:
        m_id = m["mutant_id"]
        DATABASE["mutations_cache"][m_id] = m
        DATABASE["active_acceptance"][m_id] = "ACCEPTED"

    return {
        "projectId": projectId,
        "generationId": f"gen_{uuid.uuid4().hex[:8]}",
        "mutants": prioritized_list
    }


@app.post("/api/v1/projects/{projectId}/mutations/{mutantId}/accept")
def accept_mutation(projectId: str, mutantId: str):
    if mutantId not in DATABASE["mutations_cache"]:
        raise HTTPException(status_code=444, detail="Requested mutant not cached in service registry.")
    DATABASE["active_acceptance"][mutantId] = "ACCEPTED"
    return {"mutantId": mutantId, "status": "ACCEPTED"}


@app.post("/api/v1/projects/{projectId}/mutations/{mutantId}/reject")
def reject_mutation(projectId: str, mutantId: str):
    if mutantId not in DATABASE["mutations_cache"]:
        raise HTTPException(status_code=444, detail="Requested mutant not cached.")
    DATABASE["active_acceptance"][mutantId] = "REJECTED"
    return {"mutantId": mutantId, "status": "REJECTED"}


@app.post("/api/v1/projects/{projectId}/reset")
def reset_project_database(projectId: str):
    """Clear and reset the in-memory database registry."""
    DATABASE["projects"][projectId] = {}
    DATABASE["mutations_cache"] = {}
    DATABASE["mutation_runs"] = {}
    DATABASE["active_acceptance"] = {}
    DATABASE["baseline_runs_count"] = 0
    DATABASE["baseline_runs_passed"] = 0
    DATABASE["baseline_runs_failed"] = 0
    return {"status": "SUCCESS", "message": "Database successfully reset."}


@app.post("/api/v1/projects/{projectId}/mutations/{mutantId}/preview")
def preview_mutation(projectId: str, mutantId: str, payload: Dict[str, Any]):
    """Apply the specified mutation AST transform and return the mutated code text."""
    workspace_dir = payload.get("workspaceDir")
    candidates = list(DATABASE["mutations_cache"].values())
    mutant = DATABASE["mutations_cache"].get(mutantId)
    if not mutant:
        raise HTTPException(status_code=404, detail="Mutant not found in cache.")

    orig_file = mutant["file_path"]
    if not os.path.isabs(orig_file) and workspace_dir:
        orig_file = os.path.join(workspace_dir, orig_file)

    if not os.path.exists(orig_file):
        if is_cpp_source(orig_file):
            fallback = os.path.join(workspace_dir, "agent", "hello.cpp") if workspace_dir else None
            if fallback and not os.path.exists(fallback):
                fallback = os.path.join(workspace_dir, "agent", "hello.c") if workspace_dir else None
        else:
            fallback = os.path.join(workspace_dir, "agent", "hello.py") if workspace_dir else None
        if fallback and os.path.exists(fallback):
            orig_file = fallback
        else:
            raise HTTPException(status_code=404, detail=f"Source file not found: {mutant['file_path']}")

    with open(orig_file, "r", encoding="utf-8") as f:
        unmu_code = f.read()

    adapter = get_adapter_for_file(orig_file)
    try:
        mutated_code = adapter.apply_mutation(unmu_code, mutantId, candidates)
        return {"original": unmu_code, "mutated": mutated_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate AST mutation: {str(e)}")


def run_mutation_workers_background(run_id: str, proj_id: str, ws_dir: str, mutant_ids: List[str]):
    """Background executing task matching isolated sandboxes concurrently."""
    results = []

    # Get cached items
    candidates = list(DATABASE["mutations_cache"].values())

    for m_id in mutant_ids:
        mutant = DATABASE["mutations_cache"].get(m_id)
        if not mutant:
            continue

        orig_file = mutant["file_path"]
        if not os.path.isabs(orig_file):
            orig_file = os.path.join(ws_dir, orig_file)

        if not os.path.exists(orig_file):
            # Fallback pathing resolution
            if is_cpp_source(orig_file):
                fallback = os.path.join(ws_dir, "agent", "hello.cpp")
                if not os.path.exists(fallback):
                    fallback = os.path.join(ws_dir, "agent", "hello.c")
            else:
                fallback = os.path.join(ws_dir, "agent", "hello.py")
            if os.path.exists(fallback):
                orig_file = fallback

        with open(orig_file, "r", encoding="utf-8") as f:
            unmu_code = f.read()

        adapter = get_adapter_for_file(orig_file)
        runner = get_runner_for_file(orig_file)

        # Apply target mutation change code via adapter
        mutated_code_src = adapter.apply_mutation(unmu_code, m_id, candidates)

        temp_sandbox = os.path.join(tempfile_dir_root(), f"mut-sandbox-{m_id}-{uuid.uuid4().hex[:6]}")
        res = runner.execute_suite(
            workspace_root=ws_dir,
            sandbox_dir=temp_sandbox,
            target_file=orig_file,
            mutated_code=mutated_code_src
        )

        status_result = "KILLED" if res["overallStatus"] == "TESTS_FAILED" else "SURVIVED"
        if res["overallStatus"] == "TIMEOUT":
            status_result = "KILLED" # Timeout indicates successful infinite-loop detection which verifies mutant kill (as per mutation testing guidelines)

        results.append({
            "mutantId": m_id,
            "status": status_result,
            "killingTest": res["killingTest"],
            "executionDurationMs": res["durationMs"],
            "failureOutput": res["failureOutput"],
            "testsPassed": res.get("testsPassed", 0),
            "testsFailed": res.get("testsFailed", 0),
            "totalTests": res.get("totalTests", 0),
            "line_number": mutant.get("line_number")
        })

    DATABASE["mutation_runs"][run_id] = {
        "status": "COMPLETED",
        "results": results
    }


@app.post("/api/v1/projects/{projectId}/test-runs")
def execute_test_runs(projectId: str, payload: TestRunExecuteRequest, bg_tasks: BackgroundTasks):
    """Trigger parallel isolation sandboxes to test-run mutants in background threads."""
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    DATABASE["mutation_runs"][run_id] = {
        "status": "IN_PROGRESS",
        "results": []
    }

    bg_tasks.add_task(
        run_mutation_workers_background,
        run_id,
        projectId,
        payload.workspaceDir,
        payload.mutantIds
    )

    return {
        "runId": run_id,
        "status": "IN_PROGRESS",
        "estimatedDurationMs": len(payload.mutantIds) * 1500
    }


@app.get("/api/v1/projects/{projectId}/test-runs/{runId}/status")
def query_run_status(projectId: str, runId: str):
    """Retrieve mutant testing result statistics."""
    if runId not in DATABASE["mutation_runs"]:
        raise HTTPException(status_code=404, detail="Requested run session not discovered.")
    return DATABASE["mutation_runs"][runId]


@app.post("/api/v1/projects/{projectId}/tests/generate")
def execute_tests_generation(projectId: str, payload: TestGenerateRequest):
    """Synthesize custom unit tests designed specifically to kill survivors."""
    proposed_tests = []
    for m_id in payload.survivingMutantIds:
        mutant = DATABASE["mutations_cache"].get(m_id)
        if not mutant:
            continue

        tgt_rel = payload.targetFiles[0] if payload.targetFiles else "agent/hello.py"
        full_tgt = os.path.join(payload.workspaceDir, tgt_rel)
        if not os.path.exists(full_tgt):
            if is_cpp_source(tgt_rel):
                full_tgt = os.path.join(payload.workspaceDir, "agent", "hello.cpp")
                if not os.path.exists(full_tgt):
                    full_tgt = os.path.join(payload.workspaceDir, "agent", "hello.c")
            else:
                full_tgt = os.path.join(payload.workspaceDir, "agent", "hello.py")
        
        with open(full_tgt, "r", encoding="utf-8") as f:
            tgt_src = f.read()

        # Load standard existing tests to provide styling structure
        full_test = os.path.join(payload.workspaceDir, payload.testFile)
        if not os.path.exists(full_test):
            fallback_test = "agent/test_hello.py"
            if is_cpp_source(payload.testFile):
                fallback_test = "agent/test_hello.c"
                if not os.path.exists(os.path.join(payload.workspaceDir, fallback_test)):
                    fallback_test = "agent/test_hello.cpp"
            full_test = os.path.join(payload.workspaceDir, fallback_test)

        existing_t = ""
        if os.path.exists(full_test):
            with open(full_test, "r", encoding="utf-8") as f:
                existing_t = f.read()[:1500] # trim context length limit

        language = detect_language_from_file_path(mutant.get("file_path", tgt_rel))
        ai_engine = build_ai_engine(language, payload.aiEngineProvider, payload.aiApiKey)
        ans = ai_engine.generate_test_to_kill_survivor(tgt_src, mutant, existing_t)
        proposed_tests.append({
            "filePath": payload.testFile,
            "lines": ans["test_code_lines"],
            "targetMutantId": m_id,
            "test_fn_name": ans.get("test_fn_name")
        })
        # Track generated tests by AI
        DATABASE["tests_generated_by_ai"] = DATABASE.get("tests_generated_by_ai", 0) + 1

    return {"proposedTests": proposed_tests}


# ══════════════════════════════════════════════════════════════
# Prometheus Telemetry Collector Metrics Exporters
# ══════════════════════════════════════════════════════════════

@app.get("/metrics")
def metrics():
    # Calculated aggregated statistics over active database state matching Prometheus formats
    runs = DATABASE["mutation_runs"]
    totals = 0
    survived = 0
    killed = 0

    for run_info in runs.values():
        if run_info["status"] == "COMPLETED":
            for r in run_info["results"]:
                totals += 1
                if r["status"] == "SURVIVED":
                    survived += 1
                else:
                    killed += 1

    ratio = (killed / totals) * 100.0 if totals > 0 else 100.0
    accepted_count = sum(1 for m in DATABASE["active_acceptance"].values() if m == "ACCEPTED")
    rejected_count = sum(1 for m in DATABASE["active_acceptance"].values() if m == "REJECTED")

    # Access custom baseline runs & AI test metrics
    baseline_count = DATABASE.get("baseline_runs_count", 0)
    baseline_passed = DATABASE.get("baseline_runs_passed", 0)
    baseline_failed = DATABASE.get("baseline_runs_failed", 0)
    ai_tests_generated = DATABASE.get("tests_generated_by_ai", 0)

    # Accumulate sandbox tests stats across completing background runs
    sandbox_passed = 0
    sandbox_failed = 0
    sandbox_total = 0
    for run_info in runs.values():
        if run_info["status"] == "COMPLETED":
            for r in run_info["results"]:
                sandbox_passed += r.get("testsPassed", 0)
                sandbox_failed += r.get("testsFailed", 0)
                sandbox_total += r.get("totalTests", 0)

    lines = [
        "# HELP mutation_vulnerability_score The percentage ratio of killed mutants over total run",
        "# TYPE mutation_vulnerability_score gauge",
        f"mutation_vulnerability_score {ratio:.2f}",
        "# HELP mutation_debt Accumulation count of survived mutants",
        "# TYPE mutation_debt gauge",
        f"mutation_debt {survived}",
        "# HELP mutations_generated_total Total occurrences of AST nodes mutated",
        "# TYPE mutations_generated_total counter",
        f"mutations_generated_total {len(DATABASE['mutations_cache'])}",
        "# HELP mutations_accepted_total Total mutants accepted by the user",
        "# TYPE mutations_accepted_total counter",
        f"mutations_accepted_total {accepted_count}",
        "# HELP mutations_rejected_total Total mutants rejected by the user",
        "# TYPE mutations_rejected_total counter",
        f"mutations_rejected_total {rejected_count}",
        "# HELP baseline_runs_total Total baseline test suites run",
        "# TYPE baseline_runs_total counter",
        f"baseline_runs_total {baseline_count}",
        "# HELP baseline_runs_passed_total Total baseline test suite executions that passed",
        "# TYPE baseline_runs_passed_total counter",
        f"baseline_runs_passed_total {baseline_passed}",
        "# HELP baseline_runs_failed_total Total baseline test suite executions that failed",
        "# TYPE baseline_runs_failed_total counter",
        f"baseline_runs_failed_total {baseline_failed}",
        "# HELP ai_tests_generated_total Total tests synthesized by AI to kill survivors",
        "# TYPE ai_tests_generated_total counter",
        f"ai_tests_generated_total {ai_tests_generated}",
        "# HELP sandbox_tests_passed_total Total unit tests that passed during sandbox execution runs",
        "# TYPE sandbox_tests_passed_total counter",
        f"sandbox_tests_passed_total {sandbox_passed}",
        "# HELP sandbox_tests_failed_total Total unit tests that failed (meaning they killed a mutant) during sandbox execution runs",
        "# TYPE sandbox_tests_failed_total counter",
        f"sandbox_tests_failed_total {sandbox_failed}",
        "# HELP sandbox_tests_run_total Total unit tests executed inside sandboxes",
        "# TYPE sandbox_tests_run_total counter",
        f"sandbox_tests_run_total {sandbox_total}"
    ]
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# Utility function
# ══════════════════════════════════════════════════════════════

def load_config() -> dict:
    default_config = {
        "core_service": {
            "host": "127.0.0.1",
            "port": 8000,
            "url": "http://127.0.0.1:8000"
        },
        "grafana": {
            "url": "http://localhost:3000"
        },
        "ai_engine_python": {
            "provider": "ollama",
            "openai_model": "gpt-4o",
            "ollama_model": "llama3",
            "openai_temperature": 0.1,
            "ollama_host": "http://localhost:11434",
            "ollama_timeout_seconds": 30,
            "openai_api_key_env": "OPENAI_API_KEY"
        },
        "ai_engine_cpp": {
            "provider": "openai",
            "openai_model": "gpt-4o",
            "ollama_model": "llama3",
            "openai_temperature": 0.1,
            "ollama_host": "http://localhost:11434",
            "ollama_timeout_seconds": 30,
            "openai_api_key_env": "OPENAI_API_KEY"
        },
        "ai_engine_c": {
            "provider": "openai",
            "openai_model": "gpt-4o",
            "ollama_model": "llama3",
            "openai_temperature": 0.1,
            "ollama_host": "http://localhost:11434",
            "ollama_timeout_seconds": 30,
            "openai_api_key_env": "OPENAI_API_KEY"
        },
        "ai_engine": {
            "provider": "mock",
            "openai_model": "gpt-4o",
            "ollama_model": "llama3",
            "openai_temperature": 0.1,
            "ollama_host": "http://localhost:11434",
            "ollama_timeout_seconds": 30,
            "openai_api_key_env": "OPENAI_API_KEY"
        },
        "workspace": {
            "default_source_file": "agent/hello.py",
            "default_test_file": "agent/test_hello.py",
            "test_runner": "pytest"
        }
    }

    def parse_scalar(val: str):
        if val.lower() in ["true", "false"]:
            return val.lower() == "true"
        if val.isdigit() or (val.startswith("-") and val[1:].isdigit()):
            return int(val)
        try:
            return float(val)
        except ValueError:
            return val

    # Lookup in parents to resolve absolute repo path
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "mutation_config.yml")
    if not os.path.exists(config_path):
        config_path = "mutation_config.yml"
        
    if os.path.exists(config_path):
        try:
            current_section = None
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_strip = line.strip()
                    if not line_strip or line_strip.startswith("#"):
                        continue
                    if ":" in line_strip:
                        parts = line_strip.split(":", 1)
                        key = parts[0].strip()
                        val = parts[1].strip().strip('"').strip("'")
                        if not val:  # section header
                            current_section = key
                        else:
                            if current_section and current_section in default_config:
                                default_config[current_section][key] = parse_scalar(val)
                            else:
                                default_config[key] = parse_scalar(val)
        except Exception as e:
            print(f"Error loading mutation_config.yml: {e}")
    return default_config


def tempfile_dir_root() -> str:
    path = os.path.join(tempfile.gettempdir(), "mutation-testing")
    os.makedirs(path, exist_ok=True)
    return path


APP_CONFIG = load_config()


if __name__ == "__main__":
    cfg = APP_CONFIG
    svc = cfg.get("core_service", {})
    host = svc.get("host", "127.0.0.1")
    port = svc.get("port", 8000)
    # Autostart daemon block
    uvicorn.run(app, host=host, port=port)
