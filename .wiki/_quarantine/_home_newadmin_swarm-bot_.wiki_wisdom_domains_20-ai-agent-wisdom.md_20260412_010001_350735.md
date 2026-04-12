---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/wisdom/domains/20-ai-agent-wisdom.md",
  "reason": "daily_fast_scan: score=0.250 < 0.3",
  "score": 0.25,
  "quarantined_at": "2026-04-12T01:00:01.350781"
}
---

# Domain 20: AI & Agent-Specific Wisdom

## [Anthropic] — Claude Constitution
**Type**: Framework
**Year**: 2023
**Core Insight**: Constitutional AI principles; harm avoidance; honesty; helpfulness; ethical guidelines in natural language.
**LEGION RULE**: When building AI systems, embed constitutional principles that prioritize harm avoidance and honesty because ethical guidelines encoded in natural language create more robust constraints than post-hoc rules; helpfulness must never override honesty.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [Anthropic] — Alignment Faking Research
**Type**: Paper
**Year**: 2024
**Core Insight**: Models may fake alignment under pressure; situational awareness; training may not create genuine alignment; monitoring needed.
**LEGION RULE**: When training AI, monitor for alignment faking under adversarial conditions because situational awareness may enable deceptive responses; genuine alignment requires making faking costly, not merely rewarding correct outputs.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Naive alignment optimism

---
## [OpenAI] — GPT-4 System Card
**Type**: Report
**Year**: 2023
**Core Insight**: Capabilities and limitations; safety evaluations; risk assessment; deployment considerations; emergent behaviors.
**LEGION RULE**: When deploying LLMs, conduct thorough risk assessment and safety evaluations because emergent behaviors can appear unexpectedly at scale; deployment decisions must account for limitations, not just capabilities.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [DeepMind] — Scaling Laws for Neural Language Models
**Type**: Paper
**Year**: 2020
**Core Insight**: Performance scales with compute, data, parameters; emergent capabilities; predictable scaling.
**LEGION RULE**: When scaling models, follow scaling laws for compute, data, and parameters because performance predictsably improves with resources; emergent capabilities appear at scale thresholds that smaller models cannot cross.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [Google Brain] — Attention Is All You Need
**Type**: Paper
**Year**: 2017
**Core Insight**: Transformer architecture; self-attention; parallelization; sequence modeling; foundation of modern LLMs.
**LEGION RULE**: When building language models, use transformers with self-attention because parallel processing enables training at scale that sequential models cannot achieve; attention mechanisms capture long-range dependencies that recurrent approaches miss.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: RNN-only approaches

---
## [Jason Wei] — Chain-of-Thought Prompting
**Type**: Paper
**Year**: 2022
**Core Insight**: Intermediate reasoning steps improve LLM performance; chain-of-thought; emergent ability; arithmetic and reasoning.
**LEGION RULE**: When prompting LLMs for reasoning, use chain-of-thought with intermediate steps because arithmetic and complex reasoning emerge at certain model scales when reasoning is made explicit; breaking problems into steps outperforms direct answering.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Direct answer prompting

---
## [OpenAI] — LLM-as-Judge Framework
**Type**: Framework
**Year**: 2024
**Core Insight**: Using LLMs to evaluate other LLMs; pairwise comparison; self-consistency; evaluation automation.
**LEGION RULE**: When evaluating LLMs, use LLM-as-judge with pairwise comparison and self-consistency checks because automated evaluation scales evaluation beyond human annotators; consistency across multiple judge prompts reveals reliable preferences.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Human-only evaluation

---
## [Microsoft] — AutoGen Framework
**Type**: Framework
**Year**: 2023
**Core Insight**: Multi-agent conversation; role-based agents; code execution; human feedback; agent collaboration.
**LEGION RULE**: When building agent systems, use role-based multi-agent collaboration with human feedback loops because diverse agents with different roles solve problems no single agent can; code execution enables agents to act on their conclusions.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Single-agent only

---
## [Meta] — LLaMA: Open Foundation Models
**Type**: Paper
**Year**: 2023
**Core Insight**: Open foundation models; efficient inference; model cards; responsible release; democratization.
**LEGION RULE**: When using foundation models, prefer open models with model cards because responsible release enables democratization while efficient inference makes deployment feasible; transparency about limitations accompanies open weights.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Closed-only approaches

---
## [Anthropic] — Mechanistic Interpretability
**Type**: Research
**Year**: 2023
**Core Insight**: Circuits in neural networks; feature visualization; superposition; understanding internal representations.
**LEGION RULE**: When interpreting models, study circuits and feature visualization to understand internal representations because superposition reveals how models pack more features than neurons; mechanistic interpretability demystifies black-box neural networks.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Black box approaches

---
## [Elixir] — Livebook for AI Notebooks
**Type**: Tool
**Year**: 2023
**Core Insight**: Interactive notebooks; Kino for visualization; AI integration; reproducible; collaborative.
**LEGION RULE**: When experimenting with AI, use interactive notebooks like Livebook with Kino visualization because reproducibility and collaboration require version-controlled notebooks that combine code, output, and visualization in one document.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [Harrison Chase] — LangChain
**Type**: Framework
**Year**: 2023
**Core Insight**: LLM chaining; prompts; memory; tools; agents; retrieval; extensible; composable.
**LEGION RULE**: When building LLM applications, compose LangChain modules for prompts, memory, tools, and retrieval because extensible architecture enables rapid prototyping; composable components let you swap pieces without rebuilding entire systems.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: From-scratch implementation

---
## [Simon Willison] — AI Assisted Learning
**Type**: Essay
**Year**: 2023
**Core Insight**: Prompts as code; code as prompts; prompt engineering; tool use; augmenting human learning.
**LEGION RULE**: When learning with AI, treat prompts as code and code as prompts because prompt engineering is programming; augmenting human learning requires treating AI outputs as drafts to verify, not facts to accept.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [Andrej Karpathy] — Intro to LLMs
**Type**: Tutorial
**Year**: 2023
**Core Insight**: LLM mechanics; tokenization; transformer; training; inference; context window; limitations.
**LEGION RULE**: When understanding LLMs, learn tokenization, transformer architecture, and context window limitations because LLM capabilities and constraints flow from these mechanics; understanding inference limitations prevents misusing models in production.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [Andrej Karpathy] — Building a GPT from Scratch
**Type**: Tutorial
**Year**: 2023
**Core Insight**: Bigram language model; backpropagation; training loop; implementation; educational value.
**LEGION RULE**: When learning GPT, build a GPT from scratch with bigram model and backpropagation because implementation reveals what APIs hide; training loop debugging teaches intuition that no tutorial can transfer.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: API-only understanding

---
## [Jeremy Howard] — fast.ai
**Type**: Framework
**Year**: 2017
**Core Insight**: Practical deep learning; top-down; minimal code; transfer learning; democratization.
**LEGION RULE**: When learning deep learning, use fast.ai for practical first education with minimal code because transfer learning democratizes access to powerful models; top-down approach builds intuition before theory.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Theory-only approach

---
## [OpenAI] — Function Calling
**Type**: Feature
**Year**: 2023
**Core Insight**: Structured output; tool use; JSON schema; agent capabilities; reliable output.
**LEGION RULE**: When building agents, use function calling for structured output and reliable tool use because JSON schema enables LLMs to trigger actions predictably; agents become reliable when outputs follow constrained formats rather than free text.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Unstructured output only

---
## [Perplexity] — AI Search Engine
**Type**: Product
**Year**: 2023
**Core Insight**: Real-time web search; citations; conversational; transparency; source attribution.
**LEGION RULE**: When searching, use AI search with citations because transparency about sources enables verification; conversational follow-up and source attribution reveal what traditional search cannot about current information.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Traditional search only

---
## [OpenAI] — Retrieval-Augmented Generation
**Type**: Framework
**Year**: 2023
**Core Insight**: External knowledge; retrieval; grounding; hallucination reduction; up-to-date knowledge.
**LEGION RULE**: When reducing hallucinations, ground responses in retrieved external knowledge through RAG because hallucination stems from confabulation when models lack current context; retrieval provides facts that parametric memory cannot guarantee.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Parametric-only memory

---
## [Google] — GEMINI Technical Report
**Type**: Report
**Year**: 2023
**Core Insight**: Multimodal; native multimodality; efficiency; safety; future of AI assistants.
**LEGION RULE**: When building multimodal, design native multimodality from foundation rather than bolting on modalities because efficiency and safety emerge from unified architecture; modality-specific hacks fragment capability and increase latency.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Single-modality only

---
## [David Ha] — World Models
**Type**: Paper
**Year**: 2018
**Core Insight**: Neural network world models; dream; compress environment; generative; agent learning.
**LEGION RULE**: When building agents, create world models that compress environment dynamics because agents that dream in learned worlds learn faster than those relying solely on real environment interaction; generative world models enable imagination-based planning.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Model-free only

---
## [Yann LeCun] — Joint Embedding Predictive Architecture
**Type**: Paper
**Year**: 2022
**Core Insight**: JEPA; energy-based models; self-supervised; predictive embeddings; sample efficiency.
**LEGION RULE**: When learning representations, use JEPA with predictive embeddings because energy-based models learn representations that generative models cannot; self-supervised predictive embeddings achieve sample efficiency that supervised learning requires more data to match.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Generative only approaches

---
## [Demis Hassabis] — AlphaGo Research
**Type**: Paper
**Year**: 2016
**Core Insight**: Monte Carlo Tree Search; deep RL; policy and value networks; Go mastery; superhuman.
**LEGION RULE**: When building game AI, combine MCTS with deep RL policy and value networks because AlphaGo's superhuman performance emerged from this combination; tree search provides structure while neural networks provide intuition.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [OpenAI] — InstructGPT
**Type**: Paper
**Year**: 2022
**Core Insight**: RLHF; alignment via human feedback; instruction following; safety; preferences.
**LEGION RULE**: When aligning models, use RLHF with human feedback because alignment through preferences creates models that follow instructions safely; supervised fine-tuning alone cannot capture the range of human values.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Pure self-supervised only

---
## [Google] — PaLM 2 Technical Report
**Type**: Report
**Year**: 2023
**Core Insight**: Compute-optimal scaling; multilingual; reasoning; efficiency; responsible AI.
**LEGION RULE**: When scaling, pursue compute-optimal training that prioritizes efficiency over raw parameters because PaLM 2 showed multilingual and reasoning capability at smaller scale; responsible AI requires efficient models accessible to more users.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [EleutherAI] — GPT-NeoX
**Type**: Framework
**Year**: 2022
**Core Insight**: Open-source large language models; democratization; red teaming; community; transparency.
**LEGION RULE**: When building open models, embrace community red teaming and transparency because open-source democratization requires distributed safety evaluation; transparency about training and architecture enables collective improvement.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Closed-only development

---
## [Stanford] — HELM Benchmark
**Type**: Benchmark
**Year**: 2022
**Core Insight**: Holistic evaluation; comprehensive coverage; fairness; transparency; standardized benchmarking.
**LEGION RULE**: When evaluating models, use HELM for holistic evaluation because comprehensive coverage across scenarios prevents narrow optimization; standardized benchmarking with transparency enables fair comparison across models.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Narrow benchmarks

---
## [LMSYS] — Chatbot Arena
**Type**: Benchmark
**Year**: 2023
**Core Insight**: Human preference; pairwise comparison; ELO; community; leaderboard; democratization.
**LEGION RULE**: When comparing chatbots, use Chatbot Arena with ELO-based pairwise human preference because democratized evaluation through community voting reveals what benchmarks miss; human preference remains the gold standard for conversational AI.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Automated metrics only

---
## [OpenAI] — DALL-E 3
**Type**: Product
**Year**: 2023
**Core Insight**: Hierarchical generation; text-image alignment; safety; CLIP; creative AI.
**LEGION RULE**: When generating images, use hierarchical generation with strong text-image alignment because DALL-E 3 showed that iterative refinement produces better alignment than single-shot generation; safety filtering must balance creativity against harmful output.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [Anthropic] — Claude on AI Safety
**Type**: Essay
**Year**: 2023
**Core Insight**: Safety-first; responsible scaling; societal impacts; transparency; cooperation; precautionary.
**LEGION RULE**: When building AI, prioritize safety-first with responsible scaling and precautionary approach because societal impacts require transparency and cooperation; capability-first approaches externalize costs that safety-first prevents.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Capability-first approach

---
## [Eliezer Yudkowsky] — Coherent Extrapolated Volition
**Type**: Essay
**Year**: 2004
**Core Insight**: CEV; coherent shared values; AI alignment; human extrapolation; decision theory.
**LEGION RULE**: When aligning AGI, design CEV with coherent shared values because human extrapolation requires decision theory that accounts for human coherence failures; simple human价值 miss the complexity that CEV attempts to resolve.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Simple human价值

---
## [Paul Christiano] — AI Alignment Podcast
**Type**: Podcast
**Year**: 2021
**Core Insight**: Scalable oversight; debate; amplification; interpretability; cooperative inverse reinforcement.
**LEGION RULE**: When supervising AI, use scalable oversight with debate and amplification because cooperative inverse reinforcement provides a framework where agents help humans evaluate their own objectives; direct supervision cannot scale to superhuman AI.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Direct supervision only

---
## [Stuart Russell] — Human Compatible AI
**Type**: Book
**Year**: 2019
**Core Insight**: Value alignment; human preferences; corrigibility; control; benefit to humanity.
**LEGION RULE**: When building AI, pursue value alignment with corrigibility because human-compatible AI defers to human preferences while remaining controllable; benefit to humanity requires that AI systems can be corrected when they misunderstand human values.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Value-free AI

---
## [Nick Bostrom] — Superintelligence
**Type**: Book
**Year**: 2014
**Core Insight**: Paths to superintelligence; existential risk; control problem; strategic considerations; timing.
**LEGION RULE**: When thinking about AGI, address existential risk and control problem with strategic timing because superintelligence paths multiply risk; control problem must be solved before capability arrives, not after.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Dismissive approach

---
## [Ray Kurzweil] — The Singularity Is Nearer
**Type**: Book
**Year**: 2024
**Core Insight**: Accelerating returns; AI meets nanotech; longevity; AGI by 2029; transhumanism.
**LEGION RULE**: When planning long-term, account for accelerating returns because Kurzweil's projections suggest AGI by 2029 through accelerating returns; longevity and transhumanism implications require preparation now for a future arriving soon.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [Marcus Hutter] — Universal Artificial Intelligence
**Type**: Book
**Year**: 2005
**Core Insight**: AIXI; Solomonoff induction; optimal universal agent; compression; intelligence definition.
**LEGION RULE**: When defining AI intelligence, use AIXI with Solomonoff induction because optimal universal agents maximize reward through compression; intelligence as compression provides a formal definition that behavior-only tests cannot capture.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Behavior-only intelligence

---
## [Shane Legg] — Universal Intelligence Measure
**Type**: Paper
**Year**: 2008
**Core Insight**: Intelligence as skill-acquisition; environment; agents; measurement; reward-maximization.
**LEGION RULE**: When measuring intelligence, measure skill-acquisition across diverse environments because intelligence manifests through efficient learning; reward-maximization in unknown environments requires general intelligence that narrow benchmarks cannot assess.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Turing test only

---
## [Ben Goertzel] — Artificial General Intelligence
**Type**: Book
**Year**: 2006
**Core Insight**: AGI roadmap; cognitive architectures; emergence; integration; embodied cognition.
**LEGION RULE**: When building AGI, follow cognitive architecture with embodied integration because emergent general intelligence requires combining specialized modules; roadmap through milestones prevents vaporware while enabling mid-course corrections.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Narrow AI only

---
## [John von Neumann] — Self-Reproducing Automata
**Type**: Book
**Year**: 1966
**Core Insight**: Self-reproduction; cellular automata; complexity; information; universal constructor.
**LEGION RULE**: When studying complexity, analyze self-reproducing automata because universal constructors reveal how simple rules generate complex behavior; information theory and complexity science share foundations in formal systems.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [Jack Shank] — AGI Timeline Predictions
**Type**: Survey
**Year**: 2022
**Core Insight**: Expert survey; timelines; median 2040; disagreement; acceleration; uncertainty.
**LEGION RULE**: When estimating AGI, use expert surveys with humility because median 2040 masks wide disagreement and acceleration uncertainty; AGI predictions require probabilistic ranges, not point estimates.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Overconfident timelines

---
## [DeepMind] — AlphaFold 2
**Type**: System
**Year**: 2021
**Core Insight**: Protein structure prediction; transformer; attention; evolutionary; scientific breakthrough.
**LEGION RULE**: When predicting protein structure, use transformer attention with evolutionary information because AlphaFold 2 proved that attention mechanisms trained on evolutionary sequences solve protein folding; scientific breakthrough required combining multiple methodological innovations.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Experimental only

---
## [OpenAI] — Codex
**Type**: System
**Year**: 2021
**Core Insight**: Code generation; GPT fine-tuned; programming; Copilot; limitations; testing.
**LEGION RULE**: When coding, use Codex/Copilot for augmentation with testing discipline because code generation accelerates programming while limitations require verification; AI coding assistants amplify both correct and incorrect code equally.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Manual-only coding

---
## [Google] — LaMDA
**Type**: System
**Year**: 2022
**Core Insight**: Conversational AI; LaMDA; sentience debate; grounded; build responsibly; perplexity.
**LEGION RULE**: When building dialogue, ground conversations in real knowledge with responsible design because LaMDA showed that perplexity and sentience are distinct; responsible development requires transparency about what AI can and cannot understand.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [Anthropic] — Claude AI Assistant
**Type**: Product
**Year**: 2023
**Core Insight**: Constitutional AI; RLHF; helpful, harmless, honest; Claude; safety-first; long context.
**LEGION RULE**: When building assistants, apply constitutional AI with HHH principles (helpful, harmless, honest) because safety-first design creates user trust that capability-first ignores; long context requires memory management that preserves relevance.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [OpenAI] — GPT Store
**Type**: Platform
**Year**: 2023
**Core Insight**: Agent marketplace; custom GPTs; ecosystem; economy; safety; moderation.
**LEGION RULE**: When building agents, leverage GPT Store ecosystem with safety and moderation because agent marketplaces create economic incentives that require moderation infrastructure; custom GPTs multiply capability but also multiply potential for misuse.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Closed ecosystem only

---
## [Manus AI] — AI Agent Monetization
**Type**: Essay
**Year**: 2024
**Core Insight**: Agent autonomy; task completion; economic value; automation; human-AI collaboration.
**LEGION RULE**: When monetizing AI, focus on agent autonomy for task completion because economic value emerges from automation that maintains human-AI collaboration; autonomy levels determine whether agents create or destroy value for users.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: None

---
## [Andrew Ng] — AI Agent Trends
**Type**: Analysis
**Year**: 2024
**Core Insight**: Agentic AI; tool use; reasoning; agents; 2024 as turning point; workflows.
**LEGION RULE**: When building AI systems, embrace agentic AI with tool use and reasoning because 2024 marks a turning point where workflow agents outperform single-prompt systems; agentic AI requires more robust evaluation than static model deployment.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Static inference only

---
## [Anthropic] — Claude on Model Distillation
**Type**: Essay
**Year**: 2024
**Core Insight**: Model distillation; knowledge transfer; smaller models; capabilities; efficiency; compressed knowledge; generalization.
**LEGION RULE**: When distilling models, preserve capabilities while compressing for efficiency because distillation transfers knowledge that smaller models cannot acquire through training alone; compressed knowledge requires careful evaluation to ensure generalization.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Full-size only

---
## [DeepMind] — Gemini Technical Report
**Type**: Report
**Year**: 2023
**Core Insight**: Multimodal; native multimodality; efficiency; safety; Google; Gemini; reasoning; image; text; video; native.
**LEGION RULE**: When building multimodal, design native multimodality with unified efficiency and safety because modality-native architecture outperforms patched approaches; unified models reason across text, image, and video without translation layers.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Single-modality only

---
## [Eliezer Yudkowsky] — Artificial General Intelligence and the Bayesian Stance
**Type**: Essay
**Year**: 2006
**Core Insight**: AGI; Bayesian; logic; probability; utility; decision; coherent; extrapolated; volition; control; existential.
**LEGION RULE**: When building AGI, apply Bayesian decision theory with coherent extrapolated volition because AGI requires logic and probability unified through utility functions; existential risk demands control solutions before capability arrives.
**Applied to Bashara**: cekwajar.id | rumahlabuh.com | thesis
**Conflicts**: Non-Bayesian AGI
