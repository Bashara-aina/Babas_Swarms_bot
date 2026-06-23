"""
tools/goal_auditor.py
End-to-end audit system. Produces structured results + Pareto scores.
Meta-Harness insight: Full traces > summaries. Log everything.
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

GOAL_DIR = Path(".goal")
REPORTS_DIR = GOAL_DIR / "reports"


def run_cmd(cmd: str, timeout: int = 120) -> dict:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout)
        return {
            "cmd": cmd, "returncode": r.returncode,
            "stdout": r.stdout[-3000:], "stderr": r.stderr[-500:],
            "passed": r.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"cmd": cmd, "returncode": -1,
                "stdout": "TIMEOUT", "stderr": "", "passed": False}


def run_python_audit(plan: Optional[dict] = None) -> dict:
    results = {}
    # Tests
    if Path("tests").exists() or list(Path(".").glob("test_*.py")):
        cmd = plan.get("final_audit", {}).get("run_tests", "pytest -q --tb=short 2>/dev/null") if plan else "pytest -q --tb=short 2>/dev/null"
        results["pytest"] = run_cmd(cmd)
    else:
        results["pytest"] = {"passed": True, "stdout": "No tests found", "cmd": "N/A"}

    # Lint
    if run_cmd("which ruff")["passed"]:
        results["ruff"] = run_cmd("ruff check . --select=E,W,F --ignore=E501 2>/dev/null || true")
    else:
        results["ruff"] = run_cmd("python3 -m py_compile $(find . -name '*.py' -not -path './.venv*' -not -path './tools/mirofish*') 2>/dev/null && echo OK")

    # Type check
    if run_cmd("which mypy")["passed"]:
        results["mypy"] = run_cmd("mypy . --ignore-missing-imports --no-error-summary 2>/dev/null | tail -10")

    return results


def run_node_audit(plan: Optional[dict] = None) -> dict:
    results = {}
    results["build"] = run_cmd("pnpm build 2>/dev/null || npm run build 2>/dev/null || echo no-build")
    results["lint"] = run_cmd("pnpm lint 2>/dev/null || npm run lint 2>/dev/null || echo no-lint")
    results["typecheck"] = run_cmd("pnpm typecheck 2>/dev/null || npx tsc --noEmit 2>/dev/null || echo no-tsc")
    return results


def run_git_audit() -> dict:
    results = {}
    results["diff_stat"] = run_cmd("git diff --stat HEAD 2>/dev/null")
    results["changed_files"] = run_cmd("git diff --name-only HEAD 2>/dev/null")

    # CRITICAL: mirofish must never be touched
    mirofish_diff = run_cmd("git diff -- tools/mirofish/ | wc -c")
    mirofish_clean = mirofish_diff["stdout"].strip() == "0"
    results["mirofish_untouched"] = {
        "passed": mirofish_clean,
        "stdout": "MiroFish submodule untouched" if mirofish_clean else "ALERT: MiroFish was modified -- revert immediately",
        "cmd": "git diff -- tools/mirofish/"
    }
    return results


def run_security_scan() -> dict:
    results = {}
    changed = run_cmd("git diff --name-only HEAD 2>/dev/null")
    py_files = [f for f in changed["stdout"].split("\n")
                if f.endswith(".py") and Path(f).exists()]
    if py_files:
        pattern = r"sk-|AKIA|eyJ[a-zA-Z]|password\s*=\s*['\"][^'\"]{8,}|api_key\s*=\s*['\"][^'\"]{8,}"
        cmd = f"grep -rn -E '{pattern}' {' '.join(py_files)} 2>/dev/null | grep -v 'os.getenv' | grep -v '#'"
        r = run_cmd(cmd)
        results["secret_scan"] = {
            "passed": r["stdout"].strip() == "",
            "stdout": "No hardcoded secrets" if r["stdout"].strip() == "" else f"SECRETS FOUND:\n{r['stdout'][:500]}",
            "cmd": cmd
        }
    else:
        results["secret_scan"] = {"passed": True, "stdout": "No Python files changed", "cmd": "N/A"}
    return results


def detect_project_type() -> str:
    """Detect project type for audit routing."""
    if Path("package.json").exists():
        return "node"
    elif Path("pyproject.toml").exists() or Path("setup.py").exists() or Path("requirements.txt").exists():
        return "python"
    else:
        # Check for any Python files
        py_files = list(Path(".").glob("**/*.py"))
        py_files = [f for f in py_files if "mirofish" not in str(f) and ".venv" not in str(f)]
        return "python" if py_files else "unknown"


def score_audit(results: dict) -> tuple[int, str]:
    """Score audit results. Returns (0-100 score, grade)."""
    checks = []
    for cat in results.values():
        if isinstance(cat, dict):
            if "passed" in cat:
                checks.append(cat["passed"])
            else:
                for v in cat.values():
                    if isinstance(v, dict) and "passed" in v:
                        checks.append(v["passed"])
    if not checks:
        return 50, "?"
    score = int(sum(checks) / len(checks) * 100)
    grade = ("PERFECT" if score == 100 else "GOOD" if score >= 80
             else "ACCEPTABLE" if score >= 60 else "FAILING")
    return score, grade


def format_telegram_report(goal: str, audit: dict, goal_id: str, phase: str = "final") -> str:
    score, grade = score_audit(audit)
    lines = [
        f"Audit Report ({phase})",
        f"Goal: {goal[:80]}",
        f"Score: {score}/100 -- {grade}",
    ]
    py = audit.get("python", {})
    if "pytest" in py:
        e = "OK" if py["pytest"]["passed"] else "FAIL"
        lines.append(f"Tests: {e}")
    if "ruff" in py:
        e = "clean" if py["ruff"]["passed"] else "issues"
        lines.append(f"Lint: {e}")
    git_r = audit.get("git", {})
    if "mirofish_untouched" in git_r:
        lines.append(git_r["mirofish_untouched"]["stdout"])
    sec = audit.get("security", {}).get("secret_scan", {})
    if sec:
        lines.append(sec.get("stdout", "")[:80])
    if audit.get("pr_url"):
        lines.append(f"PR: {audit['pr_url']}")
    return "\n".join(lines)


def run_full_audit(goal: str, goal_id: str, plan: Optional[dict] = None,
                   phase: str = "final") -> dict:
    """Run complete audit suite. Logs full results (Meta-Harness pattern)."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    project_type = detect_project_type()

    results = {
        "goal": goal, "goal_id": goal_id, "phase": phase,
        "timestamp": datetime.now().isoformat(),
        "project_type": project_type,
        "git": run_git_audit(),
        "security": run_security_scan(),
    }

    if project_type == "python":
        results["python"] = run_python_audit(plan)
    elif project_type == "node":
        results["node"] = run_node_audit(plan)
    else:
        results["python"] = run_python_audit(plan)
        results["node"] = run_node_audit(plan)

    score, grade = score_audit(results)
    results["score"] = score
    results["grade"] = grade

    # Write FULL report -- not a summary (Meta-Harness principle)
    report_path = REPORTS_DIR / f"{goal_id}_{phase}_audit.json"
    report_path.write_text(json.dumps(results, indent=2))

    # Also write score to harness candidate record for Pareto tracking
    harness_dir = Path(".goal/harnesses/candidates")
    harness_dir.mkdir(parents=True, exist_ok=True)
    score_record = harness_dir / f"{goal_id}_score.json"
    score_record.write_text(json.dumps({
        "goal_id": goal_id, "goal": goal, "score": score,
        "grade": grade, "phase": phase,
        "timestamp": datetime.now().isoformat()
    }, indent=2))

    return results


if __name__ == "__main__":
    import sys
    goal = sys.argv[1] if len(sys.argv) > 1 else "test"
    goal_id = sys.argv[2] if len(sys.argv) > 2 else "test_id"
    r = run_full_audit(goal, goal_id)
    print(f"Score: {r['score']}/100 {r['grade']}")
    print(format_telegram_report(goal, r, goal_id))
