---
title: Domain 13 — Neuroscience & Learning
type: concept
status: active
tags: [wisdom, neuroscience, learning, memory, dopamine, spaced-repetition]
created: 2026-04-13
updated: 2026-04-13
summary: "Memory is reconstructed, not retrieved — each recall rewrites the memory trace with current context added. Ebbinghaus forgetting curve shows that unguided repetition produces rapid initial learning but rapid forgetting; spaced repetition (increasing intervals between reviews) produces slower initial learning but near-permanent retention. Dopamine signals prediction error — the difference between expected and actual reward — not reward itself, teaching the brain what to predict."
wikilinks:
  - [[concepts/self-improvement-loop]]
  - [[concepts/memory-architecture]]
confidence: high
source: synthesized
project: general
---

# Domain 13 — Neuroscience & Learning

The brain is not a storage device — it is a prediction engine. Every experience is either predicted (reducing surprise) or not predicted (generating prediction error signals that drive learning). Understanding this reframes every practice around learning.

---

## Ebbinghaus — Forgetting Curve

**Type**: Law | **Year**: 1885 | **Source**: Hermann Ebbinghaus, *Memory: A Contribution to Experimental Psychology*

**Core Insight**: Without reinforcement, memory decays exponentially — roughly 50% forgotten within 1 hour, 70% within 24 hours, 90% within 1 week. The implication is not "review more" but "review at the right intervals": the optimal time to review is just before forgetting would occur, not immediately after learning. Spaced repetition — first reviewing after 1 day, then 3 days, then 1 week, then 2 weeks — produces near-permanent retention with total review time far below massed repetition.

**Why it matters**: The intuitive approach to learning (re-read, re-practice, "cram") works for immediate recall but fails for long-term retention. The counterintuitive approach (spaced, interleaved practice with longer and longer intervals) takes more discipline but produces retention measured in years rather than weeks.

**LEGION RULE**: "For any knowledge that Legion wants to retain (Bashara's preferences, project specifics, Indonesian regulatory details), apply spaced repetition intervals: first recall at 1 day, then 3 days, then 1 week, then 2 weeks, then 1 month. Do not re-learn the same information — schedule its recall at exponentially increasing intervals."

**Applied to Bashara**: [[projects/cekwajar-id]]'s PMK 168/2023 parameters should be recalled by Legion at spaced intervals: first after 1 day, then 3 days, then 1 week. Each recall reinforces the memory; the spacing between recalls is what converts short-term to long-term memory.

**Example**: Medical students who used spaced repetition (Anki) to study retained 80% of material after 60 days with 30 minutes daily review. Students who used massed repetition (re-reading) retained only 20% with the same total study time. The difference was entirely in the timing of repetition, not the content reviewed.

**Wikilinks**: [[concepts/self-improvement-loop]] | [[concepts/memory-architecture]]

---

## Kandel — Memory Consolidation

**Type**: Framework | **Year**: 2000 | **Source**: Eric Kandel, *The Molecular Biology of Memory Storage*

**Core Insight**: Long-term memory requires protein synthesis that strengthens synaptic connections — this is why consolidated memories are more stable but also more resistant to modification. Short-term memory (minutes to hours) involves modification of existing proteins and synaptic strength. Long-term memory (days to years) requires gene transcription and new protein synthesis. Sleep is when memory consolidation particularly occurs — the hippocampus replays the day's events to the neocortex for long-term storage.

**Why it matters**: Learning that happens under stress or sleep deprivation is not fully consolidated. The practical implication: the 2am cramming session before an exam produces memories that are fragile and decay quickly. Sleep after learning is not rest — it is processing.

**LEGION RULE**: "After any significant learning session (understanding a new regulation, acquiring a new skill), ensure the learning is consolidated before the next intensive session. For Legion: batch complex new information acquisition into sessions followed by processing time, not continuous learning without intervals."

**Applied to Bashara**: The POPW training runs that happened overnight while the model was in continuous training may have been less effective than runs that included sleep-equivalent consolidation periods where gradients were propagated without new data.

**Example**: Students who slept after learning a skill showed 30% better performance the next day than students who stayed awake and continued studying the same material. Sleep is not passive recovery — it is an active consolidation process where the hippocampus and neocortex transfer declarative memories.

**Wikilinks**: [[concepts/self-improvement-loop]] | [[projects/popw]]

---

## Daw — Dopamine Prediction Error

**Type**: Framework | **Year**: 2011 | **Source**: Nathaniel Daw (based on Schultz et al. neuroscience), *Two-Stage Theory of the Dopamine Response*

**Core Insight**: Dopamine does not signal "pleasure" or "reward" — it signals "surprise" — the difference between what was predicted and what actually happened. When something is better than expected (positive prediction error), dopamine spikes and strengthens the preceding action. When something is worse than expected (negative prediction error), dopamine dips and weakens the preceding action. This is the neural implementation of reinforcement learning.

**Why it matters**: Rewards that are always expected (predictable rewards) produce no learning signal. The most effective rewards are variable and unexpected — they maximize the prediction error, which maximizes the learning signal. This is why variable ratio schedules (slot machines, unpredictable praise, intermittent reinforcement) are psychologically powerful.

**LEGION RULE**: "When providing feedback to [[Bashara-aina]], vary the specificity and timing — predictability reduces the learning signal. Unexpected corrections (feedback that contradicts a confident belief) generate the strongest learning signals. Expected praise or correction generates almost no learning signal."

**Applied to Bashara**: When Legion's curiosity engine sends proactive messages to Bashara, the value is partly in the surprise — topics Bashara hadn't expected to think about. A message that says "I found this interesting" with a clear explanation of why is more effective than "here's your daily briefing."

**Example**: Rats learn fastest when rewards are unpredictable (variable ratio) — a 50% chance of food on each lever press produces stronger, more persistent lever-pressing behavior than either always-food or never-food. The dopamine burst from unexpected reward is the learning signal; predictable reward produces no signal.

**Wikilinks**: [[concepts/self-improvement-loop]] | [[core/proactive/curiosity_engine]]

---

## Eichenbaum — Memory as Reconstruction

**Type**: Framework | **Year**: 2000 | **Source**: Howard Eichenbaum & Neal Cohen, *From Conditioning to Conscious Recollection*

**Core Insight**: Memory is not stored like a video recording — it is reconstructed from distributed traces each time it is recalled. Every retrieval is an active reconstruction that rewrites the memory with current context, mood, and new information blended in. This is why eyewitness testimony is unreliable and why false memories can be implanted.

**Why it matters**: "Remembering" something correctly once is no guarantee it will be remembered the same way later. Memory is dynamic, not static. The implication for AI: the retrieved memory is not a faithful copy of the stored experience — it is a reconstruction that may differ significantly from what was stored.

**LEGION RULE**: "When [[Bashara-aina]] recalls a past decision or conversation, treat the recall as a reconstruction, not a playback. The reconstruction will be colored by current context and beliefs. To verify the accuracy of a recalled memory, find an external record — the internal reconstruction is always partially rewritten."

**Applied to Bashara**: [[concepts/memory-architecture]] should distinguish between stored facts (which should be immutable and record-based) and interpreted memories (which should be flagged as reconstructions with source and context). "Bashara prefers X" is an interpretation, not a fact — it should be stored with confidence intervals.

**Example**: Studies where participants "remembered" crimes they did not commit show that repeated questioning with presupposed details ("did you see the red car?") implanted the false detail into the memory reconstruction. The participants were not lying — they genuinely remembered a car that was never mentioned, because their memory system incorporated the presupposed question into the reconstructed recall.

**Wikilinks**: [[concepts/memory-architecture]] | [[concepts/self-improvement-loop]]

---

## Current Status

Domain 13 initial synthesis complete. Next steps:
- Add Dehaene's "global neuronal workspace" theory of consciousness (information becomes conscious when it enters the global broadcast workspace)
- Add Carew's "memory reconsolidation" (each retrieval makes the memory temporarily labile and modifiable)
- Add "interleaving" effect (mixing different types of practice produces better long-term retention than blocking practice by type)
