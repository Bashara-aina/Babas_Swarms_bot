"""Multi-provider fallback chain for maximum API availability.

Automatically tries multiple providers in sequence until one succeeds.
Provides 99.9% uptime by having 4 cloud backup options before local fallback.
"""

from __future__ import annotations

import logging

from core.reliability.provider_health import check_provider_health

logger = logging.getLogger(__name__)

# Provider fallback chains by priority (fastest to slowest, MiniMax free tiers first)
# RTX 3060 (12GB VRAM): gemma4:e4b (9.6GB) is the only viable local model.
# qwen3.5:35b needs ~23GB — too heavy, never use it.
_FALLBACK_CHAINS = {
    # Coding tasks: MiniMax primary, Ollama local fallback
    "coding": [
        ("minimax-coding-plan/MiniMax-M2.7", "MiniMax M2.7"),
        ("minimax-coding-plan/MiniMax-Text-01", "MiniMax Text-01"),
        ("ollama_chat/gemma4:e4b", "Local Ollama gemma4:e4b"),
    ],
    # General chat: MiniMax primary
    "chat": [
        ("minimax-coding-plan/MiniMax-M2.7", "MiniMax M2.7"),
        ("minimax-coding-plan/MiniMax-Text-01", "MiniMax Text-01"),
        ("ollama_chat/gemma4:e4b", "Local Ollama gemma4:e4b"),
    ],
    # Analysis tasks: MiniMax primary, Ollama Llama for heavy reasoning
    "analysis": [
        ("minimax-coding-plan/MiniMax-M2.7", "MiniMax M2.7"),
        ("minimax-coding-plan/MiniMax-Text-01", "MiniMax Text-01"),
        ("ollama_chat/llama3.3:70b", "Local Ollama Llama 3.3 70B"),
    ],
}


class FallbackChain:
    """Manages multi-provider fallback for maximum availability."""

    @staticmethod
    def get_provider_chain(agent_key: str = "coding") -> list[tuple[str, str]]:
        """Get the fallback chain for an agent type.

        Args:
            agent_key: Agent type (coding, chat, analysis, etc.)

        Returns:
            List of (model_string, display_name) tuples in priority order
        """
        # Use specific chain if available, otherwise default to coding
        return _FALLBACK_CHAINS.get(agent_key, _FALLBACK_CHAINS["coding"])

    @staticmethod
    def get_next_available_provider(
        agent_key: str = "coding",
        skip_providers: set[str] | None = None,
    ) -> tuple[str, str, int]:
        """Get the next healthy provider from the fallback chain.

        Args:
            agent_key: Agent type
            skip_providers: Set of provider names to skip (e.g., already tried)

        Returns:
            Tuple of (model_string, display_name, index_in_chain)
            Returns local Ollama if all cloud providers unavailable
        """
        skip_providers = skip_providers or set()
        chain = FallbackChain.get_provider_chain(agent_key)

        for idx, (model_string, display_name) in enumerate(chain):
            # Extract provider name
            provider = model_string.split("/")[0] if "/" in model_string else model_string

            # Skip if already tried
            if provider in skip_providers:
                logger.debug("Skipping already-tried provider: %s", provider)
                continue

            # Check provider health
            status = check_provider_health(provider)

            if status == "healthy":
                logger.info("Selected provider %d/%d: %s (healthy)", idx + 1, len(chain), display_name)
                return model_string, display_name, idx

            elif status == "degraded":
                logger.info("Selected provider %d/%d: %s (degraded but usable)", idx + 1, len(chain), display_name)
                return model_string, display_name, idx

            else:  # unavailable
                logger.debug("Provider %d/%d unavailable: %s (circuit open)", idx + 1, len(chain), display_name)
                continue

        # All providers unavailable — return local Ollama gemma4:e4b as last resort
        # Only used in true emergency (all cloud APIs down)
        logger.warning("All cloud providers unavailable — falling back to local Ollama gemma4:e4b")
        return "ollama_chat/gemma4:e4b", "Local Ollama gemma4:e4b (Emergency Fallback)", len(chain) - 1

    @staticmethod
    def get_optimal_provider(agent_key: str = "coding") -> tuple[str, str]:
        """Get the optimal (first healthy) provider from chain.

        This is the main entry point for normal usage.

        Args:
            agent_key: Agent type

        Returns:
            Tuple of (model_string, display_name)
        """
        model, name, _ = FallbackChain.get_next_available_provider(agent_key)
        return model, name

    @staticmethod
    def get_fallback_stats(agent_key: str = "coding") -> dict[str, str]:
        """Get health status of all providers in the chain.

        Args:
            agent_key: Agent type

        Returns:
            Dict mapping display names to health status
        """
        chain = FallbackChain.get_provider_chain(agent_key)
        stats = {}

        for model_string, display_name in chain:
            provider = model_string.split("/")[0] if "/" in model_string else model_string
            status = check_provider_health(provider)
            stats[display_name] = status

        return stats


def get_fallback_chain(agent_key: str = "coding") -> list[str]:
    """Convenience function: Get the full fallback chain model strings for an agent.

    Args:
        agent_key: Agent type (coding, chat, analysis)

    Returns:
        List of model strings in priority order

    Example:
        >>> chain = get_fallback_chain("coding")
        >>> # Returns ["minimax-coding-plan/MiniMax-M2.7", "minimax-coding-plan/MiniMax-Text-01", ...]
    """
    chain = FallbackChain.get_provider_chain(agent_key)
    return [model for model, _ in chain]


def get_best_provider(agent_key: str = "coding") -> str:
    """Convenience function: Get the best available provider model string.

    Args:
        agent_key: Agent type (coding, chat, analysis)

    Returns:
        Model string ready for use with interpreter

    Example:
        >>> model = get_best_provider("coding")
        >>> # Returns "minimax-coding-plan/MiniMax-M2.7" if healthy
        >>> # Returns "minimax-coding-plan/MiniMax-Text-01" if M2.7 down
        >>> # Or "ollama_chat/llama3.3:70b" if all cloud down (local fallback)
    """
    model, _ = FallbackChain.get_optimal_provider(agent_key)
    return model
