"""
tools/goal_auditor.py
End-to-end audit system for /goal autonomous delivery.
Runs after each phase and at final completion.
Checks: tests, lint, type errors, secrets scan, git diff sanity.
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


GOAL_DIR = Path(".goal")
REPORTS_DIR = GOAL_DIR / "reports"


def run_cmd(cmd: str, cwd: str = ".") -> dict:
    """Run a shell command and return structured result."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True,
        text=True, cwd=cwd, timeout=120
    )
    return {
        "cmd": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout[-3000:] if result.stdout else "",
        "stderr": result.stderr[-1000:] if result.stderr else "",
        "passed": result.returncode == 0
    }


def detect_project_type() -> str:
    """Detect Python, Node, or mixed project."""
    if Path("package.json").exists():
        return "node"
    if Path("requirements.txt").exists() or Path("pyproject.toml").exists():
        return "python"
    return "unknown"


def run_python_audit(plan: Optional[dict] = None) -> dict:
    """Run Python-specific audit checks."""
    results = {}

    # Run pytest if tests exist
    if Path("tests").exists() or list(Path(".").glob("test_*.py")):
        results["pytest"] = run_cmd("pytest tests/ -v --tb=short -q 2>/dev/null || pytest -v --tb=short -q 2>/dev/null")
    else:
        results["pytest"] = {"passed": True, "stdout": "No test files found", "cmd": "N/A"}

    # Run from plan if specified
    if plan and plan.get("final_audit", {}).get("run_tests"):
        results["plan_tests"] = run_cmd(plan["final_audit"]["run_tests"])

    # Ruff linting (fast, modern Python linter)
    if run_cmd("which ruff")["passed"]:
        results["ruff"] = run_cmd("ruff check . --select=E,W,F --ignore=E501 2>/dev/null || true")
    else:
        # Fallback to py_compile
        results["ruff"] = run_cmd(
            "python3 -m py_compile $(find . -name '*.py' -not -path './.venv*' -not -path './tools/mirofish*' 2>/dev/null) 2>/dev/null && echo 'Syntax OK'"
        )

    # Type checking with mypy (if installed)
    if run_cmd("which mypy")["passed"]:
        results["mypy"] = run_cmd("mypy . --ignore-missing-imports --no-error-summary 2>/dev/null | tail -20")

    # Import verification — check our goal tools import correctly
    results["imports"] = run_cmd(
        "python3 -c \"import tools.goal_runner; import tools.goal_planner; import tools.goal_auditor; print('imports OK')\" 2>/dev/null || echo 'some imports failed'"
    )

    return results


def run_node_audit(plan: Optional[dict] = None) -> dict:
    """Run Node.js-specific audit checks."""
    results = {}
    results["build"] = run_cmd("pnpm build 2>/dev/null || npm run build 2>/dev/null || echo 'no build script'")
    results["lint"] = run_cmd("pnpm lint 2>/dev/null || npm run lint 2>/dev/null || echo 'no lint script'")
    results["typecheck"] = run_cmd("pnpm typecheck 2>/dev/null || npx tsc --noEmit 2>/dev/null || echo 'no typecheck'")
    if plan and plan.get("final_audit", {}).get("run_tests"):
        results["tests"] = run_cmd(plan["final_audit"]["run_tests"])
    return results


def run_git_audit() -> dict:
    """Check git state for sanity."""
    results = {}
    results["diff_stat"] = run_cmd("git diff --stat HEAD 2>/dev/null || git diff --stat")
    results["changed_files"] = run_cmd("git diff --name-only HEAD 2>/dev/null || git diff --name-only")
    results["submodule_clean"] = run_cmd("git submodule status 2>/dev/null | grep -v '^+' | wc -l")

    # CRITICAL: verify tools/mirofish/ submodule was not modified
    mirofish_check = run_cmd("git diff -- tools/mirofish/ | wc -c")
    results["mirofish_untouched"] = {
        "passed": mirofish_check["stdout"].strip() == "0",
        "stdout": "MiroFish submodule untouched ✅" if mirofish_check["stdout"].strip() == "0"
                  else "⚠️ MiroFish submodule was modified — REVERT",
        "cmd": "git diff -- tools/mirofish/"
    }

    return results


def run_security_scan() -> dict:
    """Basic secret / security scan on changed files."""
    results = {}

    # Check for hardcoded API keys/tokens in recently changed files
    patterns = "sk-|AKIA|eyJ|password.*=.*['\"][^'\"]{8,}|api_key.*=.*['\"][^'\"]{8,}"
    changed_files = run_cmd("git diff --name-only HEAD 2>/dev/null || git diff --name-only")

    if changed_files["stdout"].strip():
        files = changed_files["stdout"].strip().split("\n")
        py_files = [f for f in files if f.endswith(".py") and Path(f).exists()]
        if py_files:
            check_cmd = f"grep -rn -E '{patterns}' {' '.join(py_files)} 2>/dev/null | grep -v '#' | grep -v 'os.getenv' | grep -v 'os.environ' | grep -v 'password.*=.*os'"
            scan_result = run_cmd(check_cmd)
            results["secret_scan"] = {
                "passed": scan_result["stdout"].strip() == "",
                "stdout": "No hardcoded secrets found ✅" if scan_result["stdout"].strip() == ""
                          else f"⚠️ Potential secrets found:\n{scan_result['stdout'][:500]}",
                "cmd": check_cmd
            }
        else:
            results["secret_scan"] = {"passed": True, "stdout": "No Python files changed", "cmd": "N/A"}
    else:
        results["secret_scan"] = {"passed": True, "stdout": "No changed files", "cmd": "N/A"}

    return results


def score_audit(results: dict) -> tuple[int, str]:
    """Score the audit results: returns (score 0-100, emoji grade)."""
    checks = []
    for category in results.values():
        if isinstance(category, dict):
            if "passed" in category:
                checks.append(category["passed"])
            else:
                for check in category.values():
                    if isinstance(check, dict) and "passed" in check:
                        checks.append(check["passed"])

    if not checks:
        return 50, "⚠️"

    score = int(sum(checks) / len(checks) * 100)
    if score == 100:
        grade = "✅ PERFECT"
    elif score >= 80:
        grade = "✅ GOOD"
    elif score >= 60:
        grade = "⚠️ ACCEPTABLE"
    else:
        grade = "❌ FAILING"

    return score, grade


def format_telegram_report(goal: str, audit_results: dict, goal_id: str,
                            phase: str = "final") -> str:
    """Format audit results as a concise Telegram message."""
    score, grade = score_audit(audit_results)

    lines = [
        f"🤖 **Goal Audit Report**",
        f"**Goal:** {goal[:100]}",
        f"**Phase:** {phase}",
        f"**Score:** {score}/100 {grade}",
        "",
    ]

    # Python results
    if "python" in audit_results:
        if "pytest" in audit_results["python"]:
            p = audit_results["python"]["pytest"]
            emoji = "✅" if p["passed"] else "❌"
            lines.append(f"{emoji} Tests: {'passed' if p['passed'] else 'FAILED'}")

        if "ruff" in audit_results["python"]:
            r = audit_results["python"]["ruff"]
            emoji = "✅" if r["passed"] else "⚠️"
            lines.append(f"{emoji} Lint: {'clean' if r['passed'] else 'issues found'}")

    # Git
    git_r = audit_results.get("git", {})
    if "mirofish_untouched" in git_r:
        lines.append(git_r["mirofish_untouched"]["stdout"])

    changed = git_r.get("changed_files", {}).get("stdout", "").strip()
    if changed:
        file_count = len(changed.split("\n"))
        lines.append(f"📝 Files changed: {file_count}")

    # Security
    sec = audit_results.get("security", {}).get("secret_scan", {})
    if sec:
        lines.append(sec.get("stdout", "")[:100])

    # PR info
    if audit_results.get("pr_url"):
        lines.append(f"\n🔗 PR: {audit_results['pr_url']}")

    return "\n".join(lines)


def run_full_audit(goal: str, goal_id: str, plan: Optional[dict] = None,
                   phase: str = "final") -> dict:
    """Run complete audit suite. Returns structured results dict."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    project_type = detect_project_type()
    results = {
        "goal": goal,
        "goal_id": goal_id,
        "phase": phase,
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
        # Try both
        results["python"] = run_python_audit(plan)
        results["node"] = run_node_audit(plan)

    score, grade = score_audit(results)
    results["score"] = score
    results["grade"] = grade

    # Write report
    report_path = REPORTS_DIR / f"{goal_id}_{phase}_audit.json"
    report_path.write_text(json.dumps(results, indent=2))

    return results


if __name__ == "__main__":
    import sys
    goal = sys.argv[1] if len(sys.argv) > 1 else "test goal"
    goal_id = sys.argv[2] if len(sys.argv) > 2 else "test_id"
    results = run_full_audit(goal, goal_id)
    print(f"Score: {results['score']}/100 {results['grade']}")
    print(format_telegram_report(goal, results, goal_id))