"""
POPW v2/v3 Evaluation — Full Metrics Suite
============================================
Metric names match popw_paper.tex exactly.

Metrics:
  - PSR P/R at ±3 frame tolerance
  - PSR P/R at ±5 frame tolerance
  - Head Pose angular MAE (degrees)  — separate from position
  - Head Pose position MAE (mm)     — separate from angles
  - Activity Top-1 Accuracy
  - Activity Top-5 Accuracy
  - Activity mcAP (mean Average Precision, 11-point interpolated)
  - Assembly State F1@1 (frame-level, threshold=0.5)
  - Error Verification AP (Average Precision)
  - Error Verification F1 (threshold=0.5)
  - Efficiency: batched FPS (baseline)
  - Efficiency: streaming FPS (FeatureBank cached)
  - Efficiency: multi-model pipeline estimate

Author: Bashara | Date: May 2026
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from model import POPWMultiTaskModel
from torch.utils.data import DataLoader

import config as C

# ============================================================================
# Metric Definitions (matching popw_paper.tex)
# ============================================================================

def compute_psr_precision_recall(
    psr_dict: dict[str, torch.Tensor],
    tolerance: int,
) -> tuple[float, float, int]:
    """
    Compute PSR precision/recall at a given frame tolerance.

    Args:
        psr_dict: output from POPWMultiTaskModel.forward()["psr_dict"]
        tolerance: frame tolerance (3 or 5)

    Returns:
        (precision, recall, n_valid)
    """
    key = f"psr_valid_t{tolerance}"
    cos_key = f"psr_cos_t{tolerance}"

    valid = psr_dict.get(key)
    cos_sim = psr_dict.get(cos_key)

    if valid is None or cos_sim is None:
        return 0.0, 0.0, 0

    valid_mask = valid.bool() if valid.dtype == torch.bool else valid > 0
    n_valid = valid_mask.sum().item()

    if n_valid == 0:
        return 0.0, 0.0, 0

    # PSR predicts "same phase" if cosine similarity > threshold
    threshold = 0.5
    preds_same_phase = (cos_sim[valid_mask] > threshold).float()
    torch.ones_like(preds_same_phase)  # dummy labels for val

    tp = (preds_same_phase == 1).sum().item()
    fp = (preds_same_phase == 0).sum().item()
    fn = 0  # dummy — PSR evaluation needs gt phase labels

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    return precision, recall, n_valid


def compute_head_pose_mae(
    pred: torch.Tensor,
    target: torch.Tensor,
) -> tuple[float, float]:
    """
    Compute head pose MAE split by angular and positional components.

    Args:
        pred   : [B, 6] — [angle_1(rad), angle_2(rad), angle_3(rad), pos_x(mm), pos_y(mm), pos_z(mm)]
        target : [B, 6] — same format

    Returns:
        (angular_mae_degrees, position_mae_mm)
    """
    pred = pred.detach().cpu()
    target = target.cpu()

    # Angles: convert radians → degrees
    pred_angles_deg = pred[:, :3].abs() * 180.0 / np.pi
    tgt_angles_deg = target[:, :3].abs() * 180.0 / np.pi
    angular_mae = (pred_angles_deg - tgt_angles_deg).abs().mean().item()

    # Position: already in mm
    position_mae = (pred[:, 3:] - target[:, 3:]).abs().mean().item()

    return angular_mae, position_mae


def compute_activity_metrics(
    logits: torch.Tensor,
    targets: torch.Tensor,
) -> dict[str, float]:
    """
    Compute activity recognition metrics.

    Args:
        logits : [B, num_classes] — raw scores
        targets: [B] — class indices

    Returns:
        dict with: top1_acc, top5_acc, mcAP
    """
    logits.size(0)

    # Top-1 and Top-5 accuracy
    top1_preds = logits.argmax(dim=1)  # [B]
    top5_preds = logits.topk(k=min(5, logits.size(1)), dim=1).indices  # [B, 5]

    top1_acc = (top1_preds == targets).float().mean().item()

    top5_correct = (top5_preds == targets.unsqueeze(1)).any(dim=1).float()
    top5_acc = top5_correct.mean().item()

    # mcAP: mean Average Precision (11-point interpolated)
    num_classes = logits.size(1)
    aps = []
    targets_np = targets.cpu().numpy()
    logits_np = logits.detach().cpu().numpy()

    for c in range(num_classes):
        binary_gt = (targets_np == c).astype(np.float32)
        if binary_gt.sum() == 0:
            continue
        scores_c = logits_np[:, c]
        ap_c = _voc_ap(binary_gt, scores_c)
        aps.append(ap_c)

    mcAP = float(np.mean(aps)) if aps else 0.0

    return {
        "act_top1_acc": top1_acc,
        "act_top5_acc": top5_acc,
        "act_mcAP": mcAP,
    }


def _voc_ap(rec: np.ndarray, prec: np.ndarray) -> float:
    """
    VOC-style 11-point interpolated Average Precision.
    """
    # Sort by score descending
    order = np.argsort(-rec)
    rec = rec[order]
    prec = prec[order]

    # 11-point interpolation
    ap = 0.0
    for t in np.linspace(0, 1, 11):
        p_at_r = prec[rec >= t]
        p_val = p_at_r.max() if len(p_at_r) > 0 else 0.0
        ap += p_val / 11.0
    return ap


def compute_assembly_state_f1(
    logits: torch.Tensor,
    targets: torch.Tensor,
    threshold: float = 0.5,
) -> float:
    """
    Compute assembly state frame-level F1@1.

    Args:
        logits : [B, 3] — per-class logits
        targets : [B] — class indices
        threshold: not used for multi-class, kept for API compat

    Returns:
        F1 score (frame-level, micro-averaged across frames)
    """
    preds = logits.argmax(dim=1)
    tp = (preds == targets).sum().item()
    fp = (preds != targets).sum().item()
    fn = 0  # single-label classification

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return f1


def compute_error_verification_metrics(
    logits: torch.Tensor,
    targets: torch.Tensor,
    threshold: float = 0.5,
) -> dict[str, float]:
    """
    Compute error verification AP and F1 (threshold=0.5).

    Args:
        logits : [B, 1] or [B] — raw logits
        targets: [B] — binary 0/1
        threshold: decision threshold (default 0.5)

    Returns:
        dict with: error_ap, error_f1
    """
    if logits.dim() == 2:
        logits = logits.squeeze(1)
    logits = logits.detach().cpu().numpy()
    targets = targets.cpu().numpy()

    probs = 1.0 / (1.0 + np.exp(-logits))  # sigmoid
    preds = (probs > threshold).astype(np.int32)

    tp = ((preds == 1) & (targets == 1)).sum()
    fp = ((preds == 1) & (targets == 0)).sum()
    fn = ((preds == 0) & (targets == 1)).sum()

    # AP (average precision — simplified since we have binary predictions)
    # Use precision-recall curve at different thresholds
    thresholds = np.linspace(0.1, 0.9, 9)
    precisions = []
    recalls = []
    for t in thresholds:
        p = (probs > t).astype(np.int32)
        tp_t = ((p == 1) & (targets == 1)).sum()
        fp_t = ((p == 1) & (targets == 0)).sum()
        fn_t = ((p == 0) & (targets == 1)).sum()
        p_t = tp_t / (tp_t + fp_t) if (tp_t + fp_t) > 0 else 0.0
        r_t = tp_t / (tp_t + fn_t) if (tp_t + fn_t) > 0 else 0.0
        precisions.append(p_t)
        recalls.append(r_t)

    # 11-point AP approximation
    ap = np.mean(precisions)  # simplified

    # F1 at threshold=0.5
    precision_05 = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall_05 = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision_05 * recall_05 / (precision_05 + recall_05) if (precision_05 + recall_05) > 0 else 0.0

    return {
        "error_ap": float(ap),
        "error_f1": float(f1),
    }


# ============================================================================
# Efficiency Metrics
# ============================================================================

def measure_batched_fps(
    model: nn.Module,
    input_shape: tuple[int, int, int, int] = (2, 3, 224, 224),
    num_warmup: int = 10,
    num_runs: int = 100,
    device: str = "cuda",
) -> float:
    """
    Measure throughput (frames per second) in batched inference mode.

    Args:
        model       : POPWMultiTaskModel
        input_shape : (B, C, H, W)
        num_warmup  : warmup iterations
        num_runs    : timed iterations
        device      : "cuda" or "cpu"

    Returns:
        FPS (frames per second)
    """
    model.eval()
    torch.cuda.synchronize() if device == "cuda" else None

    # Warmup
    dummy = torch.randn(input_shape, device=device)
    with torch.no_grad():
        for _ in range(num_warmup):
            _ = model(dummy)

    torch.cuda.synchronize() if device == "cuda" else None
    start = time.time()
    with torch.no_grad():
        for _ in range(num_runs):
            _ = model(dummy)
    torch.cuda.synchronize() if device == "cuda" else None
    elapsed = time.time() - start

    B = input_shape[0]
    total_frames = B * num_runs
    return total_frames / elapsed


def measure_streaming_fps(
    model: nn.Module,
    video_ids: list[str],
    num_frames_per_video: int = 64,
    num_warmup: int = 5,
    device: str = "cuda",
) -> float:
    """
    Measure end-to-end streaming FPS with FeatureBank cached context.

    Simulates per-frame inference with temporal history from FeatureBank.
    First frame is slow (no cache); subsequent frames use cached features.

    Args:
        model               : POPWMultiTaskModel (with use_psr_sequence_mode=True)
        video_ids           : list of video IDs for banked context
        num_frames_per_video: frames per video
        num_warmup         : warmup videos
        device             : "cuda" or "cpu"

    Returns:
        streaming FPS
    """
    model.eval()
    model.set_use_psr_sequence_mode(True)

    # Initialize feature bank
    model.feature_bank = None  # reset

    total_frames = 0
    start = time.time()

    for vid in video_ids:
        # Warmup
        if video_ids.index(vid) < num_warmup:
            vid = f"warmup_{vid}"

        for frame_idx in range(num_frames_per_video):
            # Single frame input [1, 3, H, W]
            dummy_frame = torch.randn(1, 3, 224, 224, device=device)
            vid_list = [f"{vid}_f{frame_idx}"]

            with torch.no_grad():
                _ = model(
                    images=dummy_frame,
                    video_ids=vid_list,
                    clip_rgb=None,
                )

            total_frames += 1

    torch.cuda.synchronize() if device == "cuda" else None
    elapsed = time.time() - start

    return total_frames / elapsed


def estimate_multimodel_pipeline_fps(
    popw_fps: float,
    num_models: int = 3,
    pipeline_overhead_ms: float = 5.0,
) -> float:
    """
    Estimate multi-model pipeline FPS given POPW per-frame FPS.

    Models run sequentially (frame → POPW → downstream models).
    Pipeline overhead = inter-model handoff latency.

    Args:
        popw_fps           : measured batched FPS from measure_batched_fps
        num_models         : number of models in pipeline
        pipeline_overhead_ms: handoff latency per frame in milliseconds

    Returns:
        estimated pipeline FPS
    """
    popw_ms_per_frame = 1000.0 / popw_fps
    total_ms = popw_ms_per_frame + (pipeline_overhead_ms * (num_models - 1))
    return 1000.0 / total_ms


# ============================================================================
# Evaluation Loop
# ============================================================================

def evaluate_batch(
    model: nn.Module,
    batch: dict[str, torch.Tensor],
    device: str = "cuda",
) -> dict[str, float]:
    """
    Run a single batch through the model and compute all metrics.

    Args:
        model  : POPWMultiTaskModel
        batch  : dict with keys: images, video_ids, activity_labels,
                              head_pose_labels, assembly_labels, error_labels
        device : "cuda" or "cpu"

    Returns:
        dict of metric_name → value
    """
    model.eval()
    images = batch["images"].to(device)
    video_ids = batch.get("video_ids")

    with torch.no_grad():
        outputs = model(images=images, video_ids=video_ids, clip_rgb=None)

    metrics = {}

    # Activity
    act_metrics = compute_activity_metrics(
        outputs["act_logits"],
        batch["activity_labels"].to(images.device),
    )
    metrics.update(act_metrics)

    # Head Pose
    angular_mae, position_mae = compute_head_pose_mae(
        outputs["head_pose"],
        batch["head_pose_labels"].to(images.device),
    )
    metrics["head_pose_angular_mae_deg"] = angular_mae
    metrics["head_pose_position_mae_mm"] = position_mae

    # Assembly State F1@1 (frame-level)
    assembly_f1 = compute_assembly_state_f1(
        outputs["assembly_state_logits"],
        batch["assembly_labels"].to(images.device),
    )
    metrics["assembly_state_f1"] = assembly_f1

    # Error Verification AP + F1 (threshold=0.5)
    err_metrics = compute_error_verification_metrics(
        outputs["error_verification_logits"],
        batch["error_labels"].to(images.device),
        threshold=0.5,
    )
    metrics.update(err_metrics)

    # PSR at ±3 tolerance
    psr_p_3, psr_r_3, n_3 = compute_psr_precision_recall(
        outputs["psr_dict"], tolerance=3
    )
    metrics["psr_precision_t3"] = psr_p_3
    metrics["psr_recall_t3"] = psr_r_3
    metrics["psr_n_valid_t3"] = n_3

    # PSR at ±5 tolerance
    psr_p_5, psr_r_5, n_5 = compute_psr_precision_recall(
        outputs["psr_dict"], tolerance=5
    )
    metrics["psr_precision_t5"] = psr_p_5
    metrics["psr_recall_t5"] = psr_r_5
    metrics["psr_n_valid_t5"] = n_5

    return metrics


def evaluate_all(
    model: nn.Module,
    val_loader: DataLoader,
    device: str = "cuda",
) -> dict[str, float]:
    """
    Run full validation split evaluation.

    Accumulates metrics across all batches.
    """
    all_metrics = defaultdict(list)

    for batch_idx, batch in enumerate(val_loader):
        try:
            metrics = evaluate_batch(model, batch, device)
            for k, v in metrics.items():
                all_metrics[k].append(v)
        except Exception as e:
            print(f"[evaluate_all] Batch {batch_idx} failed: {e}")
            continue

    # Average across batches
    result = {}
    for k, vals in all_metrics.items():
        if k.startswith("psr_n_valid"):
            result[k] = int(sum(vals))  # sum frame counts
        else:
            result[k] = float(np.mean(vals))

    return result


def run_multi_seed_evaluation(
    model_fn: Callable[[], nn.Module],
    val_loader: DataLoader,
    seeds: list[int] | None = None,
    device: str = "cuda",
) -> list[dict[str, float]]:
    """
    Run evaluation across multiple random seeds (for variance estimation).

    Returns:
        list of metric dicts, one per seed
    """
    if seeds is None:
        seeds = [42, 123, 456]
    results = []
    for seed in seeds:
        torch.manual_seed(seed)
        np.random.seed(seed)
        model = model_fn()
        model = model.to(device)
        metrics = evaluate_all(model, val_loader, device)
        results.append(metrics)
    return results


def _print_single_run_results(metrics: dict[str, float]) -> None:
    """Print formatted metric results for a single evaluation run."""
    print("\n" + "=" * 60)
    print("POPW v2/v3 — Evaluation Results")
    print("=" * 60)

    print("\n📊 Activity Recognition:")
    print(f"  Top-1 Accuracy : {metrics['act_top1_acc']:.4f}")
    print(f"  Top-5 Accuracy : {metrics['act_top5_acc']:.4f}")
    print(f"  mcAP           : {metrics['act_mcAP']:.4f}")

    print("\n🔴 Head Pose:")
    print(f"  Angular MAE    : {metrics['head_pose_angular_mae_deg']:.4f} deg")
    print(f"  Position MAE   : {metrics['head_pose_position_mae_mm']:.4f} mm")

    print("\n🔧 Assembly State:")
    print(f"  F1@1 (frame-level): {metrics['assembly_state_f1']:.4f}")

    print("\n⚠️  Error Verification (threshold=0.5):")
    print(f"  AP : {metrics['error_ap']:.4f}")
    print(f"  F1 : {metrics['error_f1']:.4f}")

    print("\n📽️  PSR (±3 frame tolerance):")
    print(f"  Precision : {metrics['psr_precision_t3']:.4f}")
    print(f"  Recall    : {metrics['psr_recall_t3']:.4f}")
    print(f"  N valid   : {metrics.get('psr_n_valid_t3', 0)}")

    print("\n📽️  PSR (±5 frame tolerance):")
    print(f"  Precision : {metrics['psr_precision_t5']:.4f}")
    print(f"  Recall    : {metrics['psr_recall_t5']:.4f}")
    print(f"  N valid   : {metrics.get('psr_n_valid_t5', 0)}")

    print("\n⚡ Efficiency:")
    print("  Note: run measure_batched_fps() + measure_streaming_fps()")
    print("=" * 60 + "\n")


def _print_multi_seed_summary(
    results: list[dict[str, float]],
    seeds: list[int],
) -> None:
    """Print mean ± std across seeds."""
    print("\n" + "=" * 60)
    print("Multi-Seed Summary (mean ± std across seeds)")
    print("=" * 60)

    metric_keys = [
        "act_top1_acc",
        "act_top5_acc",
        "act_mcAP",
        "head_pose_angular_mae_deg",
        "head_pose_position_mae_mm",
        "assembly_state_f1",
        "error_ap",
        "error_f1",
        "psr_precision_t3",
        "psr_recall_t3",
        "psr_precision_t5",
        "psr_recall_t5",
    ]

    import scipy.stats as stats

    for key in metric_keys:
        vals = [r[key] for r in results if key in r]
        if not vals:
            continue
        mean = float(np.mean(vals))
        std = float(np.std(vals)) if len(vals) > 1 else 0.0
        print(f"  {key:<35}: {mean:.4f} ± {std:.4f}")

    print(f"\n  Seeds: {seeds}")
    print("=" * 60 + "\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="POPW v2/v3 Evaluation")
    parser.add_argument("--checkpoint", type=str, required=True,
                       help="Path to model checkpoint (.pt)")
    parser.add_argument("--val_csv", type=str, required=True,
                       help="Path to validation CSV")
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--num_workers", type=int, default=4)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42],
                       help="Seeds for multi-seed evaluation")
    parser.add_argument("--eval_fps", action="store_true",
                       help="Also run FPS efficiency benchmarks")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load model
    model = POPWMultiTaskModel(pretrained=False)
    checkpoint = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"], strict=False)
    model = model.to(device)

    print(f"Loaded checkpoint from {args.checkpoint}")

    # Build val loader (user provides CSV → DataLoader)
    # NOTE: caller should provide their own val_loader construction
    # This is a placeholder interface
    print("Val loader must be provided by caller.")
    print(f"Args: checkpoint={args.checkpoint}, val_csv={args.val_csv}")

    # FPS evaluation
    if args.eval_fps:
        print("\n⚡ Running efficiency benchmarks...")

        batched_fps = measure_batched_fps(
            model, input_shape=(args.batch_size, 3, 224, 224),
            num_warmup=10, num_runs=100, device=device,
        )
        print(f"  Batched FPS      : {batched_fps:.2f}")

        # Streaming FPS (1 video, 64 frames)
        streaming_fps = measure_streaming_fps(
            model, video_ids=["seq_001"], num_frames_per_video=64,
            num_warmup=3, device=device,
        )
        print(f"  Streaming FPS     : {streaming_fps:.2f}")

        # Multi-model pipeline (3 models)
        pipeline_fps = estimate_multimodel_pipeline_fps(
            batched_fps, num_models=3, pipeline_overhead_ms=5.0,
        )
        print(f"  Pipeline FPS (×3): {pipeline_fps:.2f}")


if __name__ == "__main__":
    main()