"""Legion Anti-Slop Defense System.

A 4-guard quality pipeline that filters LLM responses before they reach users.
Guards: FormatGuard (filler), PackageGuard (toxicity), CritiqueGuard (repetition), ConfidenceGuard (grounding).

Architecture follows the proven wiki_quality_gate.py pattern:
  - Guards 1-3: heuristic checks (<5ms, no I/O)
  - Guard 4: LLM-powered grounding (async, only for NEEDS_IMPROVEMENT cases)
"""

from __future__ import annotations
