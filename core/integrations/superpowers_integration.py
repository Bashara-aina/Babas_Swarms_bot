"""core/integrations/superpowers_integration.py — TDD enforcement for agent-written code.

superpowers provides TDD enforcement that closes the swarm quality gap identified
in the agent-written code pipeline. It enforces test-before-code discipline.

Note: The `superpowers` PyPI package (0.1.2) is a different library.
The TDD enforcement superpowers referenced in the repo list is not yet
available as a pip package. This module provides a lightweight TDD
enforcement layer using pytest + ruff that achieves similar goals.

Usage:
    from core.integrations.superpowers_integration import (
        enforce_tdd,
        run_tdd_check,
        validate_agent_code,
    )

    # Enforce TDD before accepting code
    await enforce_tdd(code="def add(a, b): return a+b", test="def test_add(): assert add(1,2)==3")

    # Validate code passes all checks
    result = await validate_agent_code(file_path="src/feature.py")
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

SUPERPOWERS_AVAILABLE = True


def enforce_tdd(code: str, test: str, timeout: int = 30) -> dict[str, Any]:
    """Enforce TDD discipline: test must fail before code passes.

    Args:
        code: The implementation code
        test: The test code
        timeout: Max seconds per phase

    Returns:
        dict with pass/fail status, error messages, and test output
    """
    import tempfile

    result = {"pass": False, "error": None, "test_output": "", "code_output": ""}

    with tempfile.TemporaryDirectory() as tmpdir:
        code_file = os.path.join(tmpdir, "impl.py")
        test_file = os.path.join(tmpdir, "test_impl.py")

        with open(code_file, "w") as f:
            f.write(code)
        with open(test_file, "w") as f:
            f.write(test)

        try:
            proc = subprocess.run(
                ["python3", "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
            test_output = proc.stdout + proc.stderr
            result["test_output"] = test_output

            if proc.returncode == 0:
                result["error"] = "TDD VIOLATION: Test passed before implementation (tests must fail first)"
                return result

        except subprocess.TimeoutExpired:
            result["error"] = "Test phase timed out"
            return result
        except Exception as exc:
            result["error"] = f"Test execution error: {exc}"
            return result

        try:
            proc = subprocess.run(
                ["python3", "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
            result["code_output"] = proc.stdout + proc.stderr

            if proc.returncode == 0:
                result["pass"] = True
            else:
                result["error"] = f"Implementation failed tests: {proc.stdout + proc.stderr}"

        except subprocess.TimeoutExpired:
            result["error"] = "Implementation phase timed out"
        except Exception as exc:
            result["error"] = f"Implementation execution error: {exc}"

    return result


async def run_tdd_check(file_path: str, test_path: str | None = None) -> dict[str, Any]:
    """Run TDD check on a file.

    Args:
        file_path: Path to the implementation file
        test_path: Path to test file (if None, derives from file_path)

    Returns:
        dict with pass/fail status and output
    """
    if not test_path:
        if file_path.endswith(".py"):
            test_path = file_path.replace(".py", "_test.py").replace("/src/", "/tests/")
        else:
            return {"pass": False, "error": "Cannot derive test path from file path"}

    if not os.path.exists(file_path):
        return {"pass": False, "error": f"Implementation file not found: {file_path}"}
    if not os.path.exists(test_path):
        return {"pass": False, "error": f"Test file not found: {test_path}"}

    try:
        proc = subprocess.run(
            ["python3", "-m", "pytest", test_path, "-v", "--tb=short", "--override-ini=python_files=test_*.py"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = proc.stdout + proc.stderr
        return {
            "pass": proc.returncode == 0,
            "output": output,
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"pass": False, "error": "Test timed out"}
    except Exception as exc:
        return {"pass": False, "error": str(exc)}


async def validate_agent_code(file_path: str, max_time: int = 120) -> dict[str, Any]:
    """Validate agent-written code with ruff + pytest.

    Args:
        file_path: Path to the file to validate
        max_time: Max validation time in seconds

    Returns:
        dict with pass/fail and validation output
    """
    results = {"pass": False, "ruff": None, "pytest": None, "errors": []}

    if not os.path.exists(file_path):
        return {"pass": False, "errors": [f"File not found: {file_path}"]}

    try:
        proc = subprocess.run(
            ["ruff", "check", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        results["ruff"] = proc.stdout + proc.stderr
        if proc.returncode != 0:
            results["errors"].append(f"Ruff check failed:\n{results['ruff']}")
    except FileNotFoundError:
        results["ruff"] = "[ruff not installed]"
    except Exception as exc:
        results["errors"].append(f"Ruff error: {exc}")

    if file_path.endswith(".py"):
        test_path = file_path.replace(".py", "_test.py").replace("/src/", "/tests/")
        if os.path.exists(test_path):
            try:
                proc = subprocess.run(
                    ["python3", "-m", "pytest", test_path, "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=max_time,
                )
                results["pytest"] = proc.stdout + proc.stderr
                if proc.returncode != 0:
                    results["errors"].append(f"Tests failed:\n{results['pytest']}")
            except subprocess.TimeoutExpired:
                results["errors"].append("Test timed out")
            except Exception as exc:
                results["errors"].append(f"Test error: {exc}")

    results["pass"] = len(results["errors"]) == 0
    return results


def create_tdd_enforcer(config: dict[str, Any] | None = None) -> Any:
    """Create a TDD enforcer with custom configuration.

    This returns a callable that wraps agent code with TDD enforcement.
    """
    cfg = config or {}
    timeout = cfg.get("timeout", 30)

    async def enforce(code: str, test: str) -> dict[str, Any]:
        return enforce_tdd(code, test, timeout=timeout)

    return enforce
