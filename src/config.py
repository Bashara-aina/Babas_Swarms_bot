"""
POPW Multi-Task Model Configuration
=====================================
Central configuration for the POPW multi-task model covering detection, head
pose, activity classification, and PSR (Posture State Recognition).

Values verified against doc 207 findings. All LV_CLAMP_MAX values corrected
from old defaults (4.0) to doc 207 values (detection=1.5, pose=2.0).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================================
# Image / Data Configuration
# ============================================================================

# Input image dimensions
IMG_WIDTH: int = 1280
IMG_HEIGHT: int = 720

# Batch sizes
BATCH_SIZE: int = 2              # doc 207: reduced for OOM mitigation
VAL_BATCH_SIZE: int = 4          # doc 207: safe with torch.no_grad()
RAM_CACHE_MAX_IMAGES: int = 0    # doc 207: disable RAM cache by default


# ============================================================================
# Detection Configuration
# ============================================================================

# Kendall log-var clamp max for detection (lower bound = -LV_CLAMP_MAX_DET)
# doc 207: was 4.0 (weight floor exp(-4)~0.018), fixed to 1.5 (floor 0.22)
LV_CLAMP_MAX_DET: float = 1.5

NUM_DET_CLASSES: int = 24

# Detection evaluation thresholds (applied via FULL_EVAL_OVERRIDES)
DET_EVAL_SCORE_THRESH: float = 0.5
DET_EVAL_NMS_IOU_THRESH: float = 0.5
DET_EVAL_MAX_PER_IMAGE: int = 300


# ============================================================================
# Head Pose Configuration
# ============================================================================

# Kendall log-var clamp max for pose (lower bound = -LV_CLAMP_MAX_POSE)
# doc 207: was 4.0, fixed to 2.0
LV_CLAMP_MAX_POSE: float = 2.0


# ============================================================================
# Activity Classification Configuration
# ============================================================================

# doc 207: grouping set to "none" (was "hybrid" in old config)
ACT_CLASS_GROUPING: str = "none"
NUM_ACT_OUTPUTS: int = 75


# ============================================================================
# PSR (Posture State Recognition) Configuration
# ============================================================================

# Toggle between original and repaired PSR transition head
PSR_HEAD_REPAIR: bool = True

# PSR model dimensions
PSR_FPN_CHANNELS: int = 256
PSR_FEAT_DIM: int = 768            # 3 scales * 256 channels
PSR_ENCODER_HIDDEN: int = 512
PSR_ENCODER_OUTPUT: int = 256
PSR_D_MODEL: int = 256
PSR_NHEAD: int = 4
PSR_NUM_LAYERS: int = 3
PSR_DIM_FEEDFORWARD: int = 1024
PSR_NUM_COMPONENTS: int = 11
PSR_HEAD_HIDDEN: int = 64

# Dropout rates
PSR_ENCODER_DROPOUT: float = 0.1
PSR_TRANSFORMER_DROPOUT: float = 0.2
PSR_HEAD_DROPOUT: float = 0.06

# Sequence training
PSR_SEQUENCE_LENGTH: int = 2
PSR_SEQ_EVERY_N_BATCHES: int = 2

# Loss
PSR_FOCAL_GAMMA: float = 1.0
PSR_FOCAL_ALPHA: float = 0.25
PSR_WEIGHT: float = 10.0
PSR_LOSS_CAP: float = 20.0
PSR_SENSITIVITY_WEIGHT: float = 0.01
PSR_TEMPORAL_SMOOTH_WEIGHT: float = 0.05
PSR_TRANSITION_BOOST: float = 3.0  # [OPUS 207 §4.3] Boost weight on transition frames

# Per-component inverse-prevalence weights (11 PSR components)
# doc 207: component 4 gets 5.03x, component 10 gets 4.61x
PSR_COMP_WEIGHTS: list = [1.0, 1.21, 1.20, 1.98, 5.03, 1.61, 1.66, 2.20, 2.20, 2.75, 4.61]


# ============================================================================
# Dataclass for code access
# ============================================================================


@dataclass
class PSRConfig:
    """PSR transition configuration."""
    HEAD_REPAIR: bool = PSR_HEAD_REPAIR
    FPN_CHANNELS: int = PSR_FPN_CHANNELS
    FEAT_DIM: int = PSR_FEAT_DIM
    ENCODER_HIDDEN: int = PSR_ENCODER_HIDDEN
    ENCODER_OUTPUT: int = PSR_ENCODER_OUTPUT
    D_MODEL: int = PSR_D_MODEL
    NHEAD: int = PSR_NHEAD
    NUM_LAYERS: int = PSR_NUM_LAYERS
    DIM_FEEDFORWARD: int = PSR_DIM_FEEDFORWARD
    NUM_COMPONENTS: int = PSR_NUM_COMPONENTS
    HEAD_HIDDEN: int = PSR_HEAD_HIDDEN
    ENCODER_DROPOUT: float = PSR_ENCODER_DROPOUT
    TRANSFORMER_DROPOUT: float = PSR_TRANSFORMER_DROPOUT
    HEAD_DROPOUT: float = PSR_HEAD_DROPOUT
    SEQUENCE_LENGTH: int = PSR_SEQUENCE_LENGTH
    SEQ_EVERY_N_BATCHES: int = PSR_SEQ_EVERY_N_BATCHES
    FOCAL_GAMMA: float = PSR_FOCAL_GAMMA
    FOCAL_ALPHA: float = PSR_FOCAL_ALPHA
    WEIGHT: float = PSR_WEIGHT
    LOSS_CAP: float = PSR_LOSS_CAP
    SENSITIVITY_WEIGHT: float = PSR_SENSITIVITY_WEIGHT
    TEMPORAL_SMOOTH_WEIGHT: float = PSR_TEMPORAL_SMOOTH_WEIGHT
    TRANSITION_BOOST: float = PSR_TRANSITION_BOOST


# Singleton
C = PSRConfig()
