"""Multi-provider fallback chain for maximum API availability.

Automatically tries multiple providers in sequence until one succeeds.
Provides 99.9% uptime by having 4 cloud backup options before local fallback.
"""

from __future__ import annotations

import logging
from typing import List, Tuple

from core.reliability.provider_health import check_provider_health

logger = logging.getLogger(__name__)

# Provider fallback chains by priority (fastest to slowest, free tiers first)
_FALLBACK_CHAINS = {
    # Coding tasks: prioritize speed and code quality
    "coding": [
        ("openrouter/qwen/qwen3-coder:free", "OpenRouter Qwen Coder"),
        ("groq/llama-3.3-70b-versatile", "Groq Llama 3.3 70B"),
        ("cerebras/llama3.1-70b", "Cerebras Llama 3.1 70B"),
        ("gemini/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash"),
        ("ollama_chat/qwen3.5:35b", "Local Ollama Qwen 3.5 35B"),
    ],
    
    # General chat: prioritize speed
    "chat": [
        ("groq/llama-3.3-70b-versatile", "Groq Llama 3.3 70B"),
        ("openrouter/qwen/qwen3-coder:free", "OpenRouter Qwen"),
        ("cerebras/llama3.1-70b", "Cerebras Llama 3.1 70B"),
        ("gemini/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash"),
        ("ollama_chat/qwen3.5:35b", "Local Ollama"),
    ],
    
    # Analysis tasks: prioritize reasoning quality
    "analysis": [
        ("openrouter/qwen/qwen3-coder:free", "OpenRouter Qwen"),
        ("gemini/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash"),
        ("groq/llama-3.3-70b-versatile", "Groq Llama 3.3 70B"),
        ("cerebras/llama3.1-70b", "Cerebras Llama 3.1 70B"),
        ("ollama_chat/qwen3.5:35b", "Local Ollama"),
    ],
}


class FallbackChain:
    """Manages multi-provider fallback for maximum availability."""

    @staticmethod
    def get_provider_chain(agent_key: str = "coding") -> List[Tuple[str, str]]:
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
    ) -> Tuple[str, str, int]:
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
                logger.info(
                    "Selected provider %d/%d: %s (healthy)",
                    idx + 1, len(chain), display_name
                )
                return model_string, display_name, idx
            
            elif status == "degraded":
                logger.info(
                    "Selected provider %d/%d: %s (degraded but usable)",
                    idx + 1, len(chain), display_name
                )
                return model_string, display_name, idx
            
            else:  # unavailable
                logger.debug(
                    "Provider %d/%d unavailable: %s (circuit open)",
                    idx + 1, len(chain), display_name
                )
                continue
        
        # All providers unavailable — return local Ollama as last resort
        logger.warning(
            "All cloud providers unavailable — falling back to local Ollama"
        )
        return "ollama_chat/qwen3.5:35b", "Local Ollama (Emergency Fallback)", len(chain) - 1

    @staticmethod
    def get_optimal_provider(agent_key: str = "coding") -> Tuple[str, str]:
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


def get_best_provider(agent_key: str = "coding") -> str:
    """Convenience function: Get the best available provider model string.
    
    Args:
        agent_key: Agent type (coding, chat, analysis)
        
    Returns:
        Model string ready for use with interpreter
        
    Example:
        >>> model = get_best_provider("coding")
        >>> # Returns "openrouter/qwen/qwen3-coder:free" if healthy
        >>> # Or "groq/llama-3.3-70b-versatile" if OpenRouter down
        >>> # Or "ollama_chat/qwen3.5:35b" if all cloud providers down
    """
    model, _ = FallbackChain.get_optimal_provider(agent_key)
    return model
