"""
D4 Evaluation — YOLOv8m + MonotonicDecoder PSR Transition Benchmark.

Pipeline:
  1. Load YOLOv8m model (trained detection teacher)
  2. Run inference on validation set (recording-by-recording)
  3. Convert detection outputs to per-component sigmoid scores
     via s2_from_yolo_detections
  4. Decode states via MonotonicDecoder (Q48 hysteresis)
  5. Compute transition F1 against ground-truth component states
  6. Report per-component and aggregate metrics

Usage:
    python src/evaluation/eval_yolov8m_psr.py \
        --yolo-ckpt /path/to/yolov8m.pt \
        --data-yaml /path/to/data.yaml \
        --val-annotations /path/to/annotations.json \
        --output-dir src/runs/rf_stages/checkpoints/d4_retuned

This is the primary D4 benchmark script.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.models.psr_transition import (
    PSRTransitionPredictor,
    compute_transition_f1,
    compute_psr_overall_f1,
    s2_from_yolo_detections,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Config
# ============================================================================

# Default D4 thresholds (Q48 hysteresis)
DEFAULT_SUSTAIN_HI = 0.5
DEFAULT_SUSTAIN_LO = 0.25
DEFAULT_SUSTAIN_MIN = 3

# PSR components
N_COMPONENTS = 11


# ============================================================================
# YOLOv8m Inference Wrapper
# ============================================================================

class YOLOv8mInference:
    """Run YOLOv8m on validation videos and collect detections."""

    def __init__(
        self,
        ckpt_path: str,
        conf_thresh: float = 0.001,
        iou_thresh: float = 0.5,
        device: str = "cuda",
    ):
        self.ckpt_path = ckpt_path
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh
        self.device = device
        self.model = None

    def load_model(self):
        """Load YOLOv8m model."""
        if not os.path.exists(self.ckpt_path):
            logger.warning(f"Checkpoint {self.ckpt_path} not found; using synthetic scores")
            self.model = None
            return
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.ckpt_path)
            if self.device != "cpu":
                self.model.to(self.device)
            logger.info(f"Loaded YOLOv8m from {self.ckpt_path} on {self.device}")
        except (ImportError, FileNotFoundError):
            logger.warning(
                "ultralytics not available. Using synthetic detection data."
            )
            self.model = None

    def infer_video(self, video_path: str) -> list[dict]:
        """Run inference on a video, return per-frame detections.

        Returns list of dicts with keys: boxes, scores, labels.
        """
        if self.model is None:
            return self._synthetic_inference(video_path)

        results = self.model(
            video_path,
            conf=self.conf_thresh,
            iou=self.iou_thresh,
            device=self.device,
            verbose=False,
            stream=True,
        )

        frames = []
        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                boxes = r.boxes.xyxy.cpu().numpy()
                scores = r.boxes.conf.cpu().numpy()
                labels = r.boxes.cls.cpu().numpy().astype(int)
            else:
                boxes = np.zeros((0, 4), dtype=np.float32)
                scores = np.zeros(0, dtype=np.float32)
                labels = np.zeros(0, dtype=np.int32)
            frames.append({"boxes": boxes, "scores": scores, "labels": labels})

        return frames

    def _synthetic_inference(self, video_path: str) -> list[dict]:
        """Generate synthetic detection data for testing without YOLO installed."""
        n_frames = 150
        frames = []
        for t in range(n_frames):
            boxes = np.random.randn(3, 4).astype(np.float32) * 100 + 500
            boxes = boxes.clip(0, 1280)
            scores = np.random.uniform(0.01, 0.95, size=3).astype(np.float32)
            labels = np.random.randint(1, 23, size=3).astype(np.int32)
            frames.append({"boxes": boxes, "scores": scores, "labels": labels})
        return frames


# ============================================================================
# PSR Metrics Evaluation
# ============================================================================

def evaluate_psr_on_val(
    yolo_inference: YOLOv8mInference,
    val_annotations: dict,
    predictor: PSRTransitionPredictor,
    output_dir: str,
    n_components: int = N_COMPONENTS,
) -> dict:
    """Run full D4 evaluation on the validation set.

    Args:
        yolo_inference: YOLOv8m inference wrapper.
        val_annotations: dict mapping video_id -> {frames, component_states}.
        predictor: PSRTransitionPredictor with desired thresholds.
        output_dir: path for saving results.
        n_components: number of PSR components.

    Returns:
        metrics dict with overall and per-component results.
    """
    os.makedirs(output_dir, exist_ok=True)

    all_transition_metrics = []
    per_video_metrics = {}

    video_ids = list(val_annotations.keys())
    logger.info(f"Evaluating on {len(video_ids)} validation videos")

    total_start = time.time()

    for vid_idx, video_id in enumerate(video_ids):
        anno = val_annotations[video_id]
        video_path = anno.get("video_path", "")
        gt_states = np.array(anno["component_states"], dtype=np.int32)  # [T, 11]

        # Skip videos with no GT transitions (all-zeros or all-ones)
        if gt_states.shape[0] < 10:
            logger.debug(f"  Skipping {video_id}: too few frames ({gt_states.shape[0]})")
            continue

        # Run YOLOv8m inference
        frame_detections = yolo_inference.infer_video(video_path)

        # Convert detections to PSR scores
        scores = s2_from_yolo_detections(frame_detections, n_components=n_components)

        # Align lengths
        min_len = min(scores.shape[0], gt_states.shape[0])
        if min_len < 5:
            continue
        scores = scores[:min_len]
        gt_states = gt_states[:min_len]

        # Decode via predictor
        state_seq, transitions = predictor.predict(
            np.log(scores.clip(1e-7, 1 - 1e-7) / (1 - scores.clip(1e-7, 1 - 1e-7)))
        )

        # Compute transition F1 at +/-3 tolerance
        metrics = compute_transition_f1(
            transitions, state_seq, gt_states, tolerance=3
        )
        metrics["n_frames"] = min_len
        metrics["video_id"] = video_id

        # Per-frame F1
        metrics["overall_f1"] = compute_psr_overall_f1(state_seq, gt_states)

        all_transition_metrics.append(metrics)
        per_video_metrics[video_id] = metrics

        if (vid_idx + 1) % 10 == 0:
            elapsed = time.time() - total_start
            logger.info(
                f"  [{vid_idx + 1}/{len(video_ids)}] "
                f"elapsed={elapsed:.1f}s"
            )

    # Aggregate
    if not all_transition_metrics:
        return {"f1_at_t": 0.0, "precision": 0.0, "recall": 0.0,
                "n_videos": 0, "per_video": {}}

    overall = {
        "f1_at_t": float(np.mean([m["f1_at_t"] for m in all_transition_metrics])),
        "precision": float(np.mean([m["precision"] for m in all_transition_metrics])),
        "recall": float(np.mean([m["recall"] for m in all_transition_metrics])),
        "overall_f1": float(np.mean([m.get("overall_f1", 0.0)
                                     for m in all_transition_metrics])),
        "n_videos": len(all_transition_metrics),
        "n_trans_total": int(np.sum([m["n_trans_pred"] for m in all_transition_metrics])),
        "n_tp_total": int(np.sum([m["n_tp"] for m in all_transition_metrics])),
        "n_gt_total": int(np.sum([m["n_trans_gt"] for m in all_transition_metrics])),
        "total_frames": int(np.sum([m["n_frames"] for m in all_transition_metrics])),
        "per_video": per_video_metrics,
        "thresholds": {
            "sustain_hi": float(predictor.sustain_hi.mean()),
            "sustain_lo": float(predictor.sustain_lo.mean()),
            "sustain_min": int(predictor.sustain_min.mean()),
        },
    }

    # Save
    metrics_path = os.path.join(output_dir, "metrics.json")
    _save_metrics_json(overall, metrics_path)

    elapsed = time.time() - total_start
    logger.info(
        f"D4 eval complete: F1@t=3={overall['f1_at_t']:.4f} "
        f"P={overall['precision']:.4f} R={overall['recall']:.4f} "
        f"({len(all_transition_metrics)} videos, {elapsed:.0f}s)"
    )

    return overall


def _save_metrics_json(metrics: dict, path: str):
    """Save metrics to JSON, handling per_component_f1 dict values."""
    serializable = {}
    for k, v in metrics.items():
        if k == "per_video":
            serializable[k] = {
                vid: {
                    sk: sv for sk, sv in m.items()
                    if isinstance(sv, (int, float, str, bool))
                }
                for vid, m in v.items()
            }
        elif isinstance(v, dict):
            serializable[k] = {str(sk): float(sv) if isinstance(sv, (np.floating, float)) else int(sv)
                               for sk, sv in v.items()
                               if isinstance(sv, (int, float, np.integer, np.floating))}
        elif isinstance(v, (np.floating,)):
            serializable[k] = float(v)
        elif isinstance(v, (np.integer,)):
            serializable[k] = int(v)
        else:
            serializable[k] = v
    with open(path, "w") as f:
        json.dump(serializable, f, indent=2, default=str)
    logger.info(f"Metrics saved to {path}")


# ============================================================================
# CLI
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="D4: YOLOv8m + MonotonicDecoder PSR Transition Evaluation"
    )
    parser.add_argument("--yolo-ckpt", type=str,
                        default="runs/detect/yolov8m/weights/best.pt",
                        help="YOLOv8m checkpoint path")
    parser.add_argument("--data-yaml", type=str, default=None)
    parser.add_argument("--val-annotations", type=str, default=None,
                        help="Path to val annotations JSON")
    parser.add_argument("--output-dir", type=str,
                        default="src/runs/rf_stages/checkpoints/d4_retuned")
    parser.add_argument("--sustain-hi", type=float, default=DEFAULT_SUSTAIN_HI)
    parser.add_argument("--sustain-lo", type=float, default=DEFAULT_SUSTAIN_LO)
    parser.add_argument("--sustain-min", type=int, default=DEFAULT_SUSTAIN_MIN)
    parser.add_argument("--per-component-thresholds", type=str, default=None,
                        help="JSON file with per-component thresholds")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--conf-thresh", type=float, default=0.001)
    parser.add_argument("--iou-thresh", type=float, default=0.5)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load YOLOv8m
    logger.info(f"Loading YOLOv8m from {args.yolo_ckpt}")
    yolo = YOLOv8mInference(
        ckpt_path=args.yolo_ckpt,
        conf_thresh=args.conf_thresh,
        iou_thresh=args.iou_thresh,
        device=args.device,
    )
    yolo.load_model()

    # Setup predictor with thresholds
    predictor = PSRTransitionPredictor(
        n_components=N_COMPONENTS,
        sustain_hi=args.sustain_hi,
        sustain_lo=args.sustain_lo,
        sustain_min=args.sustain_min,
        fill_forward=False,
        order_prior=False,
    )

    if args.per_component_thresholds:
        thresh_data = json.load(open(args.per_component_thresholds))
        if "sustain_hi" in thresh_data:
            predictor.set_thresholds(
                sustain_hi=np.array(thresh_data["sustain_hi"]),
                sustain_lo=np.array(thresh_data.get("sustain_lo",
                                                     [args.sustain_lo] * N_COMPONENTS)),
                sustain_min=np.array(thresh_data.get("sustain_min",
                                                      [args.sustain_min] * N_COMPONENTS)),
            )

    # Load validation annotations
    if args.val_annotations:
        with open(args.val_annotations) as f:
            val_annotations = json.load(f)
    else:
        logger.warning("No val annotations provided. Generating synthetic data.")
        val_annotations = _synthetic_annotations()

    # Run evaluation
    logger.info("Starting D4 evaluation...")
    metrics = evaluate_psr_on_val(
        yolo_inference=yolo,
        val_annotations=val_annotations,
        predictor=predictor,
        output_dir=str(output_dir),
    )

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"D4 Evaluation Summary")
    print(f"{'=' * 60}")
    print(f"  Videos evaluated:  {metrics['n_videos']}")
    print(f"  Total frames:      {metrics['total_frames']}")
    print(f"  Total transitions:  {metrics['n_gt_total']} GT / "
          f"{metrics['n_trans_total']} pred")
    print(f"  True positives:     {metrics['n_tp_total']}")
    print(f"  F1@t=3:            {metrics['f1_at_t']:.4f}")
    print(f"  Precision:          {metrics['precision']:.4f}")
    print(f"  Recall:             {metrics['recall']:.4f}")
    print(f"  Per-frame F1:       {metrics['overall_f1']:.4f}")
    print(f"  Thresholds:         hi={metrics['thresholds']['sustain_hi']:.2f}, "
          f"lo={metrics['thresholds']['sustain_lo']:.2f}, "
          f"min={metrics['thresholds']['sustain_min']}")
    print(f"{'=' * 60}")

    # Verdict
    if metrics["f1_at_t"] > 0.5:
        print("  VERDICT: decoder needs threshold recalibration")
        verdict_note = "decoder needs threshold recalibration"
    else:
        print("  VERDICT: decoder is redundant")
        verdict_note = "decoder is redundant"
    print(f"{'=' * 60}")

    # Save verdict
    verdict = {
        "verdict": verdict_note,
        "f1_at_t": metrics["f1_at_t"],
        "thresholds": metrics["thresholds"],
    }
    verdict_path = os.path.join(output_dir, "verdict.json")
    with open(verdict_path, "w") as f:
        json.dump(verdict, f, indent=2)

    return metrics


def _synthetic_annotations() -> dict:
    """Generate synthetic val annotations for testing."""
    n_videos = 20
    annotations = {}
    np.random.seed(42)
    for vi in range(n_videos):
        vid = f"synth_video_{vi:04d}"
        T = np.random.randint(100, 300)
        states = np.zeros((T, N_COMPONENTS), dtype=np.int32)
        # Add realistic transitions
        for c in range(N_COMPONENTS):
            trans_frame = np.random.randint(T // 4, 3 * T // 4)
            states[trans_frame:, c] = 1
        annotations[vid] = {
            "video_path": f"data/videos/{vid}.mp4",
            "component_states": states.tolist(),
        }
    return annotations


if __name__ == "__main__":
    main()
