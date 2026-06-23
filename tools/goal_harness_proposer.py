"""
tools/goal_harness_proposer.py
Meta-Harness proposer -- evolves the harness after each /goal run.

From the Meta-Harness paper (arXiv:2603.28052):
"The proposer reads a median of 82 files per iteration, referencing
 over 20 prior candidates per step."
"Access to raw execution traces is the key ingredient for enabling harness search."
"Scores Only = 34.6 median. Full traces = 50.0 median."

This file implements the outer optimization loop.
Run after each /goal completion:
  python tools/goal_harness_proposer.py
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import anthropic

GOAL_DIR = Path(".goal")
TRACES_DIR = GOAL_DIR / "traces"
HARNESSES_DIR = GOAL_DIR / "harnesses"
CANDIDATES_DIR = HARNESSES_DIR / "candidates"
CURRENT_HARNESS = HARNESSES_DIR / "current" / "harness.py"
PARETO_DIR = HARNESSES_DIR / "pareto_frontier"


PROPOSER_SYSTEM = """You are an expert AI systems engineer specializing in
harness optimization for autonomous coding agents. Your job is to analyze
execution traces from prior agent runs and propose an improved harness.

A "harness" is the Python code that wraps an AI agent and determines:
- What context the agent sees in each task prompt (build_context_block)
- How task prompts are structured (build_task_prompt)
- What latent state passes between tasks (extract_task_summary)
- How execution traces are logged (log_trace)

Your goal: propose H_{n+1}, an improved harness that will perform better
than the current harness based on evidence from execution traces.

CRITICAL RULES:
1. Read the FULL traces -- not just scores. The failure mode is in the trace.
2. Look for: tasks where the agent got confused, missing context, wrong file
   paths, acceptance criteria not checked, loops without progress.
3. Small targeted changes beat large rewrites. Identify ONE failure mode
   and fix it precisely.
4. Output ONLY valid Python code for the new harness.py -- nothing else.
5. Increment HARNESS_VERSION by 1 in the code.
6. Keep the same function signatures -- goal_runner.py imports them.
"""


def collect_trace_evidence(max_traces: int = 20) -> str:
    """
    Collect raw execution traces for the proposer.
    Meta-Harness insight: give FULL traces, not summaries.
    Proposer reads a median of 82 files per iteration.
    """
    evidence_parts = []

    # Collect all score records sorted by score
    score_files = sorted(CANDIDATES_DIR.glob("*_score.json"))
    scores_summary = []
    for sf in score_files[-10:]:
        try:
            data = json.loads(sf.read_text())
            scores_summary.append(
                f"  goal_id={data.get('goal_id')} score={data.get('score')} grade={data.get('grade')} goal={data.get('goal','?')[:50]}"
            )
        except Exception:
            pass

    evidence_parts.append(
        "=== HARNESS SCORE HISTORY (newest last) ===\n" +
        ("\n".join(scores_summary) if scores_summary else "  (no scores yet)")
    )

    # Read current harness
    if CURRENT_HARNESS.exists():
        evidence_parts.append(
            f"=== CURRENT HARNESS (harness.py) ===\n{CURRENT_HARNESS.read_text()}"
        )

    # Read raw execution traces (the key insight from Meta-Harness)
    trace_dirs = sorted(TRACES_DIR.iterdir()) if TRACES_DIR.exists() else []
    recent_trace_dirs = trace_dirs[-5:]  # Last 5 goal runs

    for trace_dir in recent_trace_dirs:
        if not trace_dir.is_dir():
            continue
        trace_files = sorted(trace_dir.glob("*.trace"))
        for tf in trace_files[:max_traces]:
            content = tf.read_text()
            evidence_parts.append(
                f"=== TRACE: {trace_dir.name}/{tf.name} ===\n{content}"
            )

        # Include audit reports for this run
        goal_id = trace_dir.name
        report_files = list((GOAL_DIR / "reports").glob(f"{goal_id}_*.json"))
        for rf in report_files:
            try:
                data = json.loads(rf.read_text())
                evidence_parts.append(
                    f"=== AUDIT: {rf.name} ===\nscore={data.get('score')} grade={data.get('grade')}\n"
                    f"git_changed: {data.get('git',{}).get('changed_files',{}).get('stdout','?')[:200]}"
                )
            except Exception:
                pass

    return "\n\n".join(evidence_parts)


def get_harness_version() -> int:
    """Get current harness version number."""
    if CURRENT_HARNESS.exists():
        content = CURRENT_HARNESS.read_text()
        for line in content.split('\n'):
            if 'HARNESS_VERSION = "H_' in line:
                try:
                    return int(line.split('H_')[1].split('"')[0])
                except Exception:
                    pass
    return 0


def propose_next_harness(evidence: str, current_version: int) -> str:
    """Call Claude to propose H_{n+1} based on execution trace evidence."""
    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL") or None
    )

    user_msg = f"""Current harness version: H_{current_version}
Propose H_{current_version + 1} based on the following execution trace evidence.

{evidence}

Analyze the traces for failure modes. Propose ONE targeted improvement.
Output ONLY the complete improved harness.py Python code.
The code must be valid Python that I can save directly as harness.py."""

    message = client.messages.create(
        model="claude-opus-4-6-20251101",
        max_tokens=8192,
        system=PROPOSER_SYSTEM,
        messages=[{"role": "user", "content": user_msg}]
    )

    content = message.content[0].text

    # Extract Python code block if wrapped in markdown
    if "```python" in content:
        code = content.split("```python")[1].split("```")[0].strip()
    elif "```" in content:
        code = content.split("```")[1].split("```")[0].strip()
    else:
        code = content.strip()

    return code


def validate_harness(code: str) -> tuple[bool, str]:
    """Validate proposed harness has required functions."""
    required = [
        "def build_context_block",
        "def build_task_prompt",
        "def extract_task_summary",
        "def log_trace",
        "HARNESS_VERSION"
    ]
    missing = [r for r in required if r not in code]
    if missing:
        return False, f"Missing required: {missing}"

    try:
        compile(code, "<harness>", "exec")
        return True, "OK"
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"


def run_proposer(dry_run: bool = False) -> Optional[Path]:
    """
    Main entry point for Meta-Harness proposer.
    Reads traces, proposes next harness, validates, saves.
    """
    current_version = get_harness_version()
    next_version = current_version + 1

    print("Meta-Harness Proposer")
    print(f"Current harness: H_{current_version}")
    print(f"Proposing: H_{next_version}")
    print("Collecting traces...")

    evidence = collect_trace_evidence()
    evidence_tokens_est = len(evidence) // 4
    print(f"Evidence collected: ~{evidence_tokens_est:,} tokens")

    print("Calling proposer (Claude Opus)...")
    new_harness_code = propose_next_harness(evidence, current_version)

    valid, msg = validate_harness(new_harness_code)
    if not valid:
        print(f"Proposed harness invalid: {msg}")
        rejected_path = CANDIDATES_DIR / f"H_{next_version}_REJECTED.py"
        rejected_path.write_text(new_harness_code)
        print(f"Saved as rejected candidate: {rejected_path}")
        return None

    print(f"Harness H_{next_version} valid: {msg}")

    if dry_run:
        print("DRY RUN -- not saving. Preview:")
        print(new_harness_code[:500])
        return None

    # Save as candidate
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    candidate_path = CANDIDATES_DIR / f"H_{next_version}_candidate.py"
    candidate_path.write_text(new_harness_code)

    # Write metadata
    metadata = {
        "id": f"H_{next_version}",
        "created": datetime.now().isoformat(),
        "score": None,
        "evaluated": False,
        "pareto_frontier": False,
        "previous_version": f"H_{current_version}",
        "evidence_tokens": evidence_tokens_est
    }
    (CANDIDATES_DIR / f"H_{next_version}_metadata.json").write_text(
        json.dumps(metadata, indent=2)
    )

    # Promote to current
    CURRENT_HARNESS.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_HARNESS.write_text(new_harness_code)
    print(f"H_{next_version} promoted to current harness")
    print(f"Next /goal run will use H_{next_version}")

    return candidate_path


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    result = run_proposer(dry_run=dry_run)
    if result:
        print(f"New harness saved: {result}")
    else:
        print("No new harness produced.")
