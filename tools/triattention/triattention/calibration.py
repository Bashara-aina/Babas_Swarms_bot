"""
Calibration utilities for TriAttention.

These utilities help compute Q/K centers and concentration metrics
from calibration datasets.
"""

import torch
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class CalibrationResult:
    """Result of calibration computation.

    Attributes:
        q_centers: Q centers per head per band [num_heads, num_bands]
        k_centers: K centers per head per band [num_heads, num_bands]
        q_norms: Mean Q norms per head per band [num_heads, num_bands]
        k_norms: Mean K norms per head per band [num_heads, num_bands]
        mrl: Mean Resultant Length per head per band [num_heads, num_bands]
        selected_bands: Band indices selected for attention computation
    """
    q_centers: torch.Tensor
    k_centers: torch.Tensor
    q_norms: torch.Tensor
    k_norms: torch.Tensor
    mrl: torch.Tensor
    selected_bands: torch.Tensor


def extract_pre_rope_embeddings(
    model,
    input_ids: torch.Tensor,
    layer_indices: Optional[List[int]] = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Extract pre-RoPE Q and K embeddings from a model.

    This is a utility function that hooks into a model's attention layers
    to capture the Q/K embeddings before RoPE rotation is applied.

    Args:
        model: A transformers model with attention layers
        input_ids: Input token IDs [batch, seq_len]
        layer_indices: Specific layers to extract from (None = all layers)

    Returns:
        Tuple of (q_embeddings, k_embeddings), each [num_layers, num_heads, seq_len, head_dim]

    Note:
        This function uses hooks to extract intermediate activations.
        For models without hooks, you may need to modify the model's forward pass.
    """
    q_embeddings_list = []
    k_embeddings_list = []

    hooks = []

    def make_hook(store, name):
        def hook(module, input, output):
            # For attention, input is (hidden_states,) or (hidden_states, attention_mask)
            # output is (output, ) or (output, attention_weights)
            if isinstance(output, tuple):
                hidden = output[0]
            else:
                hidden = output
            store.append(hidden.detach())

        return hook

    # Register hooks on attention layers
    for name, module in model.named_modules():
        if "attention" in name.lower() or "attn" in name.lower():
            if hasattr(module, "q_proj") and hasattr(module, "k_proj"):
                # This is likely an attention module with separate Q/K projections
                store_q = []
                store_k = []

                # Hook into the output of q_proj and k_proj
                hooks.append(
                    module.q_proj.register_forward_hook(
                        lambda m, i, o, s=store_q: s.append(o.detach())
                    )
                )
                hooks.append(
                    module.k_proj.register_forward_hook(
                        lambda m, i, o, s=store_k: s.append(o.detach())
                    )
                )

    # Run model
    with torch.no_grad():
        outputs = model(input_ids)
        # Clean up hooks
        for hook in hooks:
            hook.remove()

    return q_embeddings_list, k_embeddings_list


def calibrate_from_hidden_states(
    q_hidden: torch.Tensor,
    k_hidden: torch.Tensor,
    head_dim: int = 128,
    select_bands: int = 4,
) -> CalibrationResult:
    """
    Compute calibration data from pre-RoPE hidden states.

    Args:
        q_hidden: Q hidden states before RoPE [seq_len, num_heads, head_dim]
        k_hidden: K hidden states before RoPE [seq_len, num_heads, head_dim]
        head_dim: Dimension of each head
        select_bands: Number of dominant frequency bands to select

    Returns:
        CalibrationResult with computed centers and statistics
    """
    seq_len, num_heads, d = q_hidden.shape
    num_bands = d // 2

    # Reshape to complex representation
    # [seq_len, num_heads, num_bands, 2]
    q_reshaped = q_hidden[:, :, :num_bands * 2].view(seq_len, num_heads, num_bands, 2)
    k_reshaped = k_hidden[:, :, :num_bands * 2].view(seq_len, num_heads, num_bands, 2)

    # Convert to complex
    q_complex = torch.view_as_complex(q_reshaped.float())
    k_complex = torch.view_as_complex(k_reshaped.float())

    # Compute centers
    q_centers = torch.mean(q_complex, dim=0)  # [num_heads, num_bands]
    k_centers = torch.mean(k_complex, dim=0)  # [num_heads, num_bands]

    # Compute norms
    q_norms = torch.mean(torch.abs(q_complex), dim=0)  # [num_heads, num_bands]
    k_norms = torch.mean(torch.abs(k_complex), dim=0)  # [num_heads, num_bands]

    # Compute MRL (Mean Resultant Length)
    q_center_norms = torch.abs(q_centers)
    mrl = q_center_norms / (q_norms + 1e-8)

    # Select dominant bands based on contribution
    # Contribution = ||Q_center|| * ||K_center||
    contributions = q_center_norms * torch.abs(k_centers)
    selected_bands = torch.argsort(contributions, dim=1)[:, -select_bands:]

    return CalibrationResult(
        q_centers=q_centers,
        k_centers=k_centers,
        q_norms=q_norms,
        k_norms=k_norms,
        mrl=mrl,
        selected_bands=selected_bands,
    )


def compute_band_frequencies(
    num_bands: int,
    head_dim: int = 128,
    theta: float = 10000.0,
    device: torch.device = torch.device("cuda"),
) -> torch.Tensor:
    """
    Compute RoPE frequencies for each band.

    For band f: ω_f = θ^(-2f/d)

    Args:
        num_bands: Number of frequency bands (head_dim // 2)
        head_dim: Total head dimension
        theta: Base theta (default 10000)
        device: Device to create tensor on

    Returns:
        Frequency values per band [num_bands]
    """
    freqs = torch.pow(
        torch.tensor(theta, device=device, dtype=torch.float32),
        -torch.arange(0, 2 * num_bands, 2, device=device, dtype=torch.float32) / head_dim
    )
    return freqs


def validate_concentration(mrl: torch.Tensor, threshold: float = 0.95) -> torch.Tensor:
    """
    Validate that Q/K vectors are sufficiently concentrated.

    Args:
        mrl: Mean Resultant Length values
        threshold: Minimum MRL to consider concentration "high"

    Returns:
        Boolean mask where True indicates high concentration
    """
    return mrl > threshold
