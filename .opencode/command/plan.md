---
description: >-
  Enter plan mode to thoroughly explore the codebase before implementing.
  Uses the Explorer agent to investigate architecture, then creates an
  implementation plan for user approval before spawning workers.
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---
# /plan — Enter Plan Mode

## WHEN TO USE

Use `/plan` when:
- Task is complex and requires architectural decisions
- Multiple valid implementation approaches exist
- Task touches unknown code
- Task spans multiple modules or systems
- You need user approval before proceeding

## HOW IT WORKS

The /plan command:
1. Uses @explorer to deeply investigate the relevant codebase
2. Uses @memory to check if similar tasks were done before
3. Writes architecture blueprint with implementation options
4. Presents plan to user for approval
5. Only spawns workers after user approves

## USAGE

```
/plan [task description]

Examples:
/plan add a memory consolidation background task
/plan implement the LSP reader agent
/plan refactor the intent router to use 18 intents
/plan create a GitHub PR workflow for reviews
```

## WHAT YOU GET

After running /plan, you will receive:
- **Structural findings** — directory structure, key files, dependencies
- **Architecture options** — 2-3 approaches with trade-offs
- **Risk assessment** — what could go wrong, likelihood, impact
- **Implementation plan** — numbered steps with contract format
- **Approval request** — "Approve plan to proceed?" [yes/start-over/cancel]

## APPROVAL OPTIONS

| Option | Meaning |
|--------|---------|
| yes | Proceed with plan as-is |
| start-over | Cancel and restart with different approach |
| cancel | Abandon the task |

## AFTER APPROVAL

Once you approve:
- @planner creates detailed CONTRACTS
- @worker executes contracts
- @Diff-Analyzer verifies
- @reviewer approves
- You get completion report

## EXAMPLE

```
/plan add a Pinecone vector search integration
```

Response:
```
## Plan: Add Pinecone Vector Search

### Context
Current: Legion uses mem0ai for vector storage
Proposed: Add Pinecone as alternative vector DB

### Options

**Option A: Add as Primary**
- Pros: Managed, scalable, production-ready
- Cons: External dependency, cost

**Option B: Add as Fallback**
- Pros: No change to current flow
- Cons: Complexity in routing

**Option C: Compare Both**
- Pros: Data-driven choice
- Cons: More work upfront

### Recommended: Option B
Simple fallback integration without disrupting current mem0 setup.

### Implementation
Contracts: 3
Risk: LOW — read-only until explicitly enabled

### Approval
Approve? [yes/Option A/Option C/cancel]
```

## ANTI-HALLUCINATION RULES

1. **Explore before planning** — never skip Explorer phase
2. **Check memory** — see if similar task exists
3. **Present options** — never assume single approach
4. **Cite trade-offs** — explain pros/cons of each approach
5. **Get explicit approval** — don't proceed without yes

## STATUS
```
PLAN MODE: ⏸️ ENTERED | ✅ APPROVED | ❌ CANCELLED
Task: [what you asked for]
Options presented: [N]
```
