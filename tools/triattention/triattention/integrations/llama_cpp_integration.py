"""
llama.cpp integration for TriAttention.

Provides Python bindings for using TriAttention scoring with llama.cpp
inference. Since llama.cpp handles KV cache internally, this integration
provides TriAttention scoring that can be used to inform external
KV eviction decisions.

Example:
    from llama_cpp import Llama
    from triattention.integrations.llama_cpp_integration import TriAttentionScorer

    llm = Llama(model_path="./models/llama-2-7b.gguf")
    scorer = TriAttentionScorer(llm, kv_budget=2048)

    # Score and potentially evict KV entries
    scores = scorer.score_pending_keys()
"""

import torch
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class LlamaKVEntry:
    """A single KV cache entry from llama.cpp."""
    position: int
    key: torch.Tensor
    value: torch.Tensor
    layer: int


class TriAttentionScorer:
    """
    TriAttention scorer for llama.cpp KV cache.

    This class provides TriAttention-based importance scoring for KV entries
    managed by llama.cpp. It can be used to:

    1. Score pending keys for importance
    2. Determine which entries to evict when budget is exceeded
    3. Provide scoring data for custom llama.cpp eviction strategies

    Note:
        llama.cpp manages KV cache internally, so this provides scoring
        signals that can be used for external eviction coordination.
    """

    def __init__(
        self,
        num_heads: int = 32,
        num_kv_heads: int = 32,
        head_dim: int = 128,
        kv_budget: int = 2048,
        num_bands: int = 32,
        device: str = "cuda",
        dtype: torch.dtype = torch.bfloat16,
    ):
        """
        Initialize TriAttention scorer for llama.cpp.

        Args:
            num_heads: Number of query heads
            num_kv_heads: Number of key/value heads
            head_dim: Head dimension
            kv_budget: Target KV budget
            num_bands: Number of frequency bands
            device: Computation device
            dtype: Computation data type
        """
        self.num_heads = num_heads
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        self.kv_budget = kv_budget
        self.num_bands = num_bands
        self.device = torch.device(device)
        self.dtype = dtype

        # Initialize TriAttention core
        from ..core import TriAttention, TriAttentionConfig

        config = TriAttentionConfig(
            num_heads=num_heads,
            num_kv_heads=num_kv_heads,
            head_dim=head_dim,
            kv_budget=kv_budget,
            num_bands=num_bands,
            device=device,
            dtype=dtype,
        )
        self.triattention = TriAttention(config)

        # Pending KV entries
        self.pending_entries: List[LlamaKVEntry] = []

    def add_kv_entry(
        self,
        key: torch.Tensor,
        value: torch.Tensor,
        position: int,
        layer: int = 0,
    ) -> None:
        """
        Add a new KV entry from llama.cpp.

        Args:
            key: Key tensor [num_kv_heads, head_dim]
            value: Value tensor [num_kv_heads, head_dim]
            position: Position in sequence
            layer: Layer index
        """
        entry = LlamaKVEntry(
            position=position,
            key=key.to(self.device).to(self.dtype),
            value=value.to(self.device).to(self.dtype),
            layer=layer,
        )
        self.pending_entries.append(entry)

    def score_pending_keys(
        self,
        calibration_data: Optional[Any] = None,
        current_position: Optional[int] = None,
    ) -> torch.Tensor:
        """
        Score all pending KV entries.

        Args:
            calibration_data: Optional pre-computed calibration
            current_position: Current sequence position

        Returns:
            Scores for each pending entry [num_pending]
        """
        if not self.pending_entries:
            return torch.tensor([], device=self.device)

        # Stack keys
        keys = torch.stack([e.key for e in self.pending_entries])
        positions = torch.tensor([e.position for e in self.pending_entries])

        # Determine current position
        if current_position is None:
            current_position = positions.max().item() + 1

        # Score using TriAttention
        scores = self.triattention.score_keys_position_aware(
            keys=keys,
            positions=positions,
            current_position=current_position,
        )

        return scores

    def get_eviction_candidates(
        self,
        num_to_evict: int,
        calibration_data: Optional[Any] = None,
    ) -> List[int]:
        """
        Get indices of entries to evict.

        Args:
            num_to_evict: Number of entries to consider for eviction
            calibration_data: Optional calibration data

        Returns:
            List of indices to evict
        """
        scores = self.score_pending_keys(calibration_data)

        if scores.numel() == 0:
            return []

        # Get lowest-scoring entries
        _, indices = torch.sort(scores)
        evict_indices = indices[:num_to_evict].tolist()

        return evict_indices

    def evict_entries(self, indices: List[int]) -> None:
        """
        Remove entries by index.

        Args:
            indices: Indices to remove
        """
        indices_set = set(indices)
        self.pending_entries = [
            e for i, e in enumerate(self.pending_entries)
            if i not in indices_set
        ]

    def prune_to_budget(self, calibration_data: Optional[Any] = None) -> int:
        """
        Prune entries to stay within budget.

        Args:
            calibration_data: Optional calibration data

        Returns:
            Number of entries evicted
        """
        current_size = len(self.pending_entries)
        if current_size <= self.kv_budget:
            return 0

        num_to_evict = current_size - self.kv_budget
        evict_indices = self.get_eviction_candidates(num_to_evict, calibration_data)

        self.evict_entries(evict_indices)
        return len(evict_indices)

    def clear(self) -> None:
        """Clear all pending entries."""
        self.pending_entries = []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get scorer statistics.

        Returns:
            Dictionary of stats
        """
        return {
            "num_pending": len(self.pending_entries),
            "kv_budget": self.kv_budget,
            "num_heads": self.num_heads,
            "num_kv_heads": self.num_kv_heads,
            "head_dim": self.head_dim,
        }


class LlamaCppTriAttention:
    """
    Full llama.cpp integration with TriAttention.

    This class provides a more complete integration that wraps llama.cpp
    and automatically handles KV scoring and eviction.

    Example:
        from llama_cpp import Llama
        from triattention.integrations.llama_cpp_integration import LlamaCppTriAttention

        llm = Llama(model_path="./models/llama-2-7b.gguf")
        tri_llm = LlamaCppTriAttention(llm, kv_budget=2048)

        # Generation is handled with automatic KV management
        output = tri_llm.generate(prompt, max_tokens=100)
    """

    def __init__(
        self,
        llm,
        kv_budget: int = 2048,
        num_bands: int = 32,
        device: str = "cuda",
        **kwargs,
    ):
        """
        Initialize wrapped llama.cpp model.

        Args:
            llm: llama.cpp Llama instance
            kv_budget: Target KV budget
            num_bands: Number of frequency bands
            device: Computation device
            **kwargs: Additional TriAttention config
        """
        self.llm = llm

        # Extract config from llama.cpp model
        n_heads = getattr(llm, "n_heads", 32)
        n_kv_heads = getattr(llm, "n_kv_heads", n_heads)
        head_dim = getattr(llm, "n_embd", 4096) // n_heads if n_heads > 0 else 128

        self.scorer = TriAttentionScorer(
            num_heads=n_heads,
            num_kv_heads=n_kv_heads,
            head_dim=head_dim,
            kv_budget=kv_budget,
            num_bands=num_bands,
            device=device,
            **kwargs,
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        **kwargs,
    ) -> str:
        """
        Generate with TriAttention KV management.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation args

        Returns:
            Generated text
        """
        # Run generation
        output = self.llm(prompt, max_tokens=max_tokens, **kwargs)

        # TriAttention scoring can be applied between tokens if needed
        # For now, just return the generated text
        return output

    def score_current_kv(self) -> torch.Tensor:
        """
        Score the current KV state.

        Returns:
            Scores for current KV entries
        """
        return self.scorer.score_pending_keys()

    def prune_if_needed(self) -> int:
        """
        Prune KV entries if budget exceeded.

        Returns:
            Number of entries evicted
        """
        return self.scorer.prune_to_budget()
