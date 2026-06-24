# Fable 5 -- Workflow Engine

On-demand reference. Load when dispatching multi-agent work, designing verification strategies, or running audit/review tasks.

---

## 1. Core Dispatch Patterns

### `agent(prompt, opts)` -- spawn a subagent

The primitive. Every composite pattern below is built on this. Returns a string, or validated object when `schema` is provided.

```javascript
// Free-form
const summary = await agent("Summarize these PR changes.")

// Structured with schema validation
const plan = await agent("Plan the refactor steps.", {
  schema: { type: "object", properties: {
    steps: { type: "array", items: { type: "string" } },
    risk: { type: "string" }
  }, required: ["steps", "risk"] }
})
```

### `pipeline(items, ...stages)` -- default dispatch, no barrier

Items flow through each stage independently. Stage 2 for item A begins the moment stage 1 for item A completes, regardless of where item B is. Wall-clock time = slowest single-item chain. This is the default -- use it unless you need a barrier.

```javascript
const results = await pipeline(files,
  async (f) => agent(`Lint and fix ${f}`),
  async (f) => agent(`Type-check ${f}`)
)
```

### `parallel(thunks)` -- concurrent with barrier

Every thunk runs concurrently. The barrier waits for ALL before returning. Wall-clock time = slowest thunk, but nothing after the barrier starts until everything before it is done.

```javascript
const [graph, index] = await parallel([
  () => agent("Rebuild the dependency graph."),
  () => agent("Rebuild the search index.")
])
// Both must finish before anything past this point
```

**Default: pipeline. Only use parallel when a barrier is genuinely required.**

| Use case | Barrier valid? |
|---|---|
| Stage N needs ALL of stage N-1's output (dedup, comparison, cross-referencing) | Yes |
| "I need to flatten first" | No -- do it in a pipeline stage |
| "Stages are conceptually separate" | No -- that is pipeline's job |
| "Cleaner code" | No -- barrier latency is real |

---

## 2. Adversarial Verification

Spawn N independent skeptics per finding. Each is prompted to REFUTE. If the majority refute, the finding dies. This is the single most important pattern for preventing plausible-but-wrong claims.

```javascript
const VERIFY_SCHEMA = {
  type: "object", properties: {
    refuted: { type: "boolean" },
    reason: { type: "string" }
  }, required: ["refuted", "reason"]
}

const votes = await parallel(
  Array.from({ length: 3 }, () => () =>
    agent(`REFUTE this claim if possible: "${claim}". Default to refuted=true when uncertain.`, { schema: VERIFY_SCHEMA })
  )
)

const refutedCount = votes.filter(v => v && v.refuted).length
const survives = refutedCount < 2  // majority must refute to kill
```

Default: 3 skeptics, simple majority. Scale to 5+ for high-stakes findings (security, correctness, production).

---

## 3. Perspective-Diverse Verify

When a finding can fail in multiple dimensions, give each verifier a distinct lens. Redundancy catches random misses; diversity catches systematic blind spots.

```javascript
const lenses = [
  () => agent(`REFUTE on correctness grounds: ${claim}`, { schema: VERIFY_SCHEMA }),
  () => agent(`REFUTE on security grounds: ${claim}`, { schema: VERIFY_SCHEMA }),
  () => agent(`REFUTE on performance grounds: ${claim}`, { schema: VERIFY_SCHEMA }),
  () => agent(`REFUTE on reproducibility grounds: ${claim}`, { schema: VERIFY_SCHEMA })
]
const verdicts = await parallel(lenses)
```

Use when the finding touches multiple concerns -- never when a single lens suffices.

---

## 4. Judge Panel

Generate N independent attempts from different angles, score them, then synthesize the winner while grafting the best ideas from runners-up.

```javascript
const attempts = await parallel([
  () => agent("Solve, prioritizing correctness."),
  () => agent("Solve, prioritizing simplicity."),
  () => agent("Solve, prioritizing performance.")
])

const scores = await parallel(attempts.map(a => () =>
  agent(`Score this solution 0-10: "${a}". Return numeric score only.`, {
    schema: { type: "object", properties: { score: { type: "number" } }, required: ["score"] }
  })
))

const best = scores.indexOf(Math.max(...scores))
const final = await agent(
  `Take solution #${best} as the base. Graft improvements from the other solutions where they outperform the base. Return the synthesized result.`
)
```

---

## 5. Loop-Until-Dry

For unknown-size discovery (bugs, edge cases, entities), keep spawning finders until K consecutive rounds return nothing new. K is the dryness threshold.

```javascript
const seen = new Set()
const findings = []
let dryRounds = 0
const DRY_LIMIT = 2  // safe default; tune per domain

while (dryRounds < DRY_LIMIT) {
  const batch = (await parallel(FINDERS.map(f => () =>
    agent(f.prompt, { schema: FINDING_SCHEMA })
  ))).flatMap(r => r.findings || [])

  const fresh = batch.filter(f => !seen.has(f.id))
  if (fresh.length === 0) { dryRounds++; continue }

  dryRounds = 0
  fresh.forEach(f => seen.add(f.id))
  findings.push(...fresh)
}
```

High DRY_LIMIT (5) for deep exhaustive searches. Low DRY_LIMIT (1-2) for broad surveys where diminishing returns hit fast.

---

## 6. Multi-Modal Sweep

Parallel agents each searching a different dimension. Each is blind to the others' output. Add a mode for every dimension the problem has.

```javascript
const sweeps = await parallel([
  () => agent("Find issues by analyzing module boundaries."),       // by-container
  () => agent("Find issues by tracing data flow through functions."), // by-content
  () => agent("Find issues by checking entity lifecycle and state."), // by-entity
  () => agent("Find issues by examining timing and ordering."),       // by-time
  () => agent("Find issues by auditing access control paths."),       // by-auth
  () => agent("Find issues by inspecting retained state.")            // by-memory
])
```

Modes: by-container, by-content, by-entity, by-time, by-auth, by-memory. Never run fewer modes than the problem has dimensions.

---

## 7. Completeness Critic

A dedicated pass asking only: "What is missing?" Run this after main work but before declaring done. Never let silence truncation look like coverage.

```javascript
const gap = await agent(`What is missing from this analysis?
- Which modality was not run?
- Which claim went unverified?
- Which source was not read?
Return specific, actionable gaps.`, {
  schema: { type: "object", properties: {
    gaps: { type: "array", items: { type: "string" } }
  }, required: ["gaps"] }
})

if (gap.gaps.length > 0) {
  // Do not declare done -- spawn new work from each gap
  await parallel(gap.gaps.map(g => () => agent(`Address: ${g}`)))
}
```

---

## 8. Budget-Aware Execution

When calling an external API with finite budget, check remaining budget inside every loop. Stop when dry.

```javascript
let budget = 500_000  // tokens or cost units
const STEP_COST = 50_000

while (budget >= STEP_COST) {
  const result = await agent("Continue finding issues.", { schema: ISSUES })
  budget -= STEP_COST
  if (!result.issues.length) break
}

console.warn(`Budget exhausted: ${budget} remaining`)
```

---

## 9. No Silent Caps

When a workflow bounds coverage (top-N, no retry, sampling, max depth), log what was dropped. Silent truncation reads as "covered everything."

```javascript
const dropped = []
// When hitting a bound:
dropped.push({ item, reason: "exceeded max-depth 3" })
// When skipping:
dropped.push({ item, reason: "budget floor reached" })

if (dropped.length) {
  console.warn(`Coverage capped: ${dropped.length} items not processed`)
  // Log details so the caller sees the gap
}
```

---

## 10. Quality Heuristics

| Task | Finder pool | Verify pass | Post-processing |
|---|---|---|---|
| Bug hunt | 1-2 finders | Single vote | None |
| Thorough audit | 3-5 finders | 3-5 adversarial | Synthesis + completeness critic |
| Security review | 3+ finders (diverse lenses) | 5 adversarial + perspective-diverse | Synthesis + gap analysis |
| Deep discovery | Loop-until-dry (K=5) | Adversarial per round | Dedup + completeness critic |
| Design decisions | Judge panel (3-5 angles) | Score + graft | Completeness critic |
