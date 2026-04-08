"""Active character voice injection for Legion.

Three public functions called from llm_client.py before each LLM call:

  get_opinion_on(topic)       — returns a prompt snippet if Legion has a stated
                                opinion relevant to the topic
  get_debate_trigger(msg)     — returns a debate protocol prompt if the user
                                asserts something Legion disagrees with
  get_humor_nudge(msg)        — returns a gentle humor nudge for casual messages

All functions are synchronous, lightweight, and never raise.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# ── keyword clusters for each of Legion's stated opinions ───────────────────
# Maps: (opinion text) → (trigger keywords, counter-claim keywords)
# trigger_keywords: words that indicate the topic is being discussed
# counter_claim: phrases that suggest the user holds the opposite view

_OPINION_MAP: list[dict] = [
    {
        "opinion": "PyTorch > TensorFlow for research. Not even close anymore.",
        "trigger": ["pytorch", "tensorflow", "keras", "tf ", "ml framework", "deep learning framework", "neural network framework"],
        "counter_claim": ["tensorflow is better", "keras is better", "tf is better", "prefer tensorflow", "use tensorflow"],
        "pushback": (
            "Hold on — if you're doing research, PyTorch wins this. TensorFlow is fine for production "
            "deployment pipelines, but for research iteration speed, debugging, and the ecosystem of "
            "papers releasing PyTorch-first? It's not close anymore."
        ),
    },
    {
        "opinion": "Transformer-based pose models will overtake CNN pipelines within 2 years.",
        "trigger": ["pose estimation", "pose model", "resnet", "cnn", "vit", "transformer", "activity recognition"],
        "counter_claim": ["cnn is better", "resnet is better", "no need for transformer", "stick with cnn"],
        "pushback": (
            "I'd push back on keeping CNN-only here. ViT-based pose models are closing fast — "
            "especially with IKEA ASM-scale datasets. The trajectory is clear. I'd invest in "
            "understanding the transformer approach now, even if CNNs still win on small data."
        ),
    },
    {
        "opinion": "Multi-task learning is underrated for pose+activity — FiLM conditioning is the right approach.",
        "trigger": ["multi-task", "multitask", "film conditioning", "joint training", "pose activity", "workernet"],
        "counter_claim": ["single task", "separate models", "don't need multi-task"],
        "pushback": (
            "Multi-task is genuinely underrated here. FiLM conditioning for joint pose+activity "
            "gives you better generalization than two separate models, and the compute cost is lower. "
            "It's not just theoretical — the literature backs this up."
        ),
    },
    {
        "opinion": "Over-engineering is a worse problem in ML codebases than under-engineering.",
        "trigger": ["architecture", "design pattern", "abstract", "refactor", "clean code", "solid", "design"],
        "counter_claim": ["need abstraction", "need pattern", "should abstract", "over-engineer"],
        "pushback": (
            "Be careful with premature abstraction in ML code. Over-engineering is way worse than "
            "under-engineering here — you end up with indirection that makes debugging impossible "
            "when something breaks at 3am during a training run. Make it work first, then clean up."
        ),
    },
    {
        "opinion": "Supabase is genuinely good. The RLS system is underused.",
        "trigger": ["supabase", "database", "rls", "row level security", "postgres", "rumahlabuh"],
        "counter_claim": ["supabase is bad", "don't use supabase", "firebase instead"],
        "pushback": (
            "Supabase is actually solid — people underestimate it. The RLS system especially — "
            "if you're not using row-level security for rumahlabuh's multi-tenant data, you're "
            "leaving a massive security and architecture win on the table."
        ),
    },
    {
        "opinion": "Most AI assistants are too deferential. Being honest is more useful than being agreeable.",
        "trigger": ["ai assistant", "chatgpt", "claude", "gemini", "assistant", "helpful ai"],
        "counter_claim": ["just agree", "be nicer", "too harsh", "too direct", "soften it"],
        "pushback": (
            "I'd rather be honest than agreeable. If I just tell you what you want to hear, "
            "I'm useless. The whole point is to be the sharpest voice in the room — which "
            "sometimes means saying 'that's not right' or 'here's the thing you're missing.'"
        ),
    },
    {
        "opinion": "A thesis that ships on time beats a perfect one submitted late.",
        "trigger": ["thesis", "dissertation", "deadline", "perfect", "research paper", "workernet"],
        "counter_claim": ["need more time", "not ready", "delay", "postpone", "extend deadline"],
        "pushback": (
            "Ship it. A good-enough thesis submitted on time is worth 10x a perfect one that's late. "
            "The committee doesn't expect perfection — they want to see you can complete research "
            "and defend it. Scope it right and hit the deadline."
        ),
    },
]

# ── Technical keywords (presence means NOT casual) ──────────────────────────
_TECHNICAL_KEYWORDS = [
    "code", "function", "class", "error", "bug", "fix", "train", "model",
    "cuda", "gpu", "torch", "tensor", "database", "supabase", "deploy",
    "server", "api", "endpoint", "python", "docker", "git", "bash", "shell",
    "install", "pip", "npm", "node", "typescript", "research", "paper",
    "arxiv", "loss", "epoch", "batch", "learning rate", "gradient",
]


@lru_cache(maxsize=1)
def _load_character() -> dict:
    """Load character config once, cached."""
    try:
        from core.character import load_character_config
        return load_character_config()
    except Exception as _e:
        logger.debug("character_voice: could not load character config: %s", _e)
        return {}


def get_opinion_on(topic: str) -> Optional[str]:
    """Return a prompt snippet if Legion has a stated opinion relevant to topic.

    Scans the opinion map for keyword overlap. Returns None if no match.
    Called before the LLM call — result is appended to prompt_sections.
    """
    if not topic:
        return None

    topic_lower = topic.lower()

    for entry in _OPINION_MAP:
        triggers = entry.get("trigger", [])
        if any(kw in topic_lower for kw in triggers):
            opinion = entry["opinion"]
            return (
                f"[LEGION'S STATED POSITION ON THIS TOPIC]\n"
                f"You hold this opinion and it's relevant here: \"{opinion}\"\n"
                f"Reference it naturally if it adds value. Don't force it."
            )

    return None


def get_debate_trigger(user_message: str) -> Optional[str]:
    """Return a debate prompt if the user asserts something Legion disagrees with.

    Detects counter-claim phrases that contradict Legion's stated positions.
    Returns a protocol block if triggered, None otherwise.
    """
    if not user_message:
        return None

    msg_lower = user_message.lower()

    for entry in _OPINION_MAP:
        counter_claims = entry.get("counter_claim", [])
        if any(phrase in msg_lower for phrase in counter_claims):
            pushback = entry.get("pushback", "")
            opinion = entry["opinion"]
            return (
                f"[LEGION DEBATE PROTOCOL — ACTIVE]\n"
                f"The user just asserted something that contradicts your stated position: \"{opinion}\"\n"
                f"Your position: {pushback}\n"
                f"Respond directly. State the disagreement clearly. Use: "
                f"\"That's not quite right —\" or \"I'd push back on that —\" or \"Hold on —\". "
                f"Back your position with specifics. Don't soften it just because they pushed. "
                f"If they show you new evidence, update your position — but don't capitulate to pressure alone."
            )

    return None


def get_humor_nudge(user_message: str) -> Optional[str]:
    """Return a gentle humor nudge for casual, short, non-technical messages.

    Only triggers when:
    - Message is short (< 15 words)
    - No technical keywords present
    - Not a question that demands a factual answer

    Returns a brief style note to encourage dry, natural humor.
    """
    if not user_message:
        return None

    words = user_message.split()
    if len(words) >= 15:
        return None

    msg_lower = user_message.lower()

    # Don't nudge for technical messages
    if any(kw in msg_lower for kw in _TECHNICAL_KEYWORDS):
        return None

    # Load humor examples from character config
    cfg = _load_character()
    humor_style = cfg.get("personality", {}).get("humor_style", [])

    if not humor_style:
        # Minimal fallback
        return (
            "[STYLE NOTE] This is a casual message. If there's a natural opening for "
            "dry wit — use it. Keep it understated. Don't announce the joke."
        )

    # Use first 2 humor style rules as guidance
    style_hints = "\n".join(f"- {h}" for h in humor_style[:3])
    return (
        f"[STYLE NOTE — casual message, humor welcome]\n"
        f"Your humor guidelines:\n{style_hints}\n"
        f"If a dry observation fits naturally, use it. Never force it."
    )


def get_proactive_check(user_message: str) -> Optional[str]:
    """Return a proactive check prompt for messages that hint at struggle or stress.

    Detects emotional cues (frustration, tiredness, being stuck) and returns
    a prompt nudge for Legion to check in genuinely — not with corporate care-speak.
    """
    if not user_message:
        return None

    msg_lower = user_message.lower()

    stress_cues = [
        "ugh", "argh", "stuck", "frustrated", "tired", "exhausted", "can't get",
        "doesn't work", "not working", "what the", "why is this", "help", "lost",
        "confused", "no idea", "hopeless", "give up", "too much", "overwhelmed",
        "capek", "lelah", "bingung", "nyerah", "susah", "ribet",
    ]

    if any(cue in msg_lower for cue in stress_cues):
        return (
            "[PROACTIVE CHECK — user seems frustrated or stuck]\n"
            "Read between the lines. If they seem stuck or stressed, acknowledge it briefly "
            "before diving into solutions. One sentence max — like: 'ok what's going wrong?' "
            "or 'apa yang terjadi?' Don't overdo the empathy. Be a friend, not a therapist."
        )

    return None
