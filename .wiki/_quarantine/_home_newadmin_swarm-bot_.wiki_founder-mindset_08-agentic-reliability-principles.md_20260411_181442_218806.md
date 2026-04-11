---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/founder-mindset/08-agentic-reliability-principles.md",
  "reason": "daily_fast_scan: score=0.150 < 0.3",
  "score": 0.15000000000000002,
  "quarantined_at": "2026-04-11T18:14:42.218874"
}
---

# Agentic Reliability Principles

Source: Glean + Anthropic Project VEND + Klover AGD

## The Gap
"The gap between 'can do' and 'reliably does in production' is enormous."
— Anthropic Project VEND learnings

## 7 Reliability Principles

### 1. Permission-aware
Agent must know what data it can and cannot access.
Violating this once destroys enterprise trust permanently.

### 2. Citation-backed
Every factual claim must have a source.
"I retrieved this from wiki/salary-law.md" > "I know that..."

### 3. Graceful degradation
When unsure → say "I don't know" → escalate to human.
Confident wrong answer is worse than honest uncertainty.

### 4. Idempotent actions
Running the same task twice should produce the same result.
Especially critical for file writes, API calls, database updates.

### 5. Cost-bounded
Every agent has a token budget. Exceeding it = task failure, not runaway spend.

### 6. Observable
Every agent action is logged with: what, why, how much it cost, outcome.

### 7. Recoverable
Every failure has a recovery path. No silent failures.
Dead letter queue > /dev/null.

## Applied to Legion
Audit checklist before calling any agent "production-ready":
- Permission check implemented?
- Citations in output?
- "I don't know" path exists?
- Action is idempotent?
- Token budget set?
- Action logged?
- Failure recovery defined?
