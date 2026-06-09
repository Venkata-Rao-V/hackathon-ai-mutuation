"""
run_all.py — End-to-End Orchestrator and Integration Verification Pipeline
========================================================================
Installs dependencies, starts the FastAPI daemon, invokes the Core API service endpoints,
coordinates sandbox execution pools, and proves the whole platform is fully functional.
"""

import os
import sys
import time
import subprocess
import requests

def main():
    print("=" * 70)
    print("🧬  Initializing Mutation Testing Platform Orchestrator")
    print("=" * 70)

    # 1. Install workspace dependencies
    print("\n🔍 Step 1: Checking and installing workspace dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True
        )
        print("✅ Dependencies verified successfully.")
    except Exception as e:
        print(f"⚠️  Could not run pip install: {e}. Attempting execution anyway...")

    # 2. Spin up FastAPI Backend Service in background
    print("\n🚀 Step 2: Spinning up FastAPI Core Mutation Service in background...")
    service_path = os.path.join("agent", "services", "core_mutation_service.py")
    
    # We run the FastAPI service locally on port 8000
    p = subprocess.Popen(
        [sys.executable, service_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for startup confirmation
    service_url = "http://127.0.0.1:8000"
    retries = 10
    started = False
    for i in range(retries):
        try:
            resp = requests.get(f"{service_url}/health", timeout=1)
            if resp.status_code == 200:
                started = True
                print("✅ Core Mutation Service is ONLINE & healthy.")
                break
        except requests.exceptions.ConnectionError:
            time.sleep(1)

    if not started:
        print("❌ Error: Core Mutation Service backend failed to start.")
        p.terminate()
        sys.exit(1)

    try:
        # 3. Establish Golden Master Baseline Test-Run
        print("\n🧪 Step 3: Triggering 'Golden Master' baseline tests execution...")
        ws_dir = os.path.abspath(os.path.dirname(__file__))
        
        base_resp = requests.post(f"{service_url}/api/v1/projects/default/test-runs/baseline", json={
            "workspaceDir": ws_dir,
            "testRunner": "pytest"
        })
        base_data = base_resp.json()
        print(f"📊 Baseline Status: {base_data.get('status')} | Duration: {base_data.get('durationMs')}ms")
        
        if base_data.get("status") != "SUCCESS":
            print("❌ Baseline tests are failing! Fix existing tests first.")
            sys.exit(1)

        # 4. AST Scan and Generation
        print("\n🧬 Step 4: Invoking Tree-sitter Pluggable Adapter for AST scan...")
        gen_resp = requests.post(f"{service_url}/api/v1/projects/default/mutations/generate", json={
            "workspaceDir": ws_dir,
            "targetFiles": [os.path.join("agent", "hello.py")],
            "operators": ["arithmetic", "conditional_boundary", "logical"],
            "aiEngineProvider": "mock"
        })
        gen_data = gen_resp.json()
        mutants = gen_data.get("mutants", [])
        print(f"✅ AST scan complete. Identified {len(mutants)} mutant candidates.")

        if not mutants:
            print("⚠️  No mutants discovered. Finishing process.")
            sys.exit(0)

        # Print some example mutants
        for m in mutants[:3]:
            print(f"   • {m['mutant_id']}: Line {m['line_number']} [{m['operator_type']}] - '{m['original_code']}' -> '{m['mutated_value']}'")
        if len(mutants) > 3:
            print(f"   • ... and {len(mutants) - 3} more candidates.")

        # 5. Execute Mutants in Isolated Sandboxes
        print("\n⚡ Step 5: Executing Mutants in background Sandbox workers...")
        mutant_ids = [m["mutant_id"] for m in mutants]
        
        exec_resp = requests.post(f"{service_url}/api/v1/projects/default/test-runs", json={
            "workspaceDir": ws_dir,
            "mutantIds": mutant_ids
        })
        run_id = exec_resp.json().get("runId")
        print(f"🕒 Submitted Run Session: {run_id}. Polling execution queue status...")

        while True:
            time.sleep(1)
            status_resp = requests.get(f"{service_url}/api/v1/projects/default/test-runs/{run_id}/status")
            status_data = status_resp.json()
            if status_data.get("status") == "COMPLETED":
                results = status_data.get("results", [])
                break

        # Calculate Mutation Score
        killed = len([r for r in results if r["status"] == "KILLED"])
        survived = len([r for r in results if r["status"] == "SURVIVED"])
        score = (killed / len(results)) * 100 if results else 0

        print(f"\n📊 Mutation Execution Summary:")
        print(f"   • Total Mutants Executed: {len(results)}")
        print(f"   • Killed: {killed}")
        print(f"   • Survived: {survived}")
        print(f"   • Mutation Score: {score:.1f}%")

        # 6. AI-Powered Test Cases Generation for Survivors
        survivor_records = [r for r in results if r["status"] == "SURVIVED"]
        if survivor_records:
            print(f"\n🤖 Step 6: Querying Generative AI Engine to proposed tests to kill {survivor_records[0]['mutantId']}...")
            ai_resp = requests.post(f"{service_url}/api/v1/projects/default/tests/generate", json={
                "workspaceDir": ws_dir,
                "survivingMutantIds": [survivor_records[0]["mutantId"]],
                "targetFiles": [os.path.join("agent", "hello.py")],
                "testFile": os.path.join("agent", "test_hello.py"),
                "aiEngineProvider": "mock"
            })
            ai_data = ai_resp.json()
            proposed = ai_data.get("proposedTests", [])[0]
            print(f"💡 AI Proposed Test block appending to {proposed['filePath']}:")
            for line in proposed["lines"]:
                print(f"   {line}")
        else:
            print("\n✅ Perfect test assertion protection! No mutants survived.")

        print("\n" + "=" * 70)
        print("🎉 Integration Verification Run complete! Core API & sandbox is solid.")
        print("=" * 70)

    finally:
        # Kill backend service after verification completes
        p.terminate()

if __name__ == "__main__":
    main()
