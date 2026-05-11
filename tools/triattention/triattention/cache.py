"""
KV Cache with TriAttention pruning.

This module provides a KV cache implementation that uses TriAttention
for intelligent KV eviction during long-context inference.
"""

import torch
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from collections import deque


@dataclass
class CacheEntry:
    """A single entry in the KV cache.

    Attributes:
        key: Key tensor [head_dim] or [num_kv_heads, head_dim] for GQA
        value: Value tensor [head_dim]
        position: Position in sequence
        layer: Layer index
    """
    key: torch.Tensor
    value: torch.Tensor
    position: int
    layer: int


class TriAttentionCache:
    """
    KV Cache with TriAttention-based eviction.

    This cache uses TriAttention scoring to decide which KV pairs to retain
    during long-context inference.

    Features:
    - Automatic pruning when budget is exceeded
    - GQA support (multiple query heads share KV heads)
    - Window-based pruning (prune every N tokens)
    - Position tracking for distance-based scoring

    Example:
        >>> cache = TriAttentionCache(
        ...     num_kv_heads=8,
        ...     head_dim=128,
        ...     kv_budget=2048,
        ...     device="cuda"
        ... )
        >>> # Add keys/values
        >>> cache.update(keys, values, positions, layer=0)
        >>> # Trigger pruning when needed
        >>> cache.prune_if_needed(triattention, calibration)
        >>> # Get current cache state
        >>> keys, values = cache.get()
    """

    def __init__(
        self,
        num_kv_heads: int,
        head_dim: int,
        kv_budget: int = 2048,
        window_size: int = 128,
        device: str = "cuda",
        dtype: torch.dtype = torch.bfloat16,
    ):
        """
        Initialize the TriAttention cache.

        Args:
            num_kv_heads: Number of KV heads (for GQA)
            head_dim: Dimension per head
            kv_budget: Maximum number of KV pairs to retain
            window_size: Prune every this many tokens
            device: Device for tensors
            dtype: Data type for tensors
        """
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        self.kv_budget = kv_budget
        self.window_size = window_size
        self.device = torch.device(device)
        self.dtype = dtype

        # Cache storage
        self.keys: List[torch.Tensor] = []
        self.values: List[torch.Tensor] = []
        self.positions: List[int] = []
        self.layers: List[int] = []

        # Tracking
        self.current_position = 0
        self.tokens_since_prune = 0

        # Statistics
        self.num_prunes = 0
        self.total_evicted = 0

    def update(
        self,
        keys: torch.Tensor,
        values: torch.Tensor,
        positions: torch.Tensor,
        layer: int = 0,
        triattention=None,
        calibration=None,
    ) -> None:
        """
        Add new keys and values to the cache.

        Args:
            keys: Key tensors [batch, num_kv_heads, head_dim] or [batch, head_dim]
            values: Value tensors [batch, num_kv_heads, head_dim] or [batch, head_dim]
            positions: Positions in sequence [batch]
            layer: Layer index
            triattention: Optional TriAttention instance for auto-pruning
            calibration: Optional CalibrationData for scoring
        """
        # Handle single head case
        if keys.dim() == 2:
            keys = keys.unsqueeze(1)
            values = values.unsqueeze(1)

        batch_size = keys.shape[0]

        for i in range(batch_size):
            self.keys.append(keys[i].to(self.device))
            self.values.append(values[i].to(self.device))
            self.positions.append(positions[i].item())
            self.layers.append(layer)

        self.current_position = positions[-1].item() + 1
        self.tokens_since_prune += batch_size

        # Auto-trigger pruning if conditions are met
        if triattention is not None and calibration is not None:
            if self.should_prune():
                self._auto_prune(triattention, calibration)

    def get(self) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Get current cache contents.

        Returns:
            Tuple of (keys, values, positions)
        """
        if not self.keys:
            return (
                torch.empty(0, self.num_kv_heads, self.head_dim, device=self.device, dtype=self.dtype),
                torch.empty(0, self.num_kv_heads, self.head_dim, device=self.device, dtype=self.dtype),
                torch.tensor([], device=self.device, dtype=torch.long),
            )

        keys = torch.stack(self.keys)
        values = torch.stack(self.values)
        positions = torch.tensor(self.positions, device=self.device, dtype=torch.long)

        return keys, values, positions

    def get_by_indices(self, indices: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get cache entries by indices.

        Args:
            indices: Indices to retrieve [num_indices]

        Returns:
            Tuple of (keys[indices], values[indices])
        """
        keys = torch.stack([self.keys[i] for i in indices])
        values = torch.stack([self.values[i] for i in indices])
        return keys, values

    def prune(
        self,
        indices: torch.Tensor,
    ) -> None:
        """
        Prune cache to keep only specified indices.

        Args:
            indices: Indices to keep
        """
        indices = indices.tolist() if indices.is_cuda else indices.tolist()

        self.keys = [self.keys[i] for i in indices]
        self.values = [self.values[i] for i in indices]
        self.positions = [self.positions[i] for i in indices]
        self.layers = [self.layers[i] for i in indices]

        self.total_evicted += len(indices)

    def prune_if_needed(
        self,
        scores: torch.Tensor,
    ) -> bool:
        """
        Prune cache if size exceeds budget.

        Args:
            scores: Importance scores for each cache entry [num_entries]

        Returns:
            True if pruning was performed, False otherwise
        """
        current_size = len(self.keys)

        if current_size <= self.kv_budget:
            return False

        # Get top-B indices
        _, top_indices = torch.topk(scores, self.kv_budget)

        self.prune(top_indices)
        self.num_prunes += 1
        self.tokens_since_prune = 0

        return True

    def should_prune(self) -> bool:
        """
        Check if pruning should be triggered.

        Returns:
            True if window is full and cache exceeds budget
        """
        return (
            self.tokens_since_prune >= self.window_size
            and len(self.keys) > self.kv_budget
        )

    def _auto_prune(
        self,
        triattention,
        calibration,
    ) -> None:
        """
        Automatically prune the cache using TriAttention scoring.

        Called automatically when should_prune() returns True.

        Args:
            triattention: TriAttention instance for scoring
            calibration: CalibrationData for scoring
        """
        if len(self.keys) <= self.kv_budget:
            return

        # Get key positions for scoring
        key_positions = torch.tensor(self.positions, dtype=torch.long, device=self.device)

        # Score keys using position-aware scoring
        if hasattr(triattention, 'score_keys_position_aware'):
            scores = triattention.score_keys_position_aware(
                key_positions,
                calibration=calibration,
                num_current_tokens=self.current_position,
            )
        else:
            scores = triattention.score_keys(
                key_positions,
                calibration=calibration,
            )

        # Prune to budget
        self.prune_if_needed(scores)

    def reset(self) -> None:
        """Reset the cache."""
        self.keys = []
        self.values = []
        self.positions = []
        self.layers = []
        self.current_position = 0
        self.tokens_since_prune = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "current_size": len(self.keys),
            "kv_budget": self.kv_budget,
            "num_prunes": self.num_prunes,
            "total_evicted": self.total_evicted,
            "tokens_since_prune": self.tokens_since_prune,
            "current_position": self.current_position,
        }


class StreamingCache(TriAttentionCache):
    """
    Streaming variant of TriAttention cache.

    Optimized for infinite-length streaming scenarios with
    attention sinks.
    """

    def __init__(
        self,
        num_kv_heads: int,
        head_dim: int,
        kv_budget: int = 2048,
        sink_size: int = 4,
        window_size: int = 128,
        device: str = "cuda",
        dtype: torch.dtype = torch.bfloat16,
    ):
        """
        Initialize streaming cache.

        Args:
            num_kv_heads: Number of KV heads
            head_dim: Dimension per head
            kv_budget: Maximum KV pairs to retain
            sink_size: Number of initial tokens to always keep as sinks
            window_size: Prune every this many tokens
            device: Device for tensors
            dtype: Data type
        """
        super().__init__(
            num_kv_heads=num_kv_heads,
            head_dim=head_dim,
            kv_budget=kv_budget,
            window_size=window_size,
            device=device,
            dtype=dtype,
        )
        self.sink_size = sink_size

    def _get_sink_indices(self) -> List[int]:
        """Get indices of sink tokens (first N tokens)."""
        if not self.positions:
            return []
        # Sort by position and take first sink_size
        sorted_indices = sorted(range(len(self.positions)), key=lambda i: self.positions[i])
        return sorted_indices[:self.sink_size]

    def prune(
        self,
        indices: torch.Tensor,
    ) -> None:
        """
        Prune cache but always keep sink tokens.

        Args:
            indices: Indices to keep
        """
        indices = indices.tolist() if indices.is_cuda else indices.tolist()
        sink_indices = set(self._get_sink_indices())

        # Ensure sink indices are included
        protected_indices = list(sink_indices)
        for idx in indices:
            if idx not in sink_indices:
                protected_indices.append(idx)

        # Remove duplicates while preserving order
        seen = set()
        unique_indices = []
        for idx in protected_indices:
            if idx not in seen:
                seen.add(idx)
                unique_indices.append(idx)

        # Apply pruning
        self.keys = [self.keys[i] for i in unique_indices]
        self.values = [self.values[i] for i in unique_indices]
        self.positions = [self.positions[i] for i in unique_indices]
        self.layers = [self.layers[i] for i in unique_indices]

        self.total_evicted += len(unique_indices)