"""
run_agents.py — All-in-one Mutation Testing Agent Pipeline
===========================================================

4 agents run in sequence from this single file:
  Agent 1 — TestAgent          : baseline pytest must pass
  Agent 2 — MutationAgent      : runs mutmut, finds survivors
  Agent 3 — ReviewAgent        : Claude AI generates tests to kill survivors
  Agent 4 — KillVerifierAgent  : re-runs mutmut, confirms all dead

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python run_agents.py

Options:
    --api-key   sk-ant-...   (alternative to env var)
    --project   /path/       (default: folder containing this script)
"""

import os
import re
import sys
import argparse
import subprocess
import requests


# ══════════════════════════════════════════════════════════════
# AGENT 1 — TestAgent
# ══════════════════════════════════════════════════════════════

class TestAgent:
    """Verifies the baseline test suite passes before anything else runs."""

    def __init__(self, project_root: str):
        self.root = project_root

    def run(self) -> bool:
        _banner("Agent 1 · TestAgent", "🧪", "Running baseline pytest…")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-v"],
            cwd=self.root, capture_output=True, text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            print("❌ Baseline tests FAILED — fix them before mutating.")
            print(result.stderr)
            return False
        print("✅ All baseline tests passed.\n")
        return True


# ══════════════════════════════════════════════════════════════
# AGENT 2 — MutationAgent
# ══════════════════════════════════════════════════════════════

class MutationAgent:
    """Runs mutmut and returns a list of surviving mutations."""

    def __init__(self, project_root: str):
        self.root = project_root

    def run(self) -> list[dict]:
        _banner("Agent 2 · MutationAgent", "🧬", "Running mutmut…")
        run_out = subprocess.run(
            ["mutmut", "run"],
            cwd=self.root, capture_output=True, text=True,
        )
        print(run_out.stdout)
        if run_out.stderr:
            print(run_out.stderr)

        res_out = subprocess.run(
            ["mutmut", "results"],
            cwd=self.root, capture_output=True, text=True,
        )
        print("📊 Results:\n", res_out.stdout)

        mutations = self._parse_surviving(res_out.stdout)
        if mutations:   
                print(f"⚠️  {len(mutations)} mutant(s) survived: {mutations}")
        else:
                print("✅ No surviving mutants!")
        return mutations

    def get_diff(self, mutant_id: int) -> str:
        r = subprocess.run(
            ["mutmut", "show", str(mutant_id)],
            cwd=self.root, capture_output=True, text=True,
        )
        return r.stdout

    @staticmethod
    def parse_diff(diff_text):
        original = None
        mutated = None

        for line in diff_text.splitlines():
            if line.startswith("-"):
                original = line[1:].strip()

            if line.startswith("+"):
                mutated = line[1:].strip()

        return {
            "original": original,
            "mutated": mutated
        }
    
    @staticmethod
    def extract_location(diff_text):
        file_name = None
        line_number = None

        for line in diff_text.splitlines():

            if line.startswith("--- "):
                file_name = line[4:].strip()

            match = re.search(r'@@ -(\d+)', line)
            if match:
                line_number = int(match.group(1))

        return file_name, line_number

    def get_mutant_details(self, mutant_id: str) -> str:
        result = subprocess.run(
            ["mutmut", "show", mutant_id],
            cwd=self.root,
            capture_output=True,
            text=True
        )
        return result.stdout

    def _parse_surviving(self, output: str) -> list[dict]:
        mutations = []
        for line in output.splitlines():
            line = line.strip()
            if "survived" in line.lower():
                match = re.search(r"__mutmut_(\d+)", line)
                match = re.search(r"^([^:]+):", line)
                if match:
                    mutant_id = match.group(1)
                    print(f"Found surviving mutant in line: {mutant_id}")
                    mutdetails = self.get_mutant_details(mutant_id)
                    line_diff = MutationAgent.parse_diff(mutdetails)
                    file_name, line_number = MutationAgent.extract_location(mutdetails)
                    mutations.append({
                        "mutant_id": mutant_id,
                        "original": line_diff["original"],
                        "mutated": line_diff["mutated"],
                        "file_name": file_name,
                        "line_number": line_number,
                        "status": "SURVIVED"
                    })
                # if match:
                #     mutant_id = int(match.group(1))
        return mutations

# ══════════════════════════════════════════════════════════════
# AGENT 3 — ReviewAgent  (AI-powered)
# ══════════════════════════════════════════════════════════════

class ReviewAgent:
    """
    For every surviving mutant:
      • sends the diff + source + existing tests to Claude
      • gets a new pytest function back
      • appends it to test_hello.py
    """

    API_URL = "https://api.anthropic.com/v1/messages"
    MODEL   = "claude-sonnet-4-20250514"

    def __init__(self, project_root: str, api_key: str):
        self.root    = project_root
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set.")

    def run(self, surviving_ids: list[dict], mutation_agent: MutationAgent) -> None:
        _banner("Agent 3 · ReviewAgent", "🤖", "Generating kill-tests with Claude AI…")

        if not surviving_ids:
            print("✅ Nothing to kill.\n")
            return

        new_tests: list[str] = []

        for mutation in surviving_ids:
            mid = mutation["mutant_id"]
            diff = mutation_agent.get_diff(mid)
            print(f"\n── Mutant #{mid} ──\n{diff}")
            code = self._ask_claude(mid, diff)
            if code:
                print(f"💡 Generated:\n{code}\n")
                new_tests.append(code)
            else:
                print(f"⚠️  No test generated for mutant #{mid}.")

        if new_tests:
            self._append(new_tests)
            print(f"✅ {len(new_tests)} new test(s) appended to test_hello.py\n")
        else:
            print("⚠️  No new tests were generated.\n")

    # ── Claude API ────────────────────────────────────────────

    def _ask_claude(self, mutant_id: int, diff: str) -> str:
        src   = self._read("hello.py")
        tests = self._read("test_hello.py")

        prompt = f"""You are a Python test engineer.

## Source file (hello.py)
```python
{src}
```

## Existing tests (test_hello.py)
```python
{tests}
```

## Surviving mutant #{mutant_id} — diff
```diff
{diff}
```

## Task
Write ONE new pytest test function that:
- Is named `test_kill_mutant_{mutant_id}`
- Needs NO extra imports (hello is already imported at the top of test_hello.py)
- PASSES on the original source code
- FAILS on the mutated version shown in the diff above

Return ONLY the raw Python function — no markdown fences, no explanation.
"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        body = {
            "model": self.MODEL,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = requests.post(self.API_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        raw = "".join(
            b.get("text", "") for b in resp.json().get("content", [])
            if b.get("type") == "text"
        )
        return re.sub(r"```(?:python)?", "", raw).replace("```", "").strip()

    # ── helpers ───────────────────────────────────────────────

    def _read(self, filename: str) -> str:
        with open(os.path.join(self.root, filename)) as f:
            return f.read()

    def _append(self, tests: list[str]) -> None:
        path = os.path.join(self.root, "test_hello.py")
        with open(path, "a") as f:
            f.write("\n\n# ── AI-generated tests to kill surviving mutants ──\n")
            for t in tests:
                f.write("\n" + t + "\n")


# ══════════════════════════════════════════════════════════════
# AGENT 4 — KillVerifierAgent
# ══════════════════════════════════════════════════════════════

class KillVerifierAgent:
    """Re-runs mutmut to confirm every mutant is now dead."""

    def __init__(self, project_root: str):
        self.root = project_root

    def run(self) -> bool:
        _banner("Agent 4 · KillVerifierAgent", "🔁", "Re-running mutmut to verify kills…")

        # Re-run pytest first so we know new tests don't break anything
        pytest_ok = self._run_pytest()
        if not pytest_ok:
            return False

        subprocess.run(
            ["mutmut", "run", "--rerun-all"],
            cwd=self.root, capture_output=True, text=True,
        )
        res = subprocess.run(
            ["mutmut", "results"],
            cwd=self.root, capture_output=True, text=True,
        )
        print(res.stdout)

        surviving = MutationAgent(self.root)._parse_surviving(res.stdout)
        if not surviving:
            print("ALL mutants killed — your test suite is solid!\n")
            return True
        print(
            f"⚠️  {len(surviving)} mutant(s) still alive: {surviving}\n"
            "    Re-run the agent or add manual tests.\n"
        )
        return False

    def _run_pytest(self) -> bool:
        print("🧪 Final pytest check…")
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-v"],
            cwd=self.root, capture_output=True, text=True,
        )
        print(r.stdout)
        if r.returncode != 0:
            print("Final pytest failed!\n", r.stderr)
            return False
        print("Final pytest passed.\n")
        return True


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _banner(title: str, icon: str, subtitle: str) -> None:
    print("\n" + "═" * 60)
    print(f"{icon}  {title}")
    print(f"   {subtitle}")
    print("═" * 60)


# ══════════════════════════════════════════════════════════════
# Orchestrator
# ══════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="AI mutation-testing pipeline")
    parser.add_argument(
        "--project",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Path to project root (default: folder containing this script)",
    )
    parser.add_argument("--api-key", default="", help="Anthropic API key")
    args = parser.parse_args()

    root    = os.path.abspath(args.project)
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    print(f"\nMutation Testing Agent Pipeline")
    print(f"    Project : {root}\n")

    # ── 1. Baseline tests ────────────────────────────────────
    if not TestAgent(root).run():
        print("Aborting — fix baseline tests first.")
        sys.exit(1)

    # ── 2. Mutation run ──────────────────────────────────────
    mutation_agent = MutationAgent(root)
    surviving      = mutation_agent.run()

    if not surviving:
        print("\n No survivors — nothing for the AI to do. You're done!")
        sys.exit(0)

    # ── 3. AI kill-test generation ───────────────────────────
    ReviewAgent(root, api_key).run(surviving, mutation_agent)

    # ── 4. Verify kills ──────────────────────────────────────
    all_killed = KillVerifierAgent(root).run()

    if all_killed:
        print("Mission complete — all mutants killed by AI-generated tests!")
    else:
        print("Some mutants survived. Re-run or add manual tests.")
        sys.exit(1)


if __name__ == "__main__":
    main()
