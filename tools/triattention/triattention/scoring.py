"""
Scoring functions for TriAttention.

These functions implement the trigonometric series scoring and norm-based
scoring described in the TriAttention paper.
"""

import torch
from typing import Optional, List, Tuple


def compute_trig_score(
    q_center: torch.Tensor,
    k_center: torch.Tensor,
    rope_freqs: torch.Tensor,
    delta: int,
) -> torch.Tensor:
    """
    Compute trigonometric series score for a key at given distance.

    Strig(k, Δ) = Σ_f ||Q_center_f|| * ||k_f|| * cos(ω_f * Δ + φ_f)

    where:
    - f indexes frequency bands
    - φ_f = arg(Q_center_f) - arg(k_center_f)
    - Δ is the Q-K distance

    Args:
        q_center: Q center vector [num_heads, num_bands]
        k_center: K center vector [num_heads, num_bands]
        rope_freqs: RoPE frequencies per band [num_bands]
        delta: Q-K distance (integer)

    Returns:
        Trigonometric series score [num_heads]
    """
    # Phase difference between Q and K centers
    q_phase = torch.angle(q_center)
    k_phase = torch.angle(k_center)
    phi = q_phase - k_phase

    # ω_f * Δ
    omega_delta = rope_freqs * delta

    # cos(ω_f * Δ + φ_f)
    angle = omega_delta.unsqueeze(0) + phi
    cos_term = torch.cos(angle)

    # Amplitude: ||Q_center_f|| * ||k_center_f||
    amplitude = torch.abs(q_center) * torch.abs(k_center)

    # Sum over frequency bands
    score = torch.sum(amplitude * cos_term, dim=-1)
    return score


def compute_trig_score_batch(
    q_centers: torch.Tensor,
    k_centers: torch.Tensor,
    rope_freqs: torch.Tensor,
    deltas: torch.Tensor,
) -> torch.Tensor:
    """
    Compute trigonometric series scores for batch of keys and distances.

    Args:
        q_centers: Q centers [num_heads, num_bands]
        k_centers: K centers [num_heads, num_bands]
        rope_freqs: RoPE frequencies [num_bands]
        deltas: Q-K distances [num_keys]

    Returns:
        Scores [num_keys, num_heads]
    """
    num_heads, num_bands = q_centers.shape

    # Phase difference [num_heads, num_bands]
    q_phase = torch.angle(q_centers)
    k_phase = torch.angle(k_centers)
    phi = q_phase - k_phase

    # ω_f * Δ for each delta [num_keys, num_bands]
    omega_delta = rope_freqs.unsqueeze(0) * deltas.unsqueeze(1)

    # cos(ω_f * Δ + φ_f) [num_keys, num_heads, num_bands]
    angle = omega_delta.unsqueeze(1) + phi.unsqueeze(0)
    cos_term = torch.cos(angle)

    # Amplitude [num_heads, num_bands] -> [1, num_heads, num_bands]
    amplitude = (torch.abs(q_centers) * torch.abs(k_centers)).unsqueeze(0)

    # Score [num_keys, num_heads]
    scores = torch.sum(amplitude * cos_term, dim=-1)
    return scores


def compute_norm_score(
    q_norms: torch.Tensor,
    k_norms: torch.Tensor,
    mrl: torch.Tensor,
    k_center: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """
    Compute norm-based importance score.

    Snorm(k) = Σ_f (E[||q_f||] - ||E[q_f]||) * ||k_f||
             = Σ_f (1 - R_f) * E[||q_f||] * ||k_f||

    where R_f is the MRL (concentration).

    When concentration is high (R_f → 1), this term contributes less.
    When concentration is low (R_f → 0), this term dominates.

    Args:
        q_norms: Expected Q norms per band [num_heads, num_bands]
        k_norms: Expected K norms per band [num_heads, num_bands]
        mrl: Mean Resultant Length per band [num_heads, num_bands]
        k_center: Optional K center for ||k_f|| computation

    Returns:
        Norm-based score [num_heads]
    """
    # Concentration factor (1 - R_f)
    concentration_factor = 1 - mrl

    # ||k_f|| - use norms if k_center not provided
    if k_center is not None:
        k_norm = torch.abs(k_center)
    else:
        k_norm = k_norms

    # Contribution per band
    contribution = concentration_factor * q_norms * k_norm

    # Sum over bands
    score = torch.sum(contribution, dim=-1)
    return score


def compute_combined_score(
    trig_score: torch.Tensor,
    norm_score: torch.Tensor,
    head_weights: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """
    Combine trigonometric and norm-based scores.

    S_final(k) = Strig(k) + Snorm(k)

    Args:
        trig_score: Trigonometric series score [num_heads]
        norm_score: Norm-based score [num_heads]
        head_weights: Optional weights per head [num_heads]

    Returns:
        Combined score [num_heads]
    """
    combined = trig_score + norm_score

    if head_weights is not None:
        combined = combined * head_weights

    return combined


def score_keys_at_offsets(
    key_positions: torch.Tensor,
    q_centers: torch.Tensor,
    k_centers: torch.Tensor,
    q_norms: torch.Tensor,
    mrl: torch.Tensor,
    rope_freqs: torch.Tensor,
    current_position: int,
    offsets: List[int] = None,
) -> torch.Tensor:
    """
    Score all keys considering multiple future query offsets.

    Keys are scored at each offset and the scores are averaged.

    Args:
        key_positions: Positions of keys in cache [num_keys]
        q_centers: Q centers [num_heads, num_bands]
        k_centers: K centers [num_heads, num_bands]
        q_norms: Expected Q norms [num_heads, num_bands]
        mrl: MRL for concentration [num_heads, num_bands]
        rope_freqs: RoPE frequencies [num_bands]
        current_position: Current sequence length
        offsets: List of offsets to evaluate (default: geometric progression)

    Returns:
        Average scores per key [num_keys]
    """
    if offsets is None:
        offsets = [2 ** i for i in range(17)]  # 1, 2, 4, ..., 65536

    num_keys = key_positions.shape[0]
    num_heads, num_bands = q_centers.shape

    # Precompute norm scores (same for all keys)
    norm_score = compute_norm_score(q_norms, torch.abs(k_centers), mrl)

    # Score for each offset
    all_scores = []

    for offset in offsets:
        query_pos = current_position + offset

        # Q-K distance for each key
        delta = query_pos - key_positions  # [num_keys]

        # Only consider positive deltas
        valid_mask = delta > 0
        if not valid_mask.any():
            continue

        valid_deltas = delta[valid_mask]

        # Compute trig scores for valid keys
        trig_scores = compute_trig_score_batch(
            q_centers, k_centers, rope_freqs, valid_deltas
        )  # [num_valid, num_heads]

        # Combine with norm score
        combined = trig_scores + norm_score.unsqueeze(0)  # [num_valid, num_heads]

        # Average over heads
        key_scores = torch.mean(combined, dim=1)  # [num_valid]

        # Place back in full array
        full_scores = torch.zeros(num_keys, device=key_positions.device)
        full_scores[valid_mask] = key_scores

        all_scores.append(full_scores)

    # Average over all offsets
    if all_scores:
        final_scores = torch.stack(all_scores).mean(dim=0)
    else:
        final_scores = torch.zeros(num_keys, device=key_positions.device)

    return final_scores


def reconstruct_attention_from_trig_series(
    q_center: torch.Tensor,
    k_center: torch.Tensor,
    rope_freqs: torch.Tensor,
    distances: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Reconstruct attention logits using trigonometric series.

    This can be used to visualize or validate the distance preferences
    predicted by the trigonometric series.

    Args:
        q_center: Q center [num_heads, num_bands]
        k_center: K center [num_heads, num_bands]
        rope_freqs: RoPE frequencies [num_bands]
        distances: Distances to reconstruct for [num_distances]

    Returns:
        Tuple of (distances, predicted_logits)
    """
    num_heads, num_bands = q_center.shape

    # Phase difference
    q_phase = torch.angle(q_center)
    k_phase = torch.angle(k_center)
    phi = q_phase - k_phase

    # Amplitude
    amplitude = torch.abs(q_center) * torch.abs(k_center)  # [num_heads, num_bands]

    # Compute for each distance
    all_logits = []

    for d in distances:
        omega_delta = rope_freqs * d
        angle = omega_delta.unsqueeze(0) + phi
        cos_term = torch.cos(angle)
        logit = torch.sum(amplitude * cos_term, dim=-1)  # [num_heads]
        all_logits.append(logit)

    predicted_logits = torch.stack(all_logits)  # [num_distances, num_heads]
    return distances, predicted_logits
