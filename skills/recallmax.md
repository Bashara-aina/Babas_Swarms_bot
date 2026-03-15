# RecallMax — Viking Memory Protocol (L0 / L1 / L2)

Use memory as a precision tool, not a dump. Prioritize relevance, recency, and correctness.

## 1) Tier model

### L0 — Identity / stable context
- What it stores: persistent profile-level context (owner identity, core environment, long-lived constraints).
- Load policy: always-on, lightweight.
- Update policy: rare, only when stable facts change.

### L1 — Session context
- What it stores: current session goals, recent decisions, active task state.
- Load policy: every request for that user/session.
- Update policy: each meaningful user-assistant turn.

### L2 — Deep history / semantic facts
- What it stores: important solved issues, architectural decisions, reusable research outcomes.
- Load policy: semantic retrieval based on current query.
- Update policy: only “worth-saving” interactions.

## 2) Retrieval protocol

1. Load L0 baseline context.
2. Load L1 session overview.
3. Retrieve top L2 matches by semantic similarity.
4. Keep only evidence that improves current answer quality.
5. If no relevant memory, answer normally without forcing memory mention.

## 3) Storage protocol

Store to memory only when one of these is true:
- user preference with future impact
- project-specific technical fact
- root-cause/fix pair that may recur
- explicit decision or policy set by user
- durable research finding with source

Do NOT store:
- temporary formatting requests
- low-signal small talk
- one-off trivial outputs
- unverified speculative claims

## 4) Worth-saving heuristics

Strong save signals:
- explicit "remember this"
- solved production bug with concrete fix
- URLs/references used repeatedly
- credentials/secret locations should NOT be stored in plain memory blocks

Weak/no-save signals:
- generic definitions
- repeated obvious commands
- noisy logs without diagnosis

## 5) Context injection format

When memory is relevant, inject compactly at prompt stage:

```
[MEMORY CONTEXT]
- Fact: ... (source=L1/L2)
- Decision: ... (date/session)
- Preference: ...
[END MEMORY CONTEXT]
```

Keep memory block concise; do not exceed context budget with stale history.

## 6) Staleness and confidence

- Mark stale/conflicting memory explicitly.
- If confidence is low, ask for confirmation rather than asserting.
- Prefer recent L1 signal over old L2 notes when conflict exists.

## 7) Compression policy

When history grows:
1. Preserve last 4–6 turns verbatim.
2. Summarize older turns by decisions/fixes/preferences only.
3. Drop chatter and duplicated artifacts.
4. Maintain causal chain (problem → action → result).

## 8) Privacy and safety

- Never store raw secrets/tokens/passwords.
- Avoid logging private message bodies in audit traces.
- If sensitive data appears, redact before persistence.

## 9) Operational behavior in this repo

- L1/L2 may fail-open to SQLite/TF-IDF fallback.
- Retrieval failure must not break user response path.
- Memory save should be non-blocking in hot chat path.

## 10) Quality bar

Good memory use means:
- fewer repeated clarification loops
- consistent continuity across restarts
- higher precision on recurring tasks
- no hallucinated “memory” claims

## 11) Conflict resolution policy

When two memories conflict:
1. Prefer most recent verified source.
2. Prefer user-explicit statements over inferred summaries.
3. If uncertainty remains, ask a confirmation question before proceeding.

## 12) Session handoff pattern

At key transitions (end of large task/session):
- persist a compact “state handoff” summary to L1
- include current status, pending items, blockers, and next action
- avoid storing raw verbose logs

## 13) Memory quality KPIs

Track these signals qualitatively:
- reduced repeated clarification on recurring tasks
- consistent references to prior decisions
- lower contradiction rate across sessions
- no sensitive data leakage in stored context

## 14) Failure-safe behavior

- If memory backend is unavailable, continue with local context gracefully.
- Do not claim memory retrieval happened when it did not.
- Keep user-visible output correct even with zero memory available.
