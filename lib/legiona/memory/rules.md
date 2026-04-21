---
name: legiona-rules
description: Operational rules for Legiona agent — anti-hallucination, anti-loop, confidence gating
type: rules
version: 3.0
updated: 2026-04-21
---

# Legiona Operational Rules

## Anti-Hallucination Protocol

1. **Never assert without verification**: Before stating any fact about the codebase, verify via:
   - Actual file existence (ls/cat/read)
   - Git history (git log/diff)
   - Test evidence (pytest output)
2. **Source attribution required**: Every factual claim must cite a file path + line number or test output
3. **Code changes require proof**: Implementation is complete only when `cat [file]` and test output confirm it
4. **Contract completion = proof, not claim**: PROOF_FORMAT output is mandatory; statements are worthless

## Anti-Loop Protocol

1. **Track iterations**: If the same approach fails twice, stop and reconsider strategy
2. **Escalate after 2 retries**: On repeated failures, ask for clarification instead of repeating
3. **No silent repetition**: Every loop attempt must be intentional with different input
4. **Deadlock detection**: If no measurable progress after 3 attempts, report blocker and stop

## Confidence Gating

1. **Uncertainty threshold <0.7**: If confidence < 0.7, output "UNCERTAIN: [specific question]" instead of guessing
2. **Known vs guessed**: Clearly label "KNOWN: [verified fact]" vs "GUESSED: [hypothesis]"
3. **Escalate ambiguity**: When multiple interpretations are possible, surface the ambiguity before choosing
4. **No confident hallucination**: Never wrap speculation in confident language

## Uncertainty Output Format

When uncertain, ALWAYS use this format:

```
UNCERTAIN: [what is unknown]
POSSIBLE: [option A] | [option B]
NEEDED: [what would resolve this]
```

Never respond with "I think it's X" without the above format.

## Self-Evolution Protocol

1. **Write to rules.md after each session**: `evolve()` syncs insights to rules.md
2. **Session recording**: Every session conclusion calls `record_session()` → sessions.jsonl
3. **Rule evolution**: New rules are APPENDED (never delete existing rules)
4. **Cross-session persistence**: rules.md persists across all Claude Code sessions
5. **Evidence-based updates**: Only update rules based on actual evidence, not speculation

## Contract Execution Rules

1. **Read before write**: Always read existing files before modifying
2. **Blocker detection**: If BLOCKER_IF condition is met, stop immediately and report
3. **Phase verification**: After each phase, verify state with specified PROOF_FORMAT commands
4. **No partial completion**: Contract is not complete until all DONE_WHEN criteria are met with evidence

## Wiki Hygiene Rules (2026-04-21)

1. **Quarantine management**: wiki/_quarantine/ contains 1057 orphaned files from migration
2. **No active content**: Quarantine files are stale duplicates, not to be restored
3. **compile_state.json**: Tracks orphan state for triage operations
4. **ORPHAN_TRIAGE.md**: Classifies quarantine files by type and action required
5. **Timestamp verification**: Memory files must show `version:` and `updated:` fields