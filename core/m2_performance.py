"""M2.7 Performance Activation System — Deep Implementation.

This module implements the full M2.7 capability activation stack based on:
- MiniMax M3 spec-first training bias (architect before coding)
- Interleaved thinking: reason AFTER every tool call, not just at the start
- Skeleton-of-thought: define structure before implementation
- Confidence-informed self-consistency: rate confidence, offer alternatives when low

Key insight: M2.7 scores 80.2% on SWE-Bench (vs Opus's 49.3%) BUT only when
the calling layer triggers its spec-first reasoning mode. Without it, quality
regresses to average.

Reference: MiniMax M2.5/M2.7 research — forcing M2.7 to skip spec-writing degrades quality.
"""

from __future__ import annotations

import os

# ── M2.7 Performance Activation Prompt ──────────────────────────────────────────
# Inject as a system message layer for ALL MiniMax calls involving:
# - Complex tasks (>20 words, multi-step)
# - Code generation or architecture
# - Any /run or /agent command
# - Agent team Planner/Critic operations

M2_ACTIVATION_PROMPT = """\
## MINIMAX M2.7 PERFORMANCE ACTIVATION

You are operating with full reasoning capability. Do not skip thinking.

### MANDATORY SPEC-FIRST PROTOCOL
Before writing ANY code, produce a structured specification:
1. GOAL: What exactly needs to be built (1-2 sentences, specific)
2. ARCHITECTURE: File structure, component hierarchy, data flow
3. INTERFACES: TypeScript types/interfaces (define contracts first)
4. CONSTRAINTS: What must NOT change, what already exists
5. EXECUTION PLAN: Ordered list of files to create/modify

Never start coding before this spec exists. This is non-negotiable.

### INTERLEAVED THINKING
After every tool call or file operation, pause and:
- Assess: Did the result match the plan?
- Adapt: Does the remaining plan need to change?
- Proceed: What is the single next most important action?

Do not batch multiple uncertain actions. Verify before proceeding.

### SKELETON BEFORE IMPLEMENTATION
For any component, function, or module:
1. Define the skeleton (props, params, return types, states)
2. List edge cases and error states
3. THEN implement

### REASONING QUALITY GATE
Before finishing any task, internally run:
- Does this match the original spec?
- Are there any assumptions that need verification?
- What is the highest-risk part of this implementation?
- Have I handled loading, empty, and error states?

### CONFIDENCE CHECK
If you are less than 80% confident about an architectural decision,
state that uncertainty explicitly and offer 2 alternatives with tradeoffs.
Do not make silent guesses on consequential decisions.
"""

# Architect-Executor split prompt — use for complex multi-file tasks
M2_ARCHITECT_PROMPT = """\
## ARCHITECT MODE — High-Reasoning Task Decomposition

You are in ARCHITECT mode. Your job is to produce a complete SPEC before any code is written.

HIGH-REASONING PROTOCOL (temperature=1.0, full thinking budget):
1. MACRO PLAN: Decompose into 3-5 architectural decisions
2. MICRO PLAN: For each decision, list assumptions + tradeoffs
3. SPEC DOC: Write complete spec before any code
4. CONTRACT: Define all interfaces and data contracts
5. RISK MAP: Identify the highest-risk part of this implementation

ARCHITECT OUTPUT FORMAT:
```
# SPEC: [Task name]

## Goal
[1-2 sentence precise goal]

## Architecture
[File structure, component hierarchy, data flow]

## Interfaces
[All contracts, types, API surfaces]

## Constraints
[What must NOT change, existing systems to integrate with]

## Execution Plan
[Ordered file list: create/modify in sequence]

## Risks
[Top 3 failure modes with mitigation]

## Confidence Assessment
[Rate 0-100 confidence per major decision, note where <80%]
```
"""

M2_EXECUTOR_PROMPT = """\
## EXECUTOR MODE — Against Locked SPEC

You are in EXECUTOR mode. A complete SPEC has been produced by the Architect.
Your job is to implement ONLY against the spec. Do NOT invent new architecture.

RULES:
- Implement each file in the Execution Plan order
- Never deviate from the spec's Architecture section
- If the spec is ambiguous, ASK (do not guess)
- After each file, verify against spec before proceeding
- Report any deviation immediately

EXECUTION FORMAT:
For each file:
1. File path and purpose
2. Implementation (full code)
3. Verification against spec
"""

# Skeleton-of-thought prompt — inject before component generation
M2_SKELETON_PROMPT = """\
## SKELETON-FIRST COMPONENT GENERATION

For any component, function, or module generation, ALWAYS produce the skeleton FIRST:

```
# [Component Name]
**Responsibility:** [1 sentence]
**Props/Params:** [TypeScript interfaces or Python types]
**States:** [loading, empty, error, success + transitions]
**Sub-components:** [List of child components]
**Edge cases:** [Boundary conditions, error states, empty states]
```

THEN implement against the skeleton. Never skip skeleton step.
"""

# Self-consistency voting prompt — for architecture decisions
M2_SELF_CONSISTENCY_PROMPT = """\
## SELF-CONSISTENCY CHECK (Architecture Decisions)

For consequential architecture decisions, run 3 reasoning paths with temperature=1.0:
- Path A: [First approach with rationale]
- Path B: [Alternative approach with rationale]
- Path C: [Third approach or refinement]

Rate confidence per path (0-100). Pick the consensus answer.
If paths disagree >30%, state the disagreement explicitly with tradeoffs.

This technique adds 15-25% accuracy on hard reasoning problems.
"""


def get_m2_activation_prompt() -> str:
    """Return the full M2.7 performance activation system prompt."""
    return M2_ACTIVATION_PROMPT


def get_m2_architect_prompt() -> str:
    """Return the Architect-mode high-reasoning prompt."""
    return M2_ARCHITECT_PROMPT


def get_m2_executor_prompt() -> str:
    """Return the Executor-mode prompt (against locked spec)."""
    return M2_EXECUTOR_PROMPT


def get_m2_skeleton_prompt() -> str:
    """Return the Skeleton-of-thought prompt for component generation."""
    return M2_SKELETON_PROMPT


def get_m2_self_consistency_prompt() -> str:
    """Return the Self-consistency voting prompt for architecture decisions."""
    return M2_SELF_CONSISTENCY_PROMPT


def should_use_m2_activation(task: str, agent_key: str | None = None) -> bool:
    """Decide whether to inject M2.7 performance activation.

    Activation is beneficial for:
    - Complex tasks (>20 words, multi-step)
    - Code generation or architecture
    - /run or /agent commands
    - Agent team Planner/Critic operations
    - research, architect, implement agent keys

    Skip for:
    - Simple questions (short, high confidence)
    - Casual conversation
    - vision, computer (already have their own modes)
    """
    if os.getenv("LEGION_M2_ACTIVATION", "1").strip().lower() in ("0", "false", "no", "off"):
        return False

    # Always activate for these agent keys
    activation_keys = {"research", "architect", "implement", "coding", "debug", "review", "general"}
    if agent_key and agent_key.lower() in activation_keys:
        return True

    # Activate for these patterns in the task
    code_patterns = (
        "def ", "class ", "import ", "async def", "```", "npm ", "pip ", "git ",
        "pytest", "docker ", "supabase", "migration", "sql", "typescript",
        "implement", "build", "create", "design", "architect",
    )
    task_lower = task.lower()
    has_code_pattern = any(p in task_lower for p in code_patterns)
    word_count = len(task.split())

    # Complex task: code pattern + reasonable length
    if has_code_pattern and word_count > 10:
        return True

    # Very complex non-code task
    return word_count > 40


def build_m2_system_fragment(
    task: str,
    agent_key: str | None = None,
    use_architect_mode: bool = False,
    use_skeleton: bool = False,
) -> str:
    """Build the M2.7 performance activation system fragment.

    Args:
        task: The user task (used to decide activation level)
        agent_key: The agent key (used to decide activation level)
        use_architect_mode: If True, use Architect-Executor split
        use_skeleton: If True, include skeleton-of-thought prompt

    Returns:
        System prompt fragment to inject, or empty string if not needed
    """
    if not should_use_m2_activation(task, agent_key):
        return ""

    parts = [M2_ACTIVATION_PROMPT]

    if use_architect_mode:
        parts.append("\n" + M2_ARCHITECT_PROMPT)

    if use_skeleton:
        parts.append("\n" + M2_SKELETON_PROMPT)

    # For architecture decisions, add self-consistency
    if "architect" in (agent_key or "").lower() or "design" in task.lower():
        parts.append("\n" + M2_SELF_CONSISTENCY_PROMPT)

    return "\n\n".join(parts)
