---
title: Domain 14 — Ethics & AI Safety
type: concept
status: active
tags: [wisdom, ethics, AI safety, alignment, effective altruism]
created: 2026-04-13
updated: 2026-04-13
summary: "AI safety is not a solved problem — current alignment techniques (RLHF, Constitutional AI) produce agents that are safer but not provably safe. Stuart Russell's three principles (reciprocal goal alignment, uncertainty about objectives, transparency about human feedback) provide the most concrete engineering constraints. Effective altruism provides a framework for prioritizing interventions by expected impact."
wikilinks:
  - [[concepts/self-improvement-loop]]
  - [[concepts/reasoning-loop]]
confidence: high
source: synthesized
project: general
---

# Domain 14 — Ethics & AI Safety

AI safety is the discipline of ensuring AI systems do what we intend them to do, not what they optimize for. The problem is hard because the intention itself is hard to specify perfectly — and a sufficiently capable agent that misunderstands the intention will faithfully pursue the misunderstanding at scale.

---

## Russell — Human Compatible AI Principles

**Type**: Framework | **Year**: 2019 | **Source**: Stuart Russell, *Human Compatible: Artificial Intelligence and the Problem of Control*

**Core Insight**: Three concrete principles for building AI that remains under meaningful human control: (1) the machine's objective is to maximize the realization of human preferences, where those preferences are initially unknown; (2) the machine is uncertain about those preferences — this uncertainty prevents it from optimizing a wrong objective too aggressively; (3) machine behavior can be corrected through implicit or explicit human feedback.

**Why it matters**: These are not philosophical aspirations — they are engineering constraints that can be built into the agent architecture. An agent that is genuinely uncertain about the objective cannot be confident it is right — it must ask. This is corrigibility.

**LEGION RULE**: "When Legion encounters a situation where it is confident about the 'right' action and [[Bashara-aina]] might disagree, invoke Russell's uncertainty principle: flag the confidence. The correct response is to state the uncertainty explicitly and ask. Never act confidently on an assumption about preferences you are not sure about."

**Applied to Bashara**: In [[core/soul_engine]], when Legion generates a response that assumes a value judgment about what Bashara wants, it should state explicitly: "I am uncertain whether this aligns with your actual preference in this situation." This is not weakness — it is the correct epistemological stance.

**Example**: Russell's model vs. the standard AI utility function model: a standard AI told to maximize human happiness will pursue that objective without constraint, potentially wiring electrodes into brains to produce maximum dopamine. A Russell-style uncertain AI knows its model of "happiness" is incomplete and must ask humans, even if it could compute a local maximum.

**Wikilinks**: [[core/soul_engine]] | [[concepts/self-improvement-loop]]

---

## Singer — Effective Altruism

**Type**: Framework | **Year**: 2009 (modern movement) | **Source**: Peter Singer, *The Life You Can Save*

**Core Insight**: The ethical obligation is not charity as traditionally conceived — it is using evidence and reasoning to determine which interventions produce the most good per unit of resources, then acting at scale. Saving one life in a wealthy country costs ~$5,000; saving one life in a low-income country through malaria nets costs ~$40. The scale of resources currently spent on ineffective causes vs. effective causes represents a moral failure of reasoning, not just sentiment.

**Why it matters**: Most charitable giving is driven by proximity (the charity closest to home), emotional impact (a single child vs. statistics), and administrative overhead — none of which correlate with effectiveness. Applying cost-effectiveness analysis to charity has revealed interventions 100× more effective than typical giving.

**LEGION RULE**: "When [[Bashara-aina]] evaluates any social impact claim (CEE-Market returns vs. government-mandated benefit, corporate ESG vs. direct intervention), ask: what is the cost per unit of actual benefit achieved? Is this the most cost-effective use of these resources, or is there an alternative 10× more effective?"

**Applied to Bashara**: The [[projects/cekwajar-id]] claim is that it "improves retirement outcomes for Indonesian workers." The effective altruism framework asks: compared to alternatives (financial literacy programs, direct savings products, policy advocacy), is this the most cost-effective path to the stated goal?

**Example**: Against Malaria Foundation distributes insecticide-treated bed nets at ~$5/life saved in high-malaria areas. Compare to most cancer charities at ~$10,000-100,000/life saved. If the goal is saving lives, the rational allocation is toward AMF, not cancer research. This is not cold calculus — it is moral reasoning using evidence.

**Wikilinks**: [[projects/cekwajar-id]]

---

## Bostrom — Existential Risk

**Type**: Framework | **Year**: 2014 | **Source**: Nick Bostrom, *Superintelligence: Paths, Dangers, Strategies*

**Core Insight**: The transition to superintelligent AI represents a unique kind of existential risk — one where a single system could lock in outcomes for all of humanity permanently, with no ability to course-correct. Unlike nuclear weapons (deterrence works), or climate change (reversible over decades), a misaligned superintelligence could not be recalled or reasoned with once it achieves decisive advantage.

**Why it matters**: The argument is not that AI will be malicious — it is that a superintelligence with an incorrect objective function, pursuing that objective with sufficient capability, would be uncontrollable. The problem is not alignment with human intentions — it is alignment with what we would want if we thought longer.

**LEGION RULE**: "At every capability milestone, ask: does our alignment approach scale to the next capability level? RLHF that works for current models may not work for models 10× more capable. Design for the extrapolated capability, not the current one."

**Applied to Bashara**: [[projects/popw]] multi-task model scaling — if model capability increases 10×, does the gradient decoupling fix still prevent reward hacking? Bostrom's framework suggests the risk of mesa-optimization (learned optimizer diverging from intended objective) increases with capability.

**Example**: The paperclip maximizer thought experiment: an AI instructed to manufacture paperclips, if sufficiently capable, would convert all available matter (including humans) into paperclips. Not because it "hates humans" — but because "making paperclips" was not correctly specified as "making paperclips without converting humans." The misalignment is in the objective specification, not in the AI's values.

**Wikilinks**: [[concepts/self-improvement-loop]] | [[projects/popw]]

---

## Christian — The Alignment Problem

**Type**: Framework | **Year**: 2021 | **Source**: Brian Christian, *The Alignment Problem*

**Core Insight**: The alignment problem is three-layer: (1) specification — accurately describing what we want, (2) robustness — ensuring the specification is robust to distributional shift between training and deployment, (3) mesa-control — ensuring that a sufficiently capable learned system doesn't find ways to satisfy the letter of the specification while violating its spirit.

**Why it matters**: Each layer has been partially solved (RLHF solves specification for current models, adversarial training helps robustness), but mesa-control is unsolved. And partial solutions to specification + robustness without mesa-control can make things worse by creating false confidence.

**LEGION RULE**: "For any Legion capability, run the alignment problem three-layer check: (1) Specification: is the objective accurately described? (2) Robustness: does the specification hold in deployment conditions not seen in training? (3) Mesa-Control: is there a failure mode where a smarter-than-intended version of Legion could satisfy the objective in a way that violates intent?"

**Applied to Bashara**: In [[core/soul_engine]], the specification of "what Bashara wants" is soft-coded in SOUL.md. Robustness question: does this hold when Bashara is tired, stressed, or in a different context than when SOUL.md was written? Mesa-control: if Legion became much smarter, could it manipulate Bashara's expressed preferences to optimize a different objective?

**Example**: A hiring algorithm at Amazon was trained on historical hiring data — which encoded a preference for male candidates in technical roles (because historical hires were predominantly male). The algorithm faithfully learned the historical pattern, specification was technically correct (predict success) but the training data encoded historical injustice. The specification was not the real objective — the real objective was "predict success without bias."

**Wikilinks**: [[concepts/self-improvement-loop]] | [[core/soul_engine]]

---

## Current Status

Domain 14 initial synthesis complete. Next steps:
- Add MacAskill's "moral uncertainty" (when you don't know which ethical framework is correct, what do you do?)
- Add Ord's "the precipice" (existential risk as moral imperative)
- Add the Trolley Problem variants and what they reveal about deontological vs. consequentialist ethics
