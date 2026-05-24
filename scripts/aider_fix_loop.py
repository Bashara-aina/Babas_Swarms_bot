#!/usr/bin/env python3
"""aider_fix_loop.py — Self-correcting test-fix cycle powered by MiniMax M2.7.

Cascade order: MiniMax-M2.7 → MiniMax-Text-01 → ollama_chat/llama3.3:70b (MiniMax-only, no external providers)

Usage:
    python scripts/aider_fix_loop.py                  # default: pytest tests/
    python scripts/aider_fix_loop.py --test-cmd "ruff check ." --max-retries 5

Integration with task_orchestrator.py:
    - Called as a standalone script for autonomous self-fix workflows
    - Imports FALLBACK_CHAIN from agents/__init__.py for model cascade
    - Returns exit code 0 on success, 1 on failure/escalation
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass

# ── MiniMax API config (mirrors what agents/__init__.py uses) ─────────────────
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")

# ── MiniMax-only cascade (no gemini, no deepseek — MiniMax only) ───────────────
MODEL_CASCADE: list[dict[str, str]] = [
    {"model": "minimax-coding-plan/MiniMax-M2.7", "label": "MiniMax M2.7"},
]

# ── Test command defaults ─────────────────────────────────────────────────────
# NOTE: test_integration.py excluded — it imports minisweagent which is not installed
# in the venv (RuntimeError at import). Use test_integrations.py for the fix loop.
DEFAULT_TEST_CMD = (
    "/home/newadmin/swarm-bot/.venv/bin/pytest "
    "tests/test_integrations.py -x --tb=short -q"
)
DEFAULT_MAX_RETRIES = 10
DEFAULT_AIDER_MODEL = "openai/MiniMax-M2.7"

# ── Aider binary (system-wide install) ────────────────────────────────────────
AIDER_BIN = "/home/newadmin/.local/bin/aider"


@dataclass
class LoopResult:
    success: bool
    attempts: int
    final_model: str
    elapsed_sec: float
    error_msg: str = ""


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_aider_env() -> dict:
    """Build a clean env dict for aider subprocess."""
    env = os.environ.copy()
    env["OPENAI_API_BASE"] = MINIMAX_BASE_URL
    if MINIMAX_API_KEY:
        env["OPENAI_API_KEY"] = MINIMAX_API_KEY
    return env


def _run_tests(test_cmd: str) -> tuple[int, str]:
    """Run test command, return (exit_code, combined_output)."""
    result = subprocess.run(
        test_cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    combined = f"{result.stdout}\n{result.stderr}"
    return result.returncode, combined


def _call_aider(model: str, failure_msg: str, yes: bool = True) -> tuple[int, str]:
    """Call aider with --message to inject failure context non-interactively."""
    cmd = [
        AIDER_BIN,
        "--model", model,
        "--yes" if yes else "--no-yes",
        "--no-pretty",
        "--no-git",
        "--message", f"Fix these test failures. Return ONLY the fixed code — no explanation:\n\n{failure_msg}",
    ]
    result = subprocess.run(
        cmd,
        env=_build_aider_env(),
        capture_output=True,
        text=True,
    )
    return result.returncode, f"{result.stdout}\n{result.stderr}"


# ── Main loop ─────────────────────────────────────────────────────────────────

def run_fix_loop(
    test_cmd: str = DEFAULT_TEST_CMD,
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_model: str = DEFAULT_AIDER_MODEL,
) -> LoopResult:
    """Run the self-fix loop.

    1. Run tests
    2. On failure: feed failure to aider with current model via --message
    3. On API error (rate limit / auth failure): cascade to next model
    4. On test success: return success
    5. On max retries: return failure with last model used
    """
    start = time.monotonic()
    current_model = initial_model
    model_index = 0
    attempt = 0
    last_error = ""

    # Resolve initial model to cascade index
    for i, m in enumerate(MODEL_CASCADE):
        if m["model"].replace("minimax/", "").replace("gemini/", "").replace("openrouter/", "") \
                in initial_model.replace("minimax/", "").replace("gemini/", "").replace("openrouter/", ""):
            model_index = i
            current_model = m["model"]
            break

    while attempt < max_retries:
        # ── STEP 1: Run tests ──────────────────────────────────────────────────
        attempt += 1
        is_first_run = (attempt == 1)
        retry_label = f"(retry {attempt}/{max_retries})" if not is_first_run else "(initial run)"

        print(f"\n{'='*60}")
        print(f"  [{current_model.split('/')[-1]}] {retry_label}")
        print(f"  Test cmd: {test_cmd}")
        print(f"{'='*60}")

        exit_code, output = _run_tests(test_cmd)

        if exit_code == 0:
            elapsed = time.monotonic() - start
            print(f"\n✅ All tests passed on attempt {attempt}")
            print(f"   Model: {current_model}")
            print(f"   Time: {elapsed:.1f}s")
            return LoopResult(
                success=True,
                attempts=attempt,
                final_model=current_model,
                elapsed_sec=elapsed,
            )

        # Tests failed — show output
        print(f"\n❌ Tests failed. Feeding output to aider...")
        failure_excerpt = output[:3000]
        print(f"   Failure excerpt:\n{failure_excerpt[:500]}...")

        # ── STEP 2: Feed failure to aider ──────────────────────────────────────
        aider_code, aider_output = _call_aider(current_model, output)

        if aider_code != 0:
            # API error — escalate model
            last_error = aider_output[:500]
            print(f"\n⚠️  Aider API error (exit {aider_code}):")
            print(f"   {last_error[:300]}")

            # Try next model in cascade
            if model_index + 1 < len(MODEL_CASCADE):
                model_index += 1
                current_model = MODEL_CASCADE[model_index]["model"]
                print(f"\n🔄 Escalating to: {MODEL_CASCADE[model_index]['label']}")
                # Do NOT count this as a retry — the model switch IS the retry
                continue
            else:
                print(f"\n❌ All models exhausted. Last error:\n{last_error}")
                return LoopResult(
                    success=False,
                    attempts=attempt,
                    final_model=current_model,
                    elapsed_sec=time.monotonic() - start,
                    error_msg=last_error,
                )

        print(f"\n   Aider applied edits (exit {aider_code})")
        print(f"   Output: {aider_output[:300]}...")

    # Exceeded max_retries
    return LoopResult(
        success=False,
        attempts=attempt,
        final_model=current_model,
        elapsed_sec=time.monotonic() - start,
        error_msg="Max retries exceeded",
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Self-correcting test-fix loop using MiniMax M2.7 via aider --message",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/aider_fix_loop.py
  python scripts/aider_fix_loop.py --test-cmd "pytest tests/ -q"
  python scripts/aider_fix_loop.py --test-cmd "ruff check ." --max-retries 5
  python scripts/aider_fix_loop.py --model openai/gemini/gemini-2.0-flash-exp:free
        """,
    )
    parser.add_argument(
        "--test-cmd",
        default=DEFAULT_TEST_CMD,
        help=f"Test command to run (default: {DEFAULT_TEST_CMD!r})",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"Max retry cycles (default: {DEFAULT_MAX_RETRIES})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_AIDER_MODEL,
        help=f"Aider model string (default: {DEFAULT_AIDER_MODEL!r})",
    )

    args = parser.parse_args()

    result = run_fix_loop(
        test_cmd=args.test_cmd,
        max_retries=args.max_retries,
        initial_model=args.model,
    )

    print(f"\n{'='*60}")
    if result.success:
        print(f"✅ SUCCESS — {result.attempts} attempt(s), {result.elapsed_sec:.1f}s")
        print(f"   Final model: {result.final_model}")
        sys.exit(0)
    else:
        print(f"❌ FAILED — {result.attempts} attempt(s), {result.elapsed_sec:.1f}s")
        print(f"   Final model: {result.final_model}")
        print(f"   Error: {result.error_msg[:300]}")
        sys.exit(1)


if __name__ == "__main__":
    main()