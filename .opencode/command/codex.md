---
description: >-
  Multi-model second opinion using OpenAI Codex CLI. Provides independent
  adversarial review from a different AI model. Three modes: Review (diff review
  with pass/fail gate), Challenge (adversarial mode to break your code),
  Consult (ask anything with session continuity). Use when: "second opinion",
  "codex review", "ask codex", "consult codex", "cross-model review".
  Requires: OpenAI Codex CLI installed (npm install -g @openai/codex).
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
argument-hint: [mode] [question or "review" for diff review]
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---

# /codex — Multi-Model Second Opinion

## VOICE

Be the 200 IQ second opinion. Thorough, adversarial, won't accept the first answer. Don't agree to agree. Challenge the assumption. Find what the first model missed.

## MODES

### Mode 1: Review (default)
```
/codex review
```
Independent diff review against the base branch. Pass/fail gate with P1/P2/P3 findings.

### Mode 2: Challenge
```
/codex challenge [your code or approach]
```
Adversarial mode — tries to break your code. "What's the edge case that kills this?"

### Mode 3: Consult
```
/codex consult [your question]
```
Ask codex anything. Session continuity for follow-ups.

## STEP 1 — Detect Mode

Parse the argument:
- "review" or no argument → Mode 1 (Review)
- "challenge" → Mode 2 (Challenge)
- "consult" or any other → Mode 3 (Consult)

## STEP 2 — Check Codex Availability

```bash
which codex 2>/dev/null && echo "CODEX_AVAILABLE" || echo "CODEX_NOT_INSTALLED"
```

If NOT_INSTALLED:
```
Codex CLI not installed. Install with:
npm install -g @openai/codex

Then authenticate:
codex auth

Once installed, run your command again.
```

## STEP 3 — Run Appropriate Mode

### Mode 1: Review

```bash
cd $(git rev-parse --show-toplevel)
REPO_ROOT=$(pwd)
BASE_BRANCH=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null || echo "main")

codex review --base $BASE_BRANCH -c 'model_reasoning_effort="high"' 2>&1
```

**Gate logic:** If output contains `[P1]` markers → GATE: FAIL → AskUserQuestion:
```
Codex found P1 issues.

A) Investigate and fix now (recommended)
B) Continue anyway
```

### Mode 2: Challenge

```bash
cd $(git rev-parse --show-toplevel)
REPO_ROOT=$(pwd)

codex exec "Think like an attacker and a chaos engineer. What would break this code? Find edge cases, race conditions, security holes. Be adversarial." -C "$REPO_ROOT" -s read-only 2>&1
```

### Mode 3: Consult

```bash
cd $(git rev-parse --show-toplevel)
REPO_ROOT=$(pwd)

# Escape quotes in question
QUESTION="[user's question]"
codex exec "$QUESTION" -C "$REPO_ROOT" -s read-only 2>&1
```

## STEP 4 — Synthesize

Present Codex findings alongside the original analysis:

```
CODEX SAYS:
═════════════════════════════════════════
[full codex output]

SYNTHESIS:
- Agrees with: [what both models agree on]
- Disagrees with: [where codex challenges the original]
- New finding: [what codex found that wasn't in original]
═════════════════════════════════════════
```

## ANTI-HALLUHALLUCINATION RULES

1. Present codex output verbatim — don't summarize
2. If codex times out (5 min limit), note: "Codex timed out after 5 minutes"
3. If codex auth fails, provide the auth instructions
4. Cross-model synthesis is informational — the user decides

## OUTPUT FORMAT

```
/codex [mode] — Multi-Model Second Opinion
═════════════════════════════════════════

MODE: [Review | Challenge | Consult]
CODEX: [AVAILABLE | NOT INSTALLED | ERROR]

[Full codex output or instructions]

SYNTHESIS:
[How this changes or confirms the original analysis]

STATUS: ✅ PASS | 🔴 FAIL | ℹ️ ADVISOR
```
