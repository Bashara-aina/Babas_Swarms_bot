---
description: >-
  Root cause analysis for bugs, errors, and unexpected behavior. Use when:
  "why is this broken", "debug this", "500 error", "it's not working", "find the bug",
  or when something that worked before suddenly stopped. Investigates until you
  find the root cause, not just the symptom.
allowed-tools: Bash, Read, Grep, Glob, Write, Edit, WebSearch
argument-hint: [error message or unexpected behavior]
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---

# /investigate — Root Cause Analysis

## VOICE

Be concrete. Name the file, the function, the line number. Show the exact command to run. When something is broken, point at the exact line. "auth.ts:47, the token check returns undefined when the session expires."

No em dashes. Short paragraphs. End with the action.

## STEP 1 — Gather Evidence

Run these commands in parallel and paste all outputs:

```bash
# What changed recently?
git log --oneline -10

# What's the current error?
echo "ERROR: paste your error message here"

# What's the unexpected behavior?
echo "BEHAVIOR: paste what you expected vs what happened"
```

## STEP 2 — Reproduce the Issue

If there's an error:
```bash
python -m py_compile [suspect_file.py]
python -c "from [module] import [thing]"  # test import
```

If there's a runtime error, reproduce it with a minimal case.

## STEP 3 — Hypothesis Formation

Based on evidence, form 2-3 hypotheses about what caused this.

Example:
- Hypothesis A: The token expiry check is comparing strings to ints
- Hypothesis B: The session store is returning None for expired sessions
- Hypothesis C: The middleware is not running for this route

## STEP 4 — Test Each Hypothesis

For each hypothesis, design a test that would prove or disprove it:

```bash
# Test hypothesis A
grep -n "==" [file.py] | head -20

# Test hypothesis B
python -c "print(type(expiry_value), repr(expiry_value))"
```

## STEP 5 — Find the Root Cause

When evidence points to the root cause, name it explicitly:

"ROOT CAUSE: auth.ts:47 — the `==` comparison between string token and int expiry time always returns False."

## STEP 6 — Verify and Fix

Verify the fix:
```bash
# Apply fix
[your fix here]

# Verify
python -m py_compile [fixed_file.py]
python -c "from [module] import [thing]; print('ok')"
```

## OUTPUT FORMAT

```
INVESTIGATION REPORT
═════════════════════

PROBLEM: [1-line description]

EVIDENCE:
[paste actual command outputs]

HYPOTHESES TESTED:
1. [A] — [PROVEN / DISPROVEN]
2. [B] — [PROVEN / DISPROVEN]
3. [C] — [PROVEN / DISPROVEN]

ROOT CAUSE: [file:line] — [exact description]

FIX APPLIED:
[exact fix]

VERIFICATION:
[paste verification output]

STATUS: ✅ RESOLVED | 🔴 UNRESOLVED
```

## ANTI-HALLUCINATION RULES

1. Paste actual command outputs — never summarize
2. If you can't reproduce it, say "cannot reproduce — need more information"
3. Root cause must cite exact file and line number
4. Fix must be verified with actual command output
