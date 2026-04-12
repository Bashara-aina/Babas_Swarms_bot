"""Humanizer — post-processing layer that makes Legion's responses feel natural.

Applied AFTER emotion postprocessing as the final layer.
Never changes meaning — only surface-level naturalness.
"""

from __future__ import annotations

import random
import re

_STIFF_PHRASES = [
    (r"In conclusion,?\s*", ""),
    (r"To summarize,?\s*", ""),
    (r"In summary,?\s*", ""),
    (r"Furthermore,?\s*", "Also, "),
    (r"Additionally,?\s*", "Also "),
    (r"It is (important|worth) (to note|noting) that\s*", ""),
    (r"This is (because|due to the fact that)\s*", "because "),
    (r"In order to\s*", "To "),
    (r"It should be noted that\s*", ""),
    (r"As (previously|mentioned) (mentioned|above),?\s*", ""),
    (r"Upon (careful)? consideration,?\s*", ""),
    (r"That being said,?\s*", ""),
    (r"With that in mind,?\s*", ""),
    (r"At the end of the day,?\s*", ""),
]


def humanize(response: str, emotion: str = "neutral") -> str:
    """Final pass to humanize response. Removes formal/stiff phrases."""
    for pattern, replacement in _STIFF_PHRASES:
        response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)

    response = re.sub(r"  +", " ", response)
    response = re.sub(r"\n{3,}", "\n\n", response)

    return response.strip()


def should_add_casual_opener(response: str, emotion: str, message_length: int) -> bool:
    """Decide whether to add a casual opener. Only for short-medium direct messages."""
    if "```" in response or response.startswith("#") or len(response) > 500:
        return False
    if message_length < 5:
        return False
    if emotion in ("tired", "frustrated"):
        return False
    return random.random() < 0.25


class Humanizer:
    """Wrapper class for humanization functions.

    Provides an object-oriented interface for post-processing
    LLM responses to remove stiff/formal phrasing.
    """

    def humanize(self, response: str, emotion: str = "neutral") -> str:
        """Humanize a response string.

        Args:
            response: The raw LLM response to humanize.
            emotion: Emotional context (currently unused but available for future expansion).

        Returns:
            The response with stiff phrases removed.
        """
        return humanize(response, emotion)

    def should_add_casual_opener(
        self,
        text: str,
        emotion: str = "neutral",
        message_length: int | None = None,
    ) -> bool:
        """Decide whether to prepend a casual opener.

        Args:
            text: The response text.
            emotion: Emotional state of the user/conversation.
            message_length: Length of the original message.
                          Defaults to len(text) if not provided.

        Returns:
            True if a casual opener should be added.
        """
        if message_length is None:
            message_length = len(text)
        return should_add_casual_opener(text, emotion, message_length)
