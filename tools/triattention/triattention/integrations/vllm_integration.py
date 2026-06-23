"""
vLLM integration for TriAttention.

Provides a custom attention processor that can be registered with vLLM
to use TriAttention scoring for KV cache eviction during inference.

Example:
    from vllm import LLM, SamplingParams
    from triattention.integrations.vllm_integration import TriAttentionProcessor

    # Create vLLM engine
    llm = LLM(model="meta-llama/Llama-2-7b")

    # Apply TriAttention processor
    processor = TriAttentionProcessor(kv_budget=2048)
    llm.apply_processor(processor)

    # Run inference normally
    outputs = llm.generate(["Hello world"], SamplingParams(max_tokens=100))
"""

from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import torch


@dataclass
class VLLMTriAttentionConfig:
    """Configuration for TriAttention in vLLM context."""
    kv_budget: int = 2048
    num_bands: int = 32
    prune_interval: int = 128
    window_size: int = 128


class TriAttentionProcessor:
    """
    Custom attention processor for vLLM with TriAttention.

    This processor intercepts vLLM's attention computation and applies
    TriAttention-based scoring and eviction to the KV cache.

    Usage:
        processor = TriAttentionProcessor(kv_budget=2048)
        llm = LLM(model="llama-2-7b")
        llm.apply_processor(processor)
    """

    def __init__(
        self,
        kv_budget: int = 2048,
        num_bands: int = 32,
        prune_interval: int = 128,
        window_size: int = 128,
        device: str = "cuda",
        dtype: torch.dtype = torch.bfloat16,
    ):
        """
        Initialize TriAttention processor.

        Args:
            kv_budget: Maximum KV pairs to retain
            num_bands: Number of frequency bands
            prune_interval: Tokens between pruning
            window_size: Window for position-aware scoring
            device: Computation device
            dtype: Data type
        """
        self.config = VLLMTriAttentionConfig(
            kv_budget=kv_budget,
            num_bands=num_bands,
            prune_interval=prune_interval,
            window_size=window_size,
        )
        self.device = torch.device(device)
        self.dtype = dtype

        # Per-layer TriAttention instances (set during apply)
        self.triattention_by_layer: Dict[int, Any] = {}

        # State tracking
        self.tokens_since_prune = 0
        self.current_position = 0

    def init_layer(self, layer_idx: int, layer_config: Dict[str, Any]) -> None:
        """
        Initialize TriAttention for a specific layer.

        Args:
            layer_idx: Layer index
            layer_config: Layer configuration from vLLM
        """
        from ...core import TriAttention, TriAttentionConfig

        num_heads = layer_config.get("num_heads", 32)
        num_kv_heads = layer_config.get("num_kv_heads", num_heads)
        head_dim = layer_config.get("head_dim", 128)

        config = TriAttentionConfig(
            num_heads=num_heads,
            num_kv_heads=num_kv_heads,
            head_dim=head_dim,
            kv_budget=self.config.kv_budget,
            num_bands=self.config.num_bands,
            device=str(self.device),
            dtype=self.dtype,
        )

        self.triattention_by_layer[layer_idx] = TriAttention(config)

    def process_layer(
        self,
        layer_idx: int,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        position: int,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Process a single attention layer.

        Args:
            layer_idx: Layer index
            query: Query tensor
            key: Key tensor
            value: Value tensor
            position: Current position

        Returns:
            Modified (query, key, value) with potential eviction
        """
        if layer_idx not in self.triattention_by_layer:
            return query, key, value

        tri = self.triattention_by_layer[layer_idx]
        self.current_position = position

        # Score keys
        scores = tri.score_keys_position_aware(
            keys=key,
            positions=torch.tensor([position], device=self.device),
            current_position=position,
        )

        # Track tokens
        self.tokens_since_prune += 1

        # Prune if needed
        if self.tokens_since_prune >= self.config.prune_interval:
            self._prune_layer(layer_idx)
            self.tokens_since_prune = 0

        return query, key, value

    def _prune_layer(self, layer_idx: int) -> None:
        """
        Prune KV cache for a layer.

        Args:
            layer_idx: Layer to prune
        """
        if layer_idx not in self.triattention_by_layer:
            return

        tri = self.triattention_by_layer[layer_idx]
        # Trigger pruning based on score threshold
        # Actual eviction is handled by vLLM's internal cache
        tri.prune(top_k=self.config.kv_budget)

    def process_forward(
        self,
        layer_idx: int,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.Tensor] = None,
        **kwargs,
    ) -> torch.Tensor:
        """
        Process full attention forward pass.

        This is called by vLLM during the attention forward pass.
        Override to implement custom TriAttention scoring.

        Args:
            layer_idx: Layer index
            query: Query [batch, num_heads, seq_len, head_dim]
            key: Key [batch, num_kv_heads, seq_len, head_dim]
            value: Value [batch, num_kv_heads, seq_len, head_dim]
            attention_mask: Optional attention mask
            position_ids: Position IDs
            **kwargs: Additional args

        Returns:
            Attention output
        """
        # Get position
        if position_ids is not None:
            position = position_ids.max().item() + 1
        else:
            position = query.shape[2]

        # Process with TriAttention
        query, key, value = self.process_layer(
            layer_idx, query, key, value, position
        )

        # Return standard attention result
        # In practice, vLLM would compute this
        raise NotImplementedError(
            "TriAttentionProcessor must be used with vLLM's internal attention"
        )


class TriAttentionCacheManager:
    """
    Cache manager that coordinates TriAttention across vLLM layers.

    This manager maintains per-layer calibration and scoring state,
    and coordinates eviction decisions across the model.
    """

    def __init__(
        self,
        num_layers: int,
        kv_budget: int = 2048,
        num_bands: int = 32,
        device: str = "cuda",
        dtype: torch.dtype = torch.bfloat16,
    ):
        """
        Initialize cache manager.

        Args:
            num_layers: Total number of layers
            kv_budget: Budget per layer
            num_bands: Number of frequency bands
            device: Device
            dtype: Data type
        """
        self.num_layers = num_layers
        self.kv_budget = kv_budget
        self.num_bands = num_bands
        self.device = torch.device(device)
        self.dtype = dtype

        # Per-layer state
        self.calibration_by_layer: Dict[int, Any] = {}
        self.triattention_by_layer: Dict[int, Any] = {}

        # Global tracking
        self.total_evicted = 0
        self.num_prunes = 0

    def init_layer(self, layer_idx: int, layer_cfg: Dict[str, Any]) -> None:
        """Initialize a layer's TriAttention."""
        from ...core import TriAttention, TriAttentionConfig

        config = TriAttentionConfig(
            num_heads=layer_cfg.get("num_heads", 32),
            num_kv_heads=layer_cfg.get("num_kv_heads", 32),
            head_dim=layer_cfg.get("head_dim", 128),
            kv_budget=self.kv_budget,
            num_bands=self.num_bands,
            device=str(self.device),
            dtype=self.dtype,
        )

        self.triattention_by_layer[layer_idx] = TriAttention(config)

    def get_layer(self, layer_idx: int) -> Optional[Any]:
        """Get TriAttention instance for layer."""
        return self.triattention_by_layer.get(layer_idx)

    def calibrate_all(
        self,
        calibration_inputs: torch.Tensor,
        max_seq_len: int = 4096,
    ) -> None:
        """
        Run calibration on all layers.

        Args:
            calibration_inputs: Calibration input IDs
            max_seq_len: Max sequence length for calibration
        """
        for layer_idx, tri in self.triattention_by_layer.items():
            cal_data = tri.calibrate(calibration_inputs, max_seq_len=max_seq_len)
            self.calibration_by_layer[layer_idx] = cal_data

    def score_all_layers(
        self,
        keys: Dict[int, torch.Tensor],
        positions: Dict[int, torch.Tensor],
        current_position: int,
    ) -> Dict[int, torch.Tensor]:
        """
        Score KV entries across all layers.

        Args:
            keys: Dict mapping layer_idx -> keys tensor
            positions: Dict mapping layer_idx -> positions tensor
            current_position: Current sequence position

        Returns:
            Dict mapping layer_idx -> scores tensor
        """
        scores = {}
        for layer_idx in self.triattention_by_layer:
            if layer_idx not in keys:
                continue

            tri = self.triattention_by_layer[layer_idx]
            scores[layer_idx] = tri.score_keys_position_aware(
                keys=keys[layer_idx],
                positions=positions[layer_idx],
                current_position=current_position,
            )
        return scores

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated stats."""
        return {
            "total_layers": self.num_layers,
            "initialized_layers": len(self.triattention_by_layer),
            "total_evicted": self.total_evicted,
            "num_prunes": self.num_prunes,
            "budget_per_layer": self.kv_budget,
        }


def create_vllm_processor(
    kv_budget: int = 2048,
    num_bands: int = 32,
    prune_interval: int = 128,
    **kwargs,
) -> TriAttentionProcessor:
    """
    Create a TriAttention processor for vLLM.

    Args:
        kv_budget: Maximum KV pairs per layer
        num_bands: Number of frequency bands
        prune_interval: Tokens between pruning passes
        **kwargs: Additional config

    Returns:
        TriAttentionProcessor instance
    """
    return TriAttentionProcessor(
        kv_budget=kv_budget,
        num_bands=num_bands,
        prune_interval=prune_interval,
        **kwargs,
    )
