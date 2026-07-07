---
name: genai-proofreader
description: "Multi-persona LaTeX proofreader — Domain Expert and Language Expert persona prompts for section-by-section review of scientific papers. Use when the user wants LLM-based proofreading with specialized role-based feedback (not structural/checklist review). Complements /paperdebugger (structural review) by providing full-text persona-grounded critique."
trigger: /genai-proofreader
---

# /genai-proofreader

Proofread LaTeX papers using specialized AI personas. Uses the well-engineered prompt patterns from GenAI LaTeX Proofreader (https://github.com/genai-latex-proofreader/genai-latex-proofreader).

## Approach

Uses **two proofreading personas** that each review every section of the paper:

**Domain Expert** — critically evaluates:
- Motivation: Is the problem well-motivated?
- Correctness: Are the mathematical/scientific arguments sound?
- Clarity: Are ideas expressed clearly and concisely?
- Consistency: Consistent use of terminology and notation
- Completeness: Are all necessary details provided?
- References: Appropriate citation usage
- Summary: Main strengths, weaknesses, and future research directions

**Language Expert** — focuses on:
- Grammar: Grammatical errors and corrections
- Spelling: Typos and spelling mistakes
- Formatting: Consistent use of italics, bold, capitalization
- Punctuation: Proper punctuation throughout
- Consistency: UK vs US English, dialect consistency
- Clarity: Sentence-level rewording suggestions while preserving author voice
- Flow: Transition quality between sentences and paragraphs

## Key Principles

- **Section-by-section**: Each section is proofread independently with full-paper context
- **LaTeX-aware feedback**: All suggestions are valid LaTeX — references use `\ref{}`, formulas use `$...$`, enumerate environments
- **Actionable suggestions**: Each issue includes specific location (`\ref{sec:foo}`), what to change, and how to change it
- **Never modify paper**: Suggestions are appended as comments — the paper is never modified
- **LaTeX guard**: AI-generated feedback is compiled and auto-fixed if LaTeX errors are introduced

## Usage Patterns

### Full proofreading run (requires ANTHROPIC_API_KEY)

```bash
cd tools/genai-latex-proofreader
pip install -r requirements.txt
export ANTHROPIC_API_KEY='your-key'
python3 -m genai_latex_proofreader.cli \
  --input_latex_path /path/to/paper/main.tex \
  --output_report_filepath /path/to/output/report.tex
```

### Manual persona-based proofreading (no API key needed)

Use the prompt patterns directly with any LLM:

```
Based on the Domain Expert prompts in .claude/reference/genai-proofreader/domain_expert_prompts.py,
proofread this section: [paste LaTeX section]
```

Or ask Claude:

```
/genai-proofreader "Proofread my paper at papers/my-paper/main.tex as both Domain Expert and Language Expert"
```

## Persona Prompt Architecture

The prompts are carefully engineered for LaTeX-aware feedback:

### System Prompt Pattern
- Establishes the persona's identity, experience level, and domain expertise
- Defines what the persona is known for and what they focus on
- Sets expectations about the persona's reputation and standards

### Instructions Prompt Pattern
- Uses `<latex_to_proofread>` XML tags to clearly delimit the content
- Defines specific focus areas with bullet points
- Requires valid LaTeX output (enumerate environments, proper `\ref{}`, `$...$`)
- Nested enumerate/itemize for structured feedback
- Example proofread report format is provided
- Explicitly states what OTHER reviewers cover (avoiding overlap)
- "Take a deep breath" and "be thorough and precise" meta-instructions

## Source Code

The full Python implementation is installed at `tools/genai-latex-proofreader/`:
- `genai_latex_proofreader/cli.py` — CLI entry point
- `genai_latex_proofreader/genai_proofreader/runner.py` — orchestration
- `genai_latex_proofreader/genai_proofreader/proofreaders/domain_expert.py` — Domain Expert prompts
- `genai_latex_proofreader/genai_proofreader/proofreaders/language_expert.py` — Language Expert prompts
- `genai_latex_proofreader/genai_proofreader/latex_guard.py` — Auto-fix LaTeX errors in AI output
- `genai_latex_proofreader/genai_proofreader/formatting.py` — Report formatting with color-coded sections
- `genai_latex_proofreader/latex_interface/parser.py` — Section-aware LaTeX parser

Reference prompt files at `.claude/reference/genai-proofreader/` for direct use without running the tool.

## Integration

- **/paperdebugger** — structural/deterministic review (checklist-based). Use for quick quality gates.
- **/genai-proofreader** — persona-based full-text review (LLM-grounded). Use for deep section-by-section feedback.
- **/aris paper-write** — writing pipeline. Use genai-proofreader persona patterns for review gates.
- **/paperops** — build and compile. Use to compile the proofreading report.

Run both review types before submission: structural check (`/paperdebugger`) + persona review (`/genai-proofreader`).
