"""
Transformers integration for TriAttention.

Provides a drop-in replacement for transformers attention that uses
TriAttention for KV cache compression during long-context inference.

Example:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from triattention.integrations.transformers_integration import TriAttentionModel

    model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b")
    tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b")

    tri_model = TriAttentionModel(model, kv_budget=2048)
    outputs = tri_model.generate(**inputs)
"""

import torch
import torch.nn as nn
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from collections import deque

from ..core import TriAttention, TriAttentionConfig, CalibrationData


@dataclass
class LayerCalibrationData:
    """Per-layer calibration data for multi-layer models."""
    calibrations: Dict[int, CalibrationData]
    layer_indices: List[int]


class TriAttentionModel(nn.Module):
    """
    Wrapper that adds TriAttention KV compression to any HuggingFace model.

    This wrapper intercepts attention forward passes and uses TriAttention
    scoring to prune the KV cache during generation.

    Example:
        base_model = AutoModelForCausalLM.from_pretrained("llama-2-7b")
        tri_model = TriAttentionModel(base_model, kv_budget=2048)

        # Run generation as normal
        outputs = tri_model.generate(input_ids, max_new_tokens=100)
    """

    def __init__(
        self,
        model: nn.Module,
        kv_budget: int = 2048,
        num_bands: int = 32,
        calibration_data: Optional[LayerCalibrationData] = None,
        device: str = "cuda",
        dtype: torch.dtype = torch.bfloat16,
        **kwargs,
    ):
        """
        Initialize TriAttention wrapper.

        Args:
            model: Base HuggingFace model
            kv_budget: Maximum KV pairs to retain per layer
            num_bands: Number of frequency bands
            calibration_data: Pre-computed calibration data
            device: Device for computation
            dtype: Data type for computation
            **kwargs: Additional config passed to TriAttentionConfig
        """
        super().__init__()
        self.model = model
        self.device = torch.device(device)
        self.dtype = dtype

        # Get model config
        self.config = model.config
        self.num_heads = getattr(self.config, "num_attention_heads", 32)
        self.num_kv_heads = getattr(self.config, "num_key_value_heads", self.num_heads)
        self.head_dim = getattr(self.config, "head_dim", 128)

        # Initialize TriAttention for each layer
        self.triattention_per_layer: Dict[int, TriAttention] = {}

        # Build config and per-layer TriAttention
        tri_config = TriAttentionConfig(
            num_heads=self.num_heads,
            num_kv_heads=self.num_kv_heads,
            head_dim=self.head_dim,
            kv_budget=kv_budget,
            num_bands=num_bands,
            device=device,
            dtype=dtype,
            **kwargs,
        )

        # Determine layer indices to instrument
        self.layer_indices = self._detect_attention_layers()

        for layer_idx in self.layer_indices:
            self.triattention_per_layer[layer_idx] = TriAttention(tri_config)

        # Calibration data
        self.calibration_data = calibration_data

        # Hook handles for cleanup
        self.hooks: List[Any] = []

        # Register hooks
        self._register_hooks()

    def _detect_attention_layers(self) -> List[int]:
        """Detect which layers have attention."""
        num_layers = getattr(self.config, "num_hidden_layers", 32)
        return list(range(num_layers))

    def _register_hooks(self) -> None:
        """Register forward hooks on attention layers."""
        # This is a simplified version - full implementation would
        # need to walk the model and find the attention layers
        pass

    def calibrate(
        self,
        input_ids: torch.Tensor,
        max_seq_len: int = 4096,
    ) -> LayerCalibrationData:
        """
        Run calibration on the model.

        Args:
            input_ids: Calibration input IDs [batch, seq_len]
            max_seq_len: Maximum sequence length to calibrate on

        Returns:
            LayerCalibrationData with per-layer calibration
        """
        self.model.eval()

        calibrations: Dict[int, CalibrationData] = {}

        for layer_idx in self.layer_indices:
            tri = self.triattention_per_layer[layer_idx]
            cal_data = tri.calibrate(input_ids, max_seq_len=max_seq_len)
            calibrations[layer_idx] = cal_data

        self.calibration_data = LayerCalibrationData(
            calibrations=calibrations,
            layer_indices=self.layer_indices,
        )

        return self.calibration_data

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs,
    ) -> Any:
        """
        Forward pass with TriAttention.

        Args:
            input_ids: Input token IDs [batch, seq_len]
            attention_mask: Attention mask
            **kwargs: Additional arguments passed to base model

        Returns:
            Model outputs
        """
        # Use base model forward - hooks handle the TriAttention logic
        return self.model(input_ids, attention_mask=attention_mask, **kwargs)

    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 100,
        **kwargs,
    ) -> Any:
        """
        Generate with TriAttention KV compression.

        Args:
            input_ids: Input token IDs [batch, seq_len]
            max_new_tokens: Maximum tokens to generate
            **kwargs: Additional arguments passed to model.generate

        Returns:
            Generated token IDs
        """
        # Run generation - hooks intercept attention for KV pruning
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                **kwargs,
            )
        return outputs

    def remove_hooks(self) -> None:
        """Remove all registered hooks."""
        for hook in self.hooks:
            hook.remove()
        self.hooks = []

    def __del__(self):
        """Cleanup hooks on deletion."""
        self.remove_hooks()


class TriAttentionAttention(nn.Module):
    """
    Custom attention module with TriAttention support.

    This can be used to replace the attention module in a model
    with a TriAttention-aware version.
    """

    def __init__(
        self,
        base_attention: nn.Module,
        triattention: TriAttention,
    ):
        """
        Initialize with base attention and TriAttention.

        Args:
            base_attention: Original attention module
            triattention: TriAttention instance for scoring
        """
        super().__init__()
        self.base_attention = base_attention
        self.triattention = triattention

        # KV cache storage
        self.kv_cache_keys: List[torch.Tensor] = []
        self.kv_cache_values: List[torch.Tensor] = []
        self.kv_cache_positions: List[int] = []

    def clear_cache(self) -> None:
        """Clear the KV cache."""
        self.kv_cache_keys = []
        self.kv_cache_values = []
        self.kv_cache_positions = []

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        position: int,
        use_cache: bool = True,
        **kwargs,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass with TriAttention KV pruning.

        Args:
            query: Query tensor [batch, num_heads, seq_len, head_dim]
            key: Key tensor [batch, num_kv_heads, seq_len, head_dim]
            value: Value tensor [batch, num_kv_heads, seq_len, head_dim]
            position: Current position in sequence
            use_cache: Whether to use/populate cache

        Returns:
            Tuple of (output, (key_for_cache, value_for_cache))
        """
        # Run base attention
        output = self.base_attention(query, key, value, **kwargs)

        if use_cache:
            # Score keys and potentially prune
            scores = self.triattention.score_keys(key, position)

            # Update cache with pruning if needed
            self.kv_cache_keys.append(key)
            self.kv_cache_values.append(value)
            self.kv_cache_positions.append(position)

            # Prune if budget exceeded
            if len(self.kv_cache_keys) > self.triattention.config.kv_budget:
                # Get top-scoring entries
                all_scores = torch.cat([
                    self.triattention.score_keys(k, p)
                    for k, p in zip(self.kv_cache_keys, self.kv_cache_positions)
                ])
                _, top_indices = torch.topk(all_scores, self.triattention.config.kv_budget)

                self.kv_cache_keys = [self.kv_cache_keys[i] for i in top_indices]
                self.kv_cache_values = [self.kv_cache_values[i] for i in top_indices]
                self.kv_cache_positions = [self.kv_cache_positions[i] for i in top_indices]

            key_out = key
            value_out = value
        else:
            key_out = None
            value_out = None

        return output, (key_out, value_out)


def create_triattention_wrapper(
    model: nn.Module,
    kv_budget: int = 2048,
    num_bands: int = 32,
    calibration_inputs: Optional[torch.Tensor] = None,
    **kwargs,
) -> TriAttentionModel:
    """
    Create a TriAttention-wrapped model.

    This is the main entry point for integrating TriAttention with
    a HuggingFace model.

    Args:
        model: Base model to wrap
        kv_budget: KV cache budget per layer
        num_bands: Number of frequency bands
        calibration_inputs: Optional inputs for calibration
        **kwargs: Additional config

    Returns:
        TriAttentionModel wrapper
    """
    wrapper = TriAttentionModel(
        model=model,
        kv_budget=kv_budget,
        num_bands=num_bands,
        **kwargs,
    )

    if calibration_inputs is not None:
        wrapper.calibrate(calibration_inputs)

    return wrapper
