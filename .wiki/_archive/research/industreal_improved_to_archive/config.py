"""
POPW v2/v3 Training Configuration
=================================
Safe batch size for RTX 3060 12GB + EMA + mixed precision.
BATCH_SIZE=2 w/ GRAD_ACCUM=16 → effective batch 32.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================================
# Data
# ============================================================================

IMG_HEIGHT: int = 224
IMG_WIDTH: int = 224
NUM_FRAMES: int = 16        # frames per clip
STRIDE: int = 2              # temporal stride

# ============================================================================
# Model
# ============================================================================

BACKBONE: str = "convnext_base.fb_in22k_ft_in1k"
IN_CHANNELS: int = 768      # ConvNeXt-Base output channels
TEMPORAL_CHANNELS: int = 768

NUM_ACT_CLASSES: int = 33   # IKEA assembly activities
NUM_HEAD_POSE: int = 6      # 3 angles (rad) + 3 position (mm)
NUM_ASSEMBLY_STATES: int = 3  # pre-assembly / in-assembly / post-assembly

# ============================================================================
# Training — RTX 3060 Safe
# ============================================================================

BATCH_SIZE: int = 2                # per-GPU batch (no gradient checkpointing needed)
GRAD_ACCUM_STEPS: int = 16         # → effective batch = 32
EFFECTIVE_BATCH_SIZE: int = BATCH_SIZE * GRAD_ACCUM_STEPS  # 32

# Mixed precision
USE_AMP: bool = True                # torch.cuda.amp — ~40% memory reduction
AMP_DTYPE: str = "float16"          # "float16" or "bfloat16"

# EMA (Exponential Moving Average) — safe at BATCH_SIZE=2
USE_EMA: bool = True
EMA_DECAY: float = 0.9998
EMA_WARMUP: int = 2000              # steps before EMA starts tracking

# Optimizer
OPTIMIZER: str = "AdamW"
LR: float = 3e-4
WEIGHT_DECAY: float = 0.05
BETAS: tuple = (0.9, 0.999)

# Schedules
SCHEDULE: str = "cosine"            # "cosine" | "step" | "plateau"
WARMUP_STEPS: int = 500
MIN_LR: float = 1e-6

# Regularization
DROP_PATH_RATE: float = 0.1
DROPOUT_ACTIVITY: float = 0.3
LABEL_SMOOTHING: float = 0.1        # LDAMLoss label smoothing

# ============================================================================
# Streaming / PSR
# ============================================================================

PSR_SEQUENCE_MODE: bool = False    # enable after training validates architecture
PSR_TEMPORAL_TOLERANCES: tuple = (3, 5)
PSR_NUM_PHASES: int = 8

# ============================================================================
# Data Loading
# ============================================================================

NUM_WORKERS: int = 4
PREFETCH_FACTOR: int = 2
PIN_MEMORY: bool = True

# Data augmentations
RANDOM_RESIZED_CROP: bool = True
RANDOM_HFLIP: bool = True
COLOR_JITTER: float = 0.4
RANDOM_AUG: bool = True

# ============================================================================
# Validation
# ============================================================================

VAL_INTERVAL: int = 1000           # steps between val checks
SAVE_INTERVAL: int = 5000           # steps between checkpoints
MAX_CHECKPOINTS: int = 3           # keep only N latest checkpoints

# ============================================================================
# Paths (override via env or CLI)
# ============================================================================

DATA_ROOT: str = "./data/industreal"
CHECKPOINT_DIR: str = "./checkpoints/popw_v2"
LOG_DIR: str = "./logs/popw_v2"

# ============================================================================
# Dataclass for code access
# ============================================================================

@dataclass
class Config:
    # Data
    IMG_HEIGHT: int = IMG_HEIGHT
    IMG_WIDTH: int = IMG_WIDTH
    NUM_FRAMES: int = NUM_FRAMES
    STRIDE: int = STRIDE

    # Model
    BACKBONE: str = BACKBONE
    IN_CHANNELS: int = IN_CHANNELS
    TEMPORAL_CHANNELS: int = TEMPORAL_CHANNELS
    NUM_ACT_CLASSES: int = NUM_ACT_CLASSES
    NUM_HEAD_POSE: int = NUM_HEAD_POSE
    NUM_ASSEMBLY_STATES: int = NUM_ASSEMBLY_STATES

    # Training
    BATCH_SIZE: int = BATCH_SIZE
    GRAD_ACCUM_STEPS: int = GRAD_ACCUM_STEPS
    EFFECTIVE_BATCH_SIZE: int = EFFECTIVE_BATCH_SIZE
    USE_AMP: bool = USE_AMP
    AMP_DTYPE: str = AMP_DTYPE
    USE_EMA: bool = USE_EMA
    EMA_DECAY: float = EMA_DECAY
    EMA_WARMUP: int = EMA_WARMUP
    OPTIMIZER: str = OPTIMIZER
    LR: float = LR
    WEIGHT_DECAY: float = WEIGHT_DECAY
    BETAS: tuple = BETAS
    SCHEDULE: str = SCHEDULE
    WARMUP_STEPS: int = WARMUP_STEPS
    MIN_LR: float = MIN_LR
    DROP_PATH_RATE: float = DROP_PATH_RATE
    DROPOUT_ACTIVITY: float = DROPOUT_ACTIVITY
    LABEL_SMOOTHING: float = LABEL_SMOOTHING

    # Streaming
    PSR_SEQUENCE_MODE: bool = PSR_SEQUENCE_MODE
    PSR_TEMPORAL_TOLERANCES: tuple = PSR_TEMPORAL_TOLERANCES
    PSR_NUM_PHASES: int = PSR_NUM_PHASES

    # Data loading
    NUM_WORKERS: int = NUM_WORKERS
    PREFETCH_FACTOR: int = PREFETCH_FACTOR
    PIN_MEMORY: bool = PIN_MEMORY
    RANDOM_RESIZED_CROP: bool = RANDOM_RESIZED_CROP
    RANDOM_HFLIP: bool = RANDOM_HFLIP
    COLOR_JITTER: float = COLOR_JITTER
    RANDOM_AUG: bool = RANDOM_AUG

    # Validation
    VAL_INTERVAL: int = VAL_INTERVAL
    SAVE_INTERVAL: int = SAVE_INTERVAL
    MAX_CHECKPOINTS: int = MAX_CHECKPOINTS

    # Paths
    DATA_ROOT: str = DATA_ROOT
    CHECKPOINT_DIR: str = CHECKPOINT_DIR
    LOG_DIR: str = LOG_DIR


# Singleton
C = Config()