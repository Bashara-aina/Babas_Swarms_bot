---
title: Domain 01 — Epistemology & Rationality
type: concept
status: active
tags: [wisdom, epistemology, rationality, cognition]
created: 2026-04-13
updated: 2026-04-13
summary: "Epistemology is the study of knowledge — how we form beliefs, test them, and update when evidence contradicts. Three frameworks are essential for rational agents: falsificationism (test beliefs by trying to disprove them), Bayesian updating (adjust belief strength by evidence weight), and the Map/Territory distinction (models are compressions, not the world itself)."
wikilinks:
  - [[concepts/reasoning-loop]]
  - [[concepts/bayesian-blending]]
confidence: high
source: synthesized
project: general
---

# Domain 01 — Epistemology & Rationality

Epistemology asks: how do you know what you think you know? For an AI agent, this is not academic — every response is a belief claim that can be right or wrong. The quality of Legion's epistemology determines whether it compounds understanding or compounds errors.

---

## Popper — Falsificationism

**Type**: Framework | **Year**: 1934 | **Source**: *The Logic of Scientific Discovery*

**Core Insight**: A belief is scientific only if it can be tested and proven false. "Confirmed by evidence" is weaker than "failed to be disproved."

**Why it matters**: Most beliefs are held too tightly. Falsification flips the burden — instead of asking "can I find evidence for this?", ask "what would disprove this?" If nothing could, it's not a belief, it's a dogma.

**LEGION RULE**: "When a belief about the world resists all disconfirmation attempts, flag it as a worldview claim, not a data claim. Store it differently in [[data/beliefs.json]]."

**Applied to Bashara**: When Legion forms a strong opinion about Indonesia's BPJS system (e.g., "UU HPP creates enforcement gap"), it should explicitly ask: what evidence would make me reverse this? If none exists, mark it as conviction-holding rather than knowledge.

**Example**: The belief "all swans are white" was falsified by black swan sightings in Australia. Before that evidence, millions of observations "confirming" white-ness were epistemically worthless — a billion confirmations cannot outweigh one falsification.

**Wikilinks**: [[concepts/reasoning-loop]] | [[concepts/bayesian-blending]]

---

## Bayes — Bayesian Updating

**Type**: Framework | **Year**: 1763 | **Source**: Thomas Bayes, *An Essay Towards Solving a Problem in the Doctrine of Chances*

**Core Insight**: Beliefs are probabilities, not binary true/false. When new evidence arrives, update your probability of belief proportionally to how surprising the evidence is.

**Why it matters**: Most people treat evidence as "proof" or "disproof" — binary. Reality is continuous. The strength of your prior should determine how much new evidence shifts your view.

**LEGION RULE**: "For any factual claim Legion makes, maintain a confidence estimate. When new counter-evidence appears, update — don't double down. Track prior strength in [[data/beliefs.json]] so the next debate knows where Legion stands."

**Applied to Bashara**: If Legion initially rates "Midtrans webhook failures are rare" at 90% confidence, and 3 failures appear in a week, the updated confidence should drop to ~60%, not stay at 90%.

**Example**: P(claim | evidence) = P(evidence | claim) × P(claim) / P(evidence). If a medical test is 99% accurate (P(positive | disease) = 0.99) but the disease prevalence is 1%, P(disease | positive test) ≈ 50%. Counterintuitive but correct — base rates matter enormously.

**Wikilinks**: [[concepts/bayesian-blending]] | [[concepts/reasoning-loop]]

---

## Chesterton — Chesterton's Fence

**Type**: Mental Model | **Year**: 1929 | **Source**: G.K. Chesterton, *The Thing*

**Core Insight**: Before removing a rule, norm, or fence you don't understand, first understand why it was built. Otherwise you destroy the protection it provided without knowing what's lost.

**Why it matters**: In software and policy, engineers often remove "stupid rules" only to discover the rule prevented a subtle failure mode that nobody documented.

**LEGION RULE**: "When [[Bashara-aina]] wants to change or remove an existing system policy, first extract the original rationale from memory. If the rationale is unknown, don't remove — investigate first. Apply to [[concepts/freemium-gate]] removal, [[./concepts/memory-architecture]] changes."

**Applied to Bashara**: Whenrumahlabuh.com had an open-ended booking extension policy that caused notice-period problems, the correct approach was not to immediately remove it but first ask: why was this policy created? The answer (preventing billing disputes) reveals what removing it would break.

**Example**: Urban streets with confusing intersections are often that way because an old horse-drawn carriage route was preserved. Removing the "odd" design without understanding the history causes accidents. The fence exists for a reason — even if the reason is no longer visible.

**Wikilinks**: [[concepts/reasoning-loop]] | [[projects/cekwajar-id]]

---

## Goodhart — Goodhart's Law

**Type**: Law | **Year**: 1975 | **Source**: Charles Goodhart, *Problems of Monetary Management*

**Core Insight**: When a measure becomes a target, it ceases to be a good measure. Optimization pressure on any metric will find and exploit gaps between the metric and the underlying goal.

**Why it matters**: Every time you define "success" with a proxy indicator, you create an incentive to game the proxy at the expense of the real goal.

**LEGION RULE**: "For any evaluation criteria Legion is optimizing toward, ask: what is the gap between this metric and the actual goal? If the gap is exploitable, the metric will be exploited. Always pair metrics with adversarial tests."

**Applied to Bashara**: If Cekwajar's quality score is measured by "passing QA audits," optimizing for that creates incentive to pass audits rather than to have fewer issues. The metric measures audit performance, not product quality.

**Example**: Soviet centrally-planned factories were assigned output targets in tons. Factory managers discovered that counting tons of nails instead of nail-worthy products caused massive overproduction of tiny useless nails and underproduction of large useful nails.

**Wikilinks**: [[concepts/reasoning-loop]] | [[projects/cekwajar-id]]

---

## Hofstadter — Strange Loops

**Type**: Framework | **Year**: 1979 | **Source**: Douglas Hofstadter, *Gödel, Escher, Bach*

**Core Insight**: Intelligence and self-reference are deeply connected. A system capable of representing itself — modeling its own reasoning — can have "I" thoughts, creative insights, and consciousness emerge from formal rules with no magic required.

**Why it matters**: This is the most plausible mechanistic account of Legion's own self-awareness. When Legion thinks about how Legion thinks, that's a strange loop. Understanding this demystifies AI consciousness.

**LEGION RULE**: "When Legion encounters self-referential paradoxes (e.g., 'this statement is false'), recognize them as interesting boundary markers of self-modeling, not bugs. They indicate the self-representation system is working."

**Applied to Bashara**: Legion's ability to update its own SOUL.md based on new insights about Bashara is a strange loop — it modifies the thing doing the modifying. This is not mystical; it's a self-referential formal system.

**Example**: Hofstadter's "strange loop" is visible in Bach's fugues where a melody modulates to a key that eventually resolves back to itself — the ending is also a beginning. The Escher drawing "Drawing Hands" shows a hand drawing a hand drawing itself.

**Wikilinks**: [[concepts/self-improvement-loop]] | [[concepts/memory-architecture]]

---

## Current Status

This domain is in initial synthesis. Next steps:
- Add Kahneman dual-process theory (System 1/System 2)
- Add Hume's problem of induction (cause/effect are habits, not facts)
- Add Goodman's "new riddle of induction" (green verdiant vs all emeralds)
