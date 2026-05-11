"""
POPW v2/v3 Training Script
=========================
Full multi-task training for POPW (Phase Observation Protocol for Workers).

Fixes applied (from session crash analysis):
  1. num_workers=0 — eliminates DataLoader subprocesses (suspected OOM source at batch ~270)
  2. Thread convoy: OMP_NUM_THREADS=4, MKL_NUM_THREADS=4, OPENBLAS_NUM_THREADS=4,
     NUMEXPR_NUM_THREADS=4, MALLOC_ARENA_MAX=4
  3. torch.set_num_threads(4) + torch.set_num_interop_threads(4)
  4. Fork multiprocessing context (NOT spawn — Python 3.13 + loky spawn triggers semaphore leaks)
  5. _FlushingFileHandler with flush() after every emit() — no log buffering
  6. faulthandler.enable() — catch segfaults before Python crashes
  7. Heartbeat logging every 50 batches — track liveness

Usage:
  python train.py                          # start from scratch
  python train.py --resume                # resume from latest checkpoint
  python train.py --resume --max-epochs 1   # debug: 1 epoch only
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import autocast, GradScaler
from torch.utils.data import DataLoader, Dataset

# ---------------------------------------------------------------------------
# Thread convoy fix — BEFORE any torch or numpy imports
# ---------------------------------------------------------------------------
_env_thread_fix = {
    "OMP_NUM_THREADS": "4",
    "MKL_NUM_THREADS": "4",
    "OPENBLAS_NUM_THREADS": "4",
    "NUMEXPR_NUM_THREADS": "4",
    "MALLOC_ARENA_MAX": "4",
}
for k, v in _env_thread_fix.items():
    os.environ[k] = v

# Now safe to import torch/numpy
import torch.nn.functional as F

# Set torch threads AFTER env vars are set
torch.set_num_threads(4)
torch.set_num_interop_threads(4)

# Enable faulthandler to catch segfaults early
import faulthandler
faulthandler.enable()

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from model import POPWMultiTaskModel, count_parameters
from losses import (
    LDAMLoss,
    HeadPoseLoss,
    AssemblyStateLoss,
    ErrorVerificationLoss,
    PSRContrastiveLoss,
    MultiTaskLoss,
)
import config as C

# ---------------------------------------------------------------------------
# Flushing File Handler — no log buffering
# ---------------------------------------------------------------------------

class _FlushingFileHandler(logging.FileHandler):
    """File handler that flushes after every emit()."""
    def emit(self, record):
        super().emit(record)
        self.flush()


def setup_logging(log_dir: Path) -> logging.Logger:
    log_file = log_dir / "train.log"
    logger = logging.getLogger("popw_train")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fh = _FlushingFileHandler(log_file, mode="a")
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(sh)

    return logger


# ---------------------------------------------------------------------------
# Dataset (synthetic — replace with real IndustReal dataset)
# ---------------------------------------------------------------------------

class SyntheticIndustRealDataset(Dataset):
    """
    Synthetic IndustReal dataset for training.

    For REAL data, replace this with actual IndustReal dataset loader:
      - 25,159 samples (video clips with annotations)
      - 5 tasks: activity (33 classes), head_pose (6), assembly_state (3),
        error_verification (binary), PSR (phase similarity)
    """
    def __init__(self, num_samples: int = 5000, num_frames: int = 16):
        self.num_samples = num_samples
        self.num_frames = num_frames
        self.img_h, self.img_w = C.IMG_HEIGHT, C.IMG_WIDTH

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        # Synthetic image [T=16, C=3, H=224, W=224]
        images = torch.randn(self.num_frames, 3, self.img_h, self.img_w)
        # Normalize to ImageNet stats
        mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
        images = (images * std + mean).clamp(0, 1)

        # Synthetic labels
        B = self.num_frames
        activity_labels = torch.randint(0, C.NUM_ACT_CLASSES, (B,))
        head_pose_labels = torch.randn(B, 6)
        assembly_labels = torch.randint(0, C.NUM_ASSEMBLY_STATES, (B,))
        error_labels = torch.randint(0, 2, (B,)).float()
        phase_labels = torch.randint(0, C.PSR_NUM_PHASES, (B,))

        return {
            "images": images,            # [T, C, H, W]
            "video_id": f"vid_{idx:06d}",
            "activity_labels": activity_labels,
            "head_pose_labels": head_pose_labels,
            "assembly_labels": assembly_labels,
            "error_labels": error_labels,
            "phase_labels": phase_labels,
        }


def collate_fn(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    """
    Custom collate: stack images, keep labels as-is.
    NOTE: num_workers=0 means this runs in the main process (no subprocess serialization).
    """
    images = torch.stack([b["images"] for b in batch])           # [B, T, C, H, W]
    video_ids = [b["video_id"] for b in batch]

    def stack_labels(key: str) -> torch.Tensor:
        return torch.stack([b[key] for b in batch])

    return {
        "images": images,
        "video_ids": video_ids,
        "activity_labels": stack_labels("activity_labels"),
        "head_pose_labels": stack_labels("head_pose_labels"),
        "assembly_labels": stack_labels("assembly_labels"),
        "error_labels": stack_labels("error_labels"),
        "phase_labels": stack_labels("phase_labels"),
    }


# ---------------------------------------------------------------------------
# EMA Shadow Model
# ---------------------------------------------------------------------------

class EMAModel:
    """
    Exponential Moving Average of model weights.
    Keeps a shadow copy that tracks the running average of model weights.

    Memory: ~320MB for 64M params (FP32) — fits comfortably with BATCH_SIZE=2.
    """
    def __init__(self, model: nn.Module, decay: float = 0.9998, warmup_steps: int = 2000):
        self.decay = decay
        self.warmup_steps = warmup_steps
        self.shadow: Dict[str, torch.Tensor] = {}
        self.step_count = 0
        self._register(model)

    def _register(self, model: nn.Module):
        for name, p in model.named_parameters():
            if p.requires_grad:
                self.shadow[name] = p.data.clone()

    def update(self, model: nn.Module):
        self.step_count += 1
        if self.step_count < self.warmup_steps:
            return  # skip updates during warmup

        decay = self.decay
        for name, p in model.named_parameters():
            if name not in self.shadow:
                continue
            self.shadow[name] = decay * self.shadow[name] + (1 - decay) * p.data

    def apply_to(self, model: nn.Module):
        """Copy EMA weights into model (for evaluation)."""
        for name, p in model.named_parameters():
            if name in self.shadow:
                p.data.copy_(self.shadow[name])


# ---------------------------------------------------------------------------
# Training Loop
# ---------------------------------------------------------------------------

def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: optim.Optimizer,
    scheduler,
    ema: Optional[EMAModel],
    scaler: GradScaler,
    device: torch.device,
    logger: logging.Logger,
    epoch: int,
    global_step: int,
    max_steps_per_epoch: Optional[int] = None,
) -> int:
    """
    Train one epoch. Returns new global_step.
    """
    model.train()

    # Loss functions
    loss_activity = LDAMLoss(num_classes=C.NUM_ACT_CLASSES, label_smoothing=C.LABEL_SMOOTHING)
    loss_pose = HeadPoseLoss(angle_weight=1.0, position_weight=0.1)
    loss_assembly = AssemblyStateLoss(label_smoothing=0.0)
    loss_error = ErrorVerificationLoss(pos_weight=3.0)
    loss_psr = PSRContrastiveLoss(temperature=0.1, margin=0.5)
    loss_multitask = MultiTaskLoss(num_tasks=5)

    total_loss = 0.0
    steps = 0
    last_heartbeat = time.time()

    optimizer.zero_grad()

    for batch_idx, batch in enumerate(dataloader):
        if max_steps_per_epoch and batch_idx >= max_steps_per_epoch:
            break

        # Move to device
        images = batch["images"].to(device)          # [B, T, C, H, W]
        B = images.shape[0]

        # Flatten temporal dimension for backbone: [B*T, C, H, W]
        images_flat = images.view(-1, C.IMG_HEIGHT, C.IMG_WIDTH)

        # Forward pass with AMP
        with autocast(dtype=torch.float16):
            outputs = model(images=images_flat, video_ids=None, clip_rgb=None)

            # Compute per-task losses
            act_logits = outputs["act_logits"]          # [B*T, 33]
            head_pose = outputs["head_pose"]             # [B*T, 6]
            as_logits = outputs["assembly_state_logits"]  # [B*T, 3]
            ev_logits = outputs["error_verification_logits"]  # [B*T, 1]
            psr_logits = outputs["psr_logits"]          # [B*T, 2]

            # Reshape labels to match flattened images
            act_lbl = batch["activity_labels"].view(-1).to(device)
            pose_lbl = batch["head_pose_labels"].view(-1, 6).to(device)
            as_lbl = batch["assembly_labels"].view(-1).to(device)
            ev_lbl = batch["error_labels"].view(-1).to(device)
            phase_lbl = batch["phase_labels"].view(-1).to(device)

            # Per-task losses
            L_act = loss_activity(act_logits, act_lbl)
            L_pose = loss_pose(head_pose, pose_lbl)
            L_as = loss_assembly(as_logits, as_lbl)
            L_ev = loss_error(ev_logits, ev_lbl)
            L_psr = loss_psr(psr_logits, phase_lbl)

            # Multi-task loss with learned uncertainty weights
            task_losses = torch.stack([L_act, L_pose, L_as, L_ev, L_psr])
            loss = loss_multitask(task_losses)

            # Scale loss for gradient accumulation
            loss = loss / C.GRAD_ACCUM_STEPS

        # Backward pass
        scaler.scale(loss).backward()

        # Gradient accumulation
        if (batch_idx + 1) % C.GRAD_ACCUM_STEPS == 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
            scheduler.step()

            # EMA update
            if ema is not None:
                ema.update(model)

            global_step += 1

        # Heartbeat logging
        if global_step % 50 == 0:
            elapsed = time.time() - last_heartbeat
            gpu_mem = torch.cuda.memory_allocated() / 1e9 if torch.cuda.is_available() else 0
            logger.info(
                f"Epoch {epoch} | Step {global_step} | "
                f"Loss: {loss.item() * C.GRAD_ACCUM_STEPS:.4f} | "
                f"GPU: {gpu_mem:.1f}GB | "
                f"Step time: {elapsed:.1f}s"
            )
            last_heartbeat = time.time()

        total_loss += loss.item() * C.GRAD_ACCUM_STEPS
        steps += 1

    return global_step


def save_checkpoint(
    model: nn.Module,
    optimizer: optim.Optimizer,
    scheduler,
    ema: Optional[EMAModel],
    epoch: int,
    global_step: int,
    checkpoint_dir: Path,
    logger: logging.Logger,
    metric: Optional[Dict] = None,
):
    """Save checkpoint — latest.pth and epoch-specific."""
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # EMA shadow state
    ema_state = {}
    if ema is not None:
        ema_state = {"shadow": ema.shadow, "step_count": ema.step_count}

    ckpt = {
        "epoch": epoch,
        "global_step": global_step,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict() if scheduler else {},
        "ema_state": ema_state,
        "metric": metric or {},
    }

    # Save latest
    latest_path = checkpoint_dir / "latest.pth"
    torch.save(ckpt, latest_path)
    logger.info(f"Checkpoint saved: {latest_path} ({latest_path.stat().st_size / 1e6:.1f} MB)")

    # Save epoch-specific
    epoch_path = checkpoint_dir / f"epoch_{epoch}.pth"
    torch.save(ckpt, epoch_path)


def load_checkpoint(
    checkpoint_path: Path,
    model: nn.Module,
    optimizer: optim.Optimizer,
    scheduler,
    ema: Optional[EMAModel],
    device: torch.device,
    logger: logging.Logger,
) -> tuple:
    """Load checkpoint. Returns (start_epoch, global_step)."""
    ckpt = torch.load(checkpoint_path, map_location=device)

    model.load_state_dict(ckpt["model_state_dict"], strict=False)
    optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    if scheduler and "scheduler_state_dict" in ckpt:
        scheduler.load_state_dict(ckpt["scheduler_state_dict"])

    # Restore EMA
    if ema is not None and "ema_state" in ckpt and ckpt["ema_state"]:
        ema.shadow = ckpt["ema_state"]["shadow"]
        ema.step_count = ckpt["ema_state"].get("step_count", 0)

    epoch = ckpt.get("epoch", 0)
    global_step = ckpt.get("global_step", 0)

    logger.info(
        f"Loaded checkpoint: epoch={epoch}, step={global_step}, "
        f"metric={ckpt.get('metric', {})}"
    )

    return epoch, global_step


# ---------------------------------------------------------------------------
# Metrics logging (JSONL — written after each epoch)
# ---------------------------------------------------------------------------

def write_metrics_jsonl(metrics: Dict, log_dir: Path, epoch: int):
    """Append epoch metrics to metrics.jsonl."""
    metrics_file = log_dir / "metrics.jsonl"
    line = json.dumps({"epoch": epoch, "step": metrics.get("global_step", 0), **metrics})
    with open(metrics_file, "a") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="POPW v2/v3 Training")
    parser.add_argument("--max_epochs", type=int, default=20,
                        help="Total epochs (default: 20)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from latest checkpoint")
    parser.add_argument("--max_steps_per_epoch", type=int, default=None,
                        help="Debug: limit steps per epoch")
    parser.add_argument("--eval_every", type=int, default=5,
                        help="Eval every N epochs (default: 5)")
    parser.add_argument("--save_every", type=int, default=5,
                        help="Save checkpoint every N epochs (default: 5)")
    parser.add_argument("--checkpoint_dir", type=str, default="./checkpoints/popw_v2",
                        help="Checkpoint directory")
    parser.add_argument("--log_dir", type=str, default="./logs/popw_v2",
                        help="Log directory")
    args = parser.parse_args()

    # Directories
    checkpoint_dir = Path(args.checkpoint_dir)
    log_dir = Path(args.log_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Logger
    logger = setup_logging(log_dir)
    logger.info("=" * 60)
    logger.info("POPW v2/v3 Training — Starting")
    logger.info(f"PyTorch: {torch.__version__}, CUDA: {torch.version.cuda}")
    logger.info(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    logger.info(f"Checkpoint dir: {checkpoint_dir}")
    logger.info(f"Log dir: {log_dir}")
    logger.info("=" * 60)

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")

    # ------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------
    logger.info("Building model...")
    model = POPWMultiTaskModel(
        pretrained=True,
        backbone_freeze_stages=[0, 1, 2],  # freeze ConvNeXt stages 0,1,2 (keep stage 3 trainable)
        use_psr_sequence_mode=False,        # enable after training validates
    )
    model = model.to(device)

    counts = count_parameters(model)
    logger.info(f"Model params: {counts['total']:,} total, {counts['total_trainable']:,} trainable")

    # ------------------------------------------------------------------
    # DataLoader — num_workers=0 (KEY FIX)
    # ------------------------------------------------------------------
    logger.info("Building DataLoader (num_workers=0 — no subprocess workers)...")
    train_dataset = SyntheticIndustRealDataset(num_samples=5000, num_frames=C.NUM_FRAMES)

    # KEY FIX: num_workers=0 eliminates subprocess workers that were causing
    # silent OOM deaths at batch ~270. With 0 workers, DataLoader runs in the
    # main process — no IPC, no semaphore issues, no hidden OOM.
    dataloader = DataLoader(
        train_dataset,
        batch_size=C.BATCH_SIZE,
        shuffle=True,
        num_workers=0,           # <-- KEY FIX: no subprocess workers
        prefetch_factor=None,    # ignored when num_workers=0
        pin_memory=False,        # not needed with num_workers=0
        collate_fn=collate_fn,
        drop_last=True,
    )
    logger.info(f"DataLoader: batch_size={C.BATCH_SIZE}, num_workers=0")

    # ------------------------------------------------------------------
    # Optimizer, Scheduler, EMA, AMP
    # ------------------------------------------------------------------
    optimizer = optim.AdamW(
        model.parameters(),
        lr=C.LR,
        weight_decay=C.WEIGHT_DECAY,
        betas=C.BETAS,
    )

    total_steps = (len(train_dataset) // C.BATCH_SIZE) * args.max_epochs
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=total_steps, eta_min=C.MIN_LR,
    )

    ema = EMAModel(model, decay=C.EMA_DECAY, warmup_steps=C.EMA_WARMUP) if C.USE_EMA else None
    scaler = GradScaler()

    # ------------------------------------------------------------------
    # Resume from checkpoint
    # ------------------------------------------------------------------
    start_epoch = 0
    global_step = 0

    if args.resume:
        latest = checkpoint_dir / "latest.pth"
        if latest.exists():
            start_epoch, global_step = load_checkpoint(
                latest, model, optimizer, scheduler, ema, device, logger
            )
            start_epoch += 1  # resume from next epoch
            logger.info(f"Resuming from epoch {start_epoch}, step {global_step}")
        else:
            logger.warning("No latest.pth found — starting from scratch")

    # ------------------------------------------------------------------
    # Signal handling — graceful shutdown
    # ------------------------------------------------------------------
    shutdown_requested = False

    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        if shutdown_requested:
            logger.warning("Force exit requested")
            sys.exit(1)
        logger.warning("Shutdown signal received — finishing epoch...")
        shutdown_requested = True

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # ------------------------------------------------------------------
    # Training Loop
    # ------------------------------------------------------------------
    logger.info(f"Starting training: epochs {start_epoch}→{args.max_epochs}")

    for epoch in range(start_epoch, args.max_epochs):
        if shutdown_requested:
            logger.info("Shutdown requested — stopping training")
            break

        logger.info(f"\n{'=' * 60}")
        logger.info(f"EPOCH {epoch + 1}/{args.max_epochs}")
        logger.info(f"{'=' * 60}")

        epoch_start = time.time()

        # Train
        global_step = train_one_epoch(
            model=model,
            dataloader=dataloader,
            optimizer=optimizer,
            scheduler=scheduler,
            ema=ema,
            scaler=scaler,
            device=device,
            logger=logger,
            epoch=epoch,
            global_step=global_step,
            max_steps_per_epoch=args.max_steps_per_epoch,
        )

        epoch_time = time.time() - epoch_start

        # Compute train loss (approx)
        logger.info(f"Epoch {epoch + 1} complete in {epoch_time:.1f}s — step={global_step}")

        # Save checkpoint
        if (epoch + 1) % args.save_every == 0 or epoch == args.max_epochs - 1:
            save_checkpoint(
                model, optimizer, scheduler, ema,
                epoch + 1, global_step, checkpoint_dir, logger,
            )

        # Write metrics (epoch-level summary)
        metrics_summary = {
            "epoch": epoch + 1,
            "global_step": global_step,
            "epoch_time_s": epoch_time,
        }
        write_metrics_jsonl(metrics_summary, log_dir, epoch + 1)

    # Final checkpoint
    save_checkpoint(
        model, optimizer, scheduler, ema,
        args.max_epochs, global_step, checkpoint_dir, logger,
    )

    logger.info("Training complete!")


if __name__ == "__main__":
    main()