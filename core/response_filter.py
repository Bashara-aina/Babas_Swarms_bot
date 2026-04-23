"""Optional post-process: tighten overly long or padded model replies."""

from __future__ import annotations

import os


async def maybe_tighten_response(text: str, task: str, agent_key: str) -> str:
    if not text or len(text) < int(os.getenv("LEGION_RESPONSE_FILTER_MIN_CHARS", "6000")):
        return text

    from llm_client import wiki_raw_completion

    model = os.getenv("LEGION_RESPONSE_FILTER_MODEL", "minimax/MiniMax-Text-01")
    tightened = await wiki_raw_completion(
        f"""User task (for context only, do not repeat verbatim):
{task[:1200]}

Assistant draft (compress without losing facts/steps/code):
{text[:14000]}

Rewrite: same substance, tighter, no filler, no apology meta. Preserve code blocks.""",
        model=model,
        max_tokens=min(4096, len(text) // 2 + 500),
    )
    out = (tightened or "").strip()
    return out if len(out) > 200 else text
