# GenAI LaTeX Proofreader — Multi-Persona Paper Proofreading

## Overview

**GenAI LaTeX Proofreader** uses generative AI (Anthropic Claude) to proofread scientific papers written in LaTeX. It generates a proofreading report with feedback from multiple personas (Domain Expert, Language Expert) appended to each section of the paper.

**Upstream:** https://github.com/genai-latex-proofreader/genai-latex-proofreader (active dev moved to https://github.com/genai-latex-proofreader/latexq)  
**License:** MIT  
**Author:** Matias Dahl

## Architecture

The proofreader works as a pipeline:

1. **Parse** — Section-aware LaTeX parser extracts sections, subsections, appendix, bibliography from the document
2. **Compile check** — Confirms the input document compiles with pdflatex before proofreading
3. **Proofread** — For each section, runs both persona prompts via the Anthropic API
4. **LaTeX Guard** — Tests whether the generated feedback compiles; auto-fixes if not (up to 3 retries via LLM)
5. **Insert comments** — Appends formatted, color-coded feedback blocks before each section
6. **Compile report** — Compiles the final report PDF with all feedback inserted

## Installation in this project

**Source code:** `tools/genai-latex-proofreader/genai_latex_proofreader/`  
**Wrapper:** `tools/genai-latex-proofreader/bin/genai-proofreader`  
**Prompt references:** `.claude/reference/genai-proofreader/`  
**Skill:** `/genai-proofreader`

### To run the full pipeline:

```bash
cd tools/genai-latex-proofreader
pip install -r requirements.txt
export ANTHROPIC_API_KEY='your-key'
python3 -m genai_latex_proofreader.cli \
  --input_latex_path /path/to/paper/main.tex \
  --output_report_filepath output/report.tex
```

## Persona Prompts

### Domain Expert (`domain_expert_prompts.py`)

**System prompt** establishes:
- Distinguished expert in specific domains (configured per paper)
- Meticulous attention to detail
- Insightful suggestions for content, structure, and clarity
- Commitment to helping authors meet top journal standards

**Instructions prompt** focuses on:
- Motivation, correctness, clarity, consistency, completeness, references
- Summary of strengths, weaknesses, future research directions
- **Must not** cover formatting, LaTeX usage, typos, grammar (those are for Language Expert)
- Output format: `\begin{enumerate}`...`\end{enumerate}` with nested enumerate/itemize
- Must produce valid LaTeX

**Two calls per section:**
1. Proofread the section content
2. Check title/abstract/intro match the rest of the paper (once, before first section)

### Language Expert (`language_expert_prompts.py`)

**System prompt** establishes:
- 20+ years as elite editor/proofreader across all academic fields
- Linguistic precision: grammar, spelling, punctuation, dialects
- Style guide mastery: APA, MLA, Chicago, IEEE
- Technical proficiency: LaTeX typesetting
- Ethical editing: preserving author voice

**Instructions prompt** focuses on:
- Grammar, spelling, formatting, punctuation, consistency, clarity, flow
- **Must not** review scientific content or LaTeX usage
- Specific, actionable suggestions with exact locations (`\ref{sec:foo}`)
- Output format: enumerated list with bolded key parts, bracketed additions
- Target: 15-20 key points per section

## LaTeX Guard

The LaTeX Guard (`latex_guard.py`) is a critical innovation:
- After each AI-generated feedback block, it attempts to compile the full document
- If the AI introduced LaTeX errors, it extracts error messages and sends them back to the LLM for fixing
- Retries up to 3 times per block
- Falls back gracefully with an error message if unable to fix

### Guard prompt pattern:
- "You are an expert in LaTeX typesetting"
- Receives the failing snippet and error messages
- Rules: modify as little as possible, only fix errors, fill dummy values for missing args, handle unmatched braces/environments
- Must not preface with explanations, only return corrected LaTeX

## Key Patterns for LLM-Aware LaTeX Editing

These patterns from the codebase are reusable for any AI-assisted LaTeX workflow:

1. **Section-aware parsing** — Extract sections for independent processing while preserving full-document context
2. **Compile verification** — Always verify LaTeX before AND after AI modification
3. **Error isolation** — Use `\typeout{RUN_ID}` markers to isolate which AI output caused errors
4. **Split at lambda** — Utility to split LaTeX at section boundaries without regex fragility
5. **Format as compile-safe** — All AI output wrapped in color environments, `\typeout` start/end markers, horizontal rules
6. **Persona deconfliction** — Explicitly tell each persona what OTHER reviewers handle (avoids redundant feedback)

## Comparison with Other Paper Tools

| Aspect | genai-proofreader | paperdebugger | ARIS review |
|--------|------------------|---------------|-------------|
| Review type | Full-text persona | Structural/checklist | Adversarial cross-model |
| LaTeX-aware | Yes (parser, guard, compile) | Basic regex | Section parsing |
| Personas | Domain Expert, Language Expert | Single reviewer | Multi-model pairs |
| Output | Color-coded inline comments | JSON issues list | Full reports |
| API needed | Anthropic | No | Optional (multi-model) |
| Auto-fix LaTeX | Yes (LaTeX Guard) | No | No |
