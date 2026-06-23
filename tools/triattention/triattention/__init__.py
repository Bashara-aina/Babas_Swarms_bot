"""
TriAttention: Efficient Long Reasoning with Trigonometric KV Compression

A KV cache compression method that leverages Q/K concentration in pre-RoPE space
to estimate key importance via trigonometric series scoring.

Paper: https://arxiv.org/abs/2604.04921
"""

from .core import TriAttention, TriAttentionConfig, CalibrationData, compute_mrl, compute_centers
from .calibration import CalibrationResult, calibrate_from_hidden_states, compute_band_frequencies, validate_concentration
from .scoring import compute_trig_score, compute_trig_score_batch, compute_norm_score, compute_combined_score, score_keys_at_offsets  # noqa: F401
from .cache import TriAttentionCache, StreamingCache, CacheEntry

__version__ = "0.1.0"
__all__ = [
    # Core
    "TriAttention",
    "TriAttentionConfig",
    "CalibrationData",
    "compute_mrl",
    "compute_centers",
    # Calibration
    "CalibrationResult",
    "calibrate_from_hidden_states",
    "compute_band_frequencies",
    "validate_concentration",
    # Scoring
    "compute_trig_score",
    "compute_norm_score",
    "compute_combined_score",
    "score_keys_at_offsets",
    # Cache
    "TriAttentionCache",
    "StreamingCache",
    "CacheEntry",
]
