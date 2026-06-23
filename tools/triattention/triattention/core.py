"""
Core TriAttention implementation for KV cache compression.

This module implements the main TriAttention algorithm for KV cache compression
based on the paper "TriAttention: Efficient Long Reasoning with Trigonometric KV Compression".

Key ideas:
1. Q/K vectors in pre-RoPE space are concentrated around fixed non-zero centers
2. This concentration causes attention to favor keys at specific distances
3. Distance preferences can be predicted via trigonometric series computed from centers
4. Key importance = trigonometric series score + norm-based score (weighted by concentration)
"""

import torch
from dataclasses import dataclass
from typing import Optional, Tuple, List


@dataclass
class CalibrationData:
    """Calibration data for TriAttention computation.

    Stores pre-RoPE Q/K statistics computed from a calibration dataset.

    Attributes:
        q_centers: Mean Q vectors per head per frequency band [num_heads, d_head/2, 2]
        k_centers: Mean K vectors per head per frequency band [num_heads, d_head/2, 2]
        q_norms: Mean Q norms per head per frequency band [num_heads, d_head/2]
        k_norms: Mean K norms per head per frequency band [num_heads, d_head/2]
        mrl: Mean Resultant Length (concentration measure) per head per band [num_heads, d_head/2]
        freq_bands: Frequency band indices used for computation
        theta: RoPE base theta (default 10000)
    """
    q_centers: torch.Tensor
    k_centers: torch.Tensor
    q_norms: torch.Tensor
    k_norms: torch.Tensor
    mrl: torch.Tensor
    freq_bands: torch.Tensor
    theta: float = 10000.0


@dataclass
class TriAttentionConfig:
    """Configuration for TriAttention.

    Attributes:
        kv_budget: Maximum number of KV pairs to retain in cache
        num_heads: Number of attention heads
        head_dim: Dimension of each head (d_head)
        num_kv_heads: Number of KV heads (for GQA, can be less than num_heads)
        window_size: Pruning interval in tokens (default 128, following R-KV)
        max_cache_len: Maximum cache length before pruning is triggered
        device: Device to run computations on
        dtype: Data type for computations
    """
    kv_budget: int = 2048
    num_heads: int = 32
    head_dim: int = 128
    num_kv_heads: Optional[int] = None
    window_size: int = 128
    max_cache_len: int = 32768
    device: str = "cuda"
    dtype: torch.dtype = torch.bfloat16


class TriAttention:
    """
    TriAttention KV cache compression.

    Implements the TriAttention algorithm from the paper for efficient KV cache
    compression in long reasoning scenarios.

    The algorithm has three main components:
    1. Calibration: Compute Q/K centers from a calibration dataset
    2. Scoring: Compute importance scores using trigonometric series + norms
    3. Pruning: Retain only top-scoring keys within budget constraints

    Example:
        >>> config = TriAttentionConfig(kv_budget=2048, num_heads=32, head_dim=128)
        >>> triattention = TriAttention(config)
        >>> # Calibrate with representative data
        >>> calibration = triattention.calibrate(q_embeddings, k_embeddings)
        >>> # Score keys in cache
        >>> scores = triattention.score_keys(cache, calibration)
        >>> # Get top-B keys to retain
        >>> top_indices = triattention.prune(cache, scores)
    """

    def __init__(self, config: TriAttentionConfig):
        self.config = config
        self.num_heads = config.num_heads
        self.head_dim = config.head_dim
        self.num_kv_heads = config.num_kv_heads or config.num_heads
        self.kv_budget = config.kv_budget
        self.window_size = config.window_size
        self.device = torch.device(config.device)

        # Frequency bands for RoPE (d_head/2 bands)
        self.num_bands = config.head_dim // 2
        self.freq_bands = torch.arange(
            0, self.num_bands, device=self.device, dtype=torch.long
        )

        # Precompute RoPE frequencies: theta^(-2f/d) for f in freq_bands
        # This is ω_f in the paper
        self.rope_freqs = self._compute_rope_freqs()

        # Calibration data (set during calibrate())
        self.calibration_data: Optional[CalibrationData] = None

        # GQA group size
        self.gqa_ratio = config.num_heads // self.num_kv_heads

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"TriAttention(num_heads={self.num_heads}, "
            f"num_kv_heads={self.num_kv_heads}, "
            f"head_dim={self.head_dim}, "
            f"kv_budget={self.kv_budget}, "
            f"num_bands={self.num_bands}, "
            f"window_size={self.window_size}, "
            f"gqa_ratio={self.gqa_ratio})"
        )

    def _compute_rope_freqs(self) -> torch.Tensor:
        """Compute RoPE rotation frequencies for each frequency band.

        For band f, frequency is ω_f = θ^(-2f/d) where θ=10000 and d=head_dim.
        """
        theta = 10000.0
        d = self.head_dim

        # frequencies: [num_bands]
        freqs = torch.pow(
            torch.tensor(theta, device=self.device),
            -torch.arange(0, 2 * self.num_bands, 2, device=self.device, dtype=torch.float32) / d
        )
        return freqs

    def calibrate(
        self,
        q_embeddings: torch.Tensor,
        k_embeddings: torch.Tensor,
        select_bands: Optional[int] = 4,
    ) -> CalibrationData:
        """
        Compute Q/K centers from calibration data.

        Args:
            q_embeddings: Pre-RoPE Q embeddings [seq_len, num_heads, head_dim]
            k_embeddings: Pre-RoPE K embeddings [seq_len, num_heads, head_dim]
            select_bands: Number of dominant frequency bands to use (default 4)

        Returns:
            CalibrationData with computed centers and statistics

        Note:
            The embeddings should be pre-RoPE (before positional encoding).
            For most models, this means the embeddings before the RoPE rotation is applied.
        """
        seq_len, num_heads, head_dim = q_embeddings.shape
        num_bands = head_dim // 2

        # Handle GQA: use only kv_head embeddings for center computation
        # but tile to num_heads for consistent processing
        if num_heads != self.num_kv_heads and k_embeddings.shape[1] == self.num_kv_heads:
            # Tile K embeddings across query head groups
            k_emb = k_embeddings.repeat_interleave(self.gqa_ratio, dim=1)
        else:
            k_emb = k_embeddings

        # Reshape to [seq_len, num_heads, num_bands, 2] for complex representation
        # Each 2D subspace (2f, 2f+1) becomes a complex number
        q_reshaped = q_embeddings[:, :, :num_bands * 2].view(
            seq_len, num_heads, num_bands, 2
        )
        k_reshaped = k_emb[:, :, :num_bands * 2].view(
            seq_len, self.num_heads, num_bands, 2
        )

        # Convert to complex numbers: x + yi -> complex
        q_complex = torch.view_as_complex(q_reshaped.float())
        k_complex = torch.view_as_complex(k_reshaped.float())

        # Compute centers (means)
        q_centers = torch.mean(q_complex, dim=0)  # [num_heads, num_bands]
        k_centers = torch.mean(k_complex, dim=0)  # [num_heads, num_bands]

        # Compute norms
        q_norm_mean = torch.mean(torch.abs(q_complex), dim=0)  # [num_heads, num_bands]
        k_norm_mean = torch.mean(torch.abs(k_complex), dim=0)  # [num_heads, num_bands]

        q_center_norms = torch.abs(q_centers)
        k_center_norms = torch.abs(k_centers)

        # Compute Mean Resultant Length (MRL) for concentration
        # MRL = ||E[q]|| / E[||q||]
        mrl = q_center_norms / (q_norm_mean + 1e-8)

        # Select dominant frequency bands based on contribution
        # Band contribution = ||center|| * expected norm contribution
        contributions = q_center_norms * k_center_norms
        top_band_indices = torch.argsort(contributions, dim=1)[:, -select_bands:]
        # Clamp to valid range [0, num_bands-1]
        top_band_indices = torch.clamp(top_band_indices, min=0, max=num_bands - 1)

        # Store selected bands
        selected_bands = top_band_indices

        calibration = CalibrationData(
            q_centers=q_centers,
            k_centers=k_centers,
            q_norms=q_norm_mean,
            k_norms=k_norm_mean,
            mrl=mrl,
            freq_bands=selected_bands,
            theta=10000.0,
        )
        self.calibration_data = calibration
        return calibration

    def score_keys(
        self,
        key_positions: torch.Tensor,
        calibration: Optional[CalibrationData] = None,
        future_offsets: Optional[List[int]] = None,
    ) -> torch.Tensor:
        """
        Compute importance scores for keys in the cache.

        Args:
            key_positions: Positions of keys in cache [num_keys]
            calibration: Calibration data (uses self.calibration_data if None)
            future_offsets: Offsets to consider for future queries

        Returns:
            Importance scores for each key [num_keys]
        """
        if calibration is None:
            calibration = self.calibration_data
        if calibration is None:
            raise ValueError("No calibration data provided. Call calibrate() first.")

        if future_offsets is None:
            # Default: geometric progression of offsets
            future_offsets = [2 ** i for i in range(17)]  # 1, 2, 4, ..., 65536

        num_keys = key_positions.shape[0]
        num_heads = self.num_heads

        # Get Q centers [num_heads, num_bands]
        q_centers = calibration.q_centers
        q_norms = calibration.q_norms
        k_centers = calibration.k_centers
        k_norms = calibration.k_norms
        mrl = calibration.mrl
        safe_bands = torch.clamp(calibration.freq_bands, 0, self.num_bands - 1)

        # Compute scores for each key at each offset, then average
        all_scores = []

        for offset in future_offsets:
            # Q-K distance for each key when query is at position (key_pos + offset)
            # We approximate: future queries will be at positions key_pos + offset
            delta = offset  # same for all keys in this iteration

            # Compute trigonometric series score
            # Strig(k, Δ) = Σ_f ||Q_center_f|| * ||k_f|| * cos(ω_f * Δ + φ_f)
            # where φ_f = arg(Q_center_f) - arg(k_f)

            # Get k vectors (complex) for selected bands
            # Using centers as approximation for keys
            k_selected = k_centers[:, safe_bands]  # [num_heads, select_bands]

            # Phase difference: arg(Q_center) - arg(k_center)
            q_phase = torch.angle(q_centers[:, safe_bands])  # [num_heads, select_bands]
            k_phase = torch.angle(k_selected)  # [num_heads, select_bands]
            phi = q_phase - k_phase  # [num_heads, select_bands]

            # ω_f * Δ - use flat indexing to keep omega_delta 1D
            omega_delta = self.rope_freqs[safe_bands.flatten()] * delta  # [select_bands] (1D)
            omega_delta = omega_delta.view(num_heads, -1)  # reshape back to [num_heads, select_bands]

            # Cosine term: cos(ω_f * Δ + φ_f)
            angle = omega_delta.unsqueeze(0) + phi.unsqueeze(0)  # [num_heads, select_bands]
            cos_term = torch.cos(angle)

            # Amplitude: ||Q_center_f|| * ||k_f||
            amplitude = torch.abs(q_centers[:, safe_bands]) * torch.abs(k_selected)

            # Trigonometric score per head
            trig_score = torch.sum(amplitude * cos_term, dim=-1)  # [num_heads]

            # Norm-based score
            # Snorm(k) = Σ_f (E[||q_f||] - ||E[q_f]||) * ||k_f||
            # This is (1 - R_f) * E[||q_f||] * ||k_f||

            # Using concentration-weighted norm score
            concentration_factor = 1 - mrl[:, safe_bands]  # [num_heads, select_bands]
            norm_contribution = concentration_factor * q_norms[:, safe_bands] * torch.abs(k_selected)
            norm_score = torch.sum(norm_contribution, dim=-1)  # [num_heads]

            # Combined score
            combined = trig_score + norm_score  # [num_heads]

            # Average across heads for final score per key position
            # key_score is a scalar per offset (averaged across heads)
            key_score = torch.mean(combined)  # scalar (0D tensor)
            all_scores.append(key_score)

        # Average across all offsets - all_scores elements are 0D scalars
        avg_score = torch.stack(all_scores).mean()  # scalar

        # Return score for each key (identical since we use centers as proxy for all keys)
        return avg_score.expand(num_keys)

    def score_keys_position_aware(
        self,
        key_positions: torch.Tensor,
        calibration: Optional[CalibrationData] = None,
        num_current_tokens: int = 0,
    ) -> torch.Tensor:
        """
        Compute position-aware importance scores for keys.

        Different from score_keys, this considers the actual key positions
        relative to the current query position.

        Args:
            key_positions: Positions of keys in cache [num_keys]
            calibration: Calibration data
            num_current_tokens: Current sequence length (query position)

        Returns:
            Position-aware importance scores [num_keys]
        """
        if calibration is None:
            calibration = self.calibration_data
        if calibration is None:
            raise ValueError("No calibration data provided. Call calibrate() first.")

        num_keys = key_positions.shape[0]
        future_offsets = [2 ** i for i in range(17)]

        q_centers = calibration.q_centers
        q_norms = calibration.q_norms
        k_centers = calibration.k_centers
        k_norms = calibration.k_norms
        mrl = calibration.mrl
        selected_bands = calibration.freq_bands

        scores_per_key = []

        for key_idx in range(num_keys):
            key_pos = key_positions[key_idx]
            key_scores = []

            for offset in future_offsets:
                query_pos = num_current_tokens + offset
                delta = query_pos - key_pos.item() if key_pos.numel() == 1 else query_pos - key_pos

                if delta <= 0:
                    continue

                # Guard: delta * freq can overflow, so clamp delta
                if delta > 10000:
                    delta = 10000

                # Trigonometric series score
                k_selected = k_centers[:, selected_bands]
                q_phase = torch.angle(q_centers[:, selected_bands])
                k_phase = torch.angle(k_selected)
                phi = q_phase - k_phase

                # Clamp omega*delta to prevent overflow
                # Guard: ensure selected_bands indices are in bounds for rope_freqs
                safe_bands = selected_bands.clone()
                safe_bands = torch.clamp(safe_bands, 0, self.num_bands - 1)
                omega_delta = self.rope_freqs[safe_bands] * delta
                # Clip large values to avoid cos instability
                omega_delta = torch.clamp(omega_delta, min=-100.0, max=100.0)
                angle = omega_delta.unsqueeze(0) + phi.unsqueeze(0)
                cos_term = torch.cos(angle)

                amplitude = torch.abs(q_centers[:, selected_bands]) * torch.abs(k_selected)
                trig_score = torch.sum(amplitude * cos_term, dim=-1)

                # Norm-based score
                concentration_factor = 1 - mrl[:, selected_bands]
                norm_contribution = concentration_factor * q_norms[:, selected_bands] * torch.abs(k_selected)
                norm_score = torch.sum(norm_contribution, dim=-1)

                combined = trig_score + norm_score
                key_score = torch.mean(combined, dim=0)
                key_scores.append(key_score)

            if key_scores:
                avg_score = torch.stack(key_scores).mean()
            else:
                avg_score = torch.tensor(0.0, device=self.device)

            scores_per_key.append(avg_score)

        return torch.stack(scores_per_key)

    def prune(
        self,
        scores: torch.Tensor,
        budget: Optional[int] = None,
    ) -> torch.Tensor:
        """
        Select top-scoring keys to retain within budget.

        Args:
            scores: Importance scores [num_keys]
            budget: Maximum keys to retain (uses self.kv_budget if None)

        Returns:
            Indices of keys to retain [budget]
        """
        budget = budget or self.kv_budget
        num_keys = scores.shape[0]

        if num_keys <= budget:
            return torch.arange(num_keys, device=scores.device)

        # Get top-B indices
        _, top_indices = torch.topk(scores, budget)
        return top_indices


def compute_mrl(vectors: torch.Tensor) -> torch.Tensor:
    """
    Compute Mean Resultant Length for concentration measurement.

    MRL = ||E[v]|| / E[||v||]

    High MRL (close to 1) indicates vectors are concentrated around their mean.
    Low MRL (close to 0) indicates uniform dispersion.

    Args:
        vectors: Complex vectors [seq_len, num_heads, num_bands] or similar

    Returns:
        MRL values [num_heads, num_bands] or scalar
    """
    mean_vector = torch.mean(vectors, dim=0)
    mean_norm = torch.abs(mean_vector)

    norm_of_vectors = torch.abs(vectors)
    mean_norm_of_vectors = torch.mean(norm_of_vectors, dim=0)

    mrl = mean_norm / (mean_norm_of_vectors + 1e-8)
    return mrl


def compute_centers(
    q_embeddings: torch.Tensor,
    k_embeddings: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Compute Q/K centers from embeddings.

    Args:
        q_embeddings: Pre-RoPE Q embeddings
        k_embeddings: Pre-RoPE K embeddings

    Returns:
        Tuple of (q_centers, k_centers, mrl)
    """
    q_complex = torch.view_as_complex(q_embeddings.float())
    k_complex = torch.view_as_complex(k_embeddings.float())

    q_centers = torch.mean(q_complex, dim=0)
    k_centers = torch.mean(k_complex, dim=0)

    mrl_q = compute_mrl(q_complex)

    return q_centers, k_centers, mrl_q
