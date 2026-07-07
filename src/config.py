"""
PSR Transition Training Configuration
======================================
Configures the PSR head repair toggling and related hyperparameters.

PSR_HEAD_REPAIR: When True, the model uses the repaired transition heads from
  `psr_transition_repaired.py` instead of the original heads from `psr_transition.py`.
  The repaired head includes:
    - Output bias initialized to 0.0 (was -1.0)
    - LeakyReLU(0.01) activation (was ReLU(inplace=True))
    - Xavier/Glorot uniform initialization for all linear layers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================================
# PSR Transition Configuration
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


# Singleton
C = PSRConfig()
