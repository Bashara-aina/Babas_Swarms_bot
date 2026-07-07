"""
Compute MonotonicDecoder oracle bound (CPU-only, OOM-safe).

Feed GT fill-forward binary state sequences directly to MonotonicDecoder
to measure the decoder's theoretical upper bound on transition F1.

Two modes:
  - Sustained (procedure_order=True, sustain_min=3): full decoder with
    hardcoded sequential component ordering (comp0 before comp1, etc.)
  - Relaxed (procedure_order=False): hysteresis only, no ordering constraint

Opus 141 Q46 reference: "decoder isn't the bottleneck" test.

OOM safeguard: pure numpy, no GPU, no forward pass needed. Works while
both GPUs are busy with training.
"""

from __future__ import annotations

import json
import csv
from collections import defaultdict
from pathlib import Path
from typing import Optional

import numpy as np


# Recording root — all 16 val recordings with PSR_labels_raw.csv
RECORDINGS_VAL = Path("/media/newadmin/master/POPW/datasets/industreal/recordings/val")


# ============================================================================
# MonotonicDecoder — pure numpy, matches src/models/psr_transition.py logic
# ============================================================================

class MonotonicDecoder:
    """Decode per-component sigmoid scores into monotone state sequences.

    Hysteresis parameters (per component):
        sustain_hi  : score above which state is forced to 1
        sustain_lo  : score below which state is forced to 0
        sustain_min : minimum frames a state must persist

    For oracle computation, GT binary values are 0 or 1. Since 0 < sustain_lo
    and 1 > sustain_hi, the only constraint that can degrade F1 is sustain_min
    (rapid GT transitions get suppressed) and procedure-order (components
    transition out of hardcoded order).
    """

    def __init__(
        self,
        sustain_hi: float = 0.5,
        sustain_lo: float = 0.3,
        sustain_min: int = 3,
    ):
        if sustain_lo >= sustain_hi:
            raise ValueError(
                f"sustain_lo ({sustain_lo}) must be < sustain_hi ({sustain_hi})"
            )
        if sustain_min < 1:
            raise ValueError(f"sustain_min ({sustain_min}) must be >= 1")

        self.sustain_hi = sustain_hi
        self.sustain_lo = sustain_lo
        self.sustain_min = sustain_min

    def decode(self, scores: np.ndarray) -> tuple[np.ndarray, list[int]]:
        """Decode a 1-D score sequence into binary states.

        Args:
            scores: [T] float array of sigmoid scores in [0, 1].

        Returns:
            state_seq: [T] binary array (0 or 1).
            transitions: list of frame indices where 0->1 occurs.
        """
        T = len(scores)
        state = np.zeros(T, dtype=np.int32)
        trans: list[int] = []
        last_flip = -self.sustain_min  # allow immediate first flip

        for t in range(T):
            s = scores[t]

            if s > self.sustain_hi:
                desired = 1
            elif s < self.sustain_lo:
                desired = 0
            else:
                # hysteresis band — keep previous if sustain has not expired
                if t == 0:
                    desired = 0
                else:
                    desired = int(state[t - 1])

            # enforce minimum sustain
            prev_state = int(state[t - 1]) if t > 0 else 0
            if desired != prev_state:
                if t - last_flip < self.sustain_min:
                    desired = prev_state  # suppress transition
                else:
                    last_flip = t
                    if desired == 1:
                        trans.append(t)

            state[t] = desired

        return state, trans


# ============================================================================
# Data loading
# ============================================================================

def count_frames(rec_dir: Path) -> int:
    """Count frames in a recording's rgb directory."""
    rgb_dir = rec_dir / "rgb"
    if not rgb_dir.exists():
        return 0
    return len(list(rgb_dir.glob("*.jpg")))


def load_psr_labels(rec_dir: Path, num_frames: int) -> np.ndarray:
    """Load and fill-forward PSR labels for a recording.

    Matches the dataset's _parse_psr_raw() logic.
    Returns [num_frames, 11] float32 array with values 0.0 or 1.0.
    """
    psr_file = rec_dir / "PSR_labels_raw.csv"
    if not psr_file.exists():
        return np.zeros((num_frames, 11), dtype=np.float32)

    sparse: list[tuple[int, np.ndarray]] = []
    with open(psr_file, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 12:
                continue
            try:
                frame_num = int(Path(row[0]).stem)
                values = np.array(
                    [float(v) for v in row[1:12]], dtype=np.float32
                )
                sparse.append((frame_num, values))
            except (ValueError, IndexError):
                continue

    if not sparse:
        return np.zeros((num_frames, 11), dtype=np.float32)

    sparse.sort(key=lambda x: x[0])

    dense = np.zeros((num_frames, 11), dtype=np.float32)
    last_valid = np.zeros(11, dtype=np.int64)
    sparse_idx = 0
    for frame in range(num_frames):
        if sparse_idx < len(sparse) and frame == sparse[sparse_idx][0]:
            new_vals = sparse[sparse_idx][1].copy()
            sparse_idx += 1
            valid_mask = new_vals >= 0
            last_valid[valid_mask] = new_vals[valid_mask]
        dense[frame] = last_valid.copy()

    return dense


# ============================================================================
# Oracle decoding
# ============================================================================

def decode_oracle_states(
    gt_states: np.ndarray,
    sustain_hi: float = 0.5,
    sustain_lo: float = 0.3,
    sustain_min: int = 3,
    procedure_order: bool = True,
) -> np.ndarray:
    """Decode GT states through MonotonicDecoder to get oracle state sequence.

    GT binary values (0 or 1) are fed as scores. Since 0 < sustain_lo and
    1 > sustain_hi, the only suppression comes from sustain_min and
    procedure-order constraints.

    With procedure_order=True, components must fire in sequential order
    (comp0 before comp1 before comp2 ...). This is the "sustained" mode.

    With procedure_order=False, each component is decoded independently
    with only hysteresis applied. This is the "relaxed" mode.

    Args:
        gt_states: [T, 11] binary fill-forward GT states (0 or 1).
        sustain_hi: hysteresis high threshold.
        sustain_lo: hysteresis low threshold.
        sustain_min: minimum sustain frames.
        procedure_order: if True, enforce sequential component ordering.

    Returns:
        pred_states: [T, 11] decoded binary states.
    """
    T, C = gt_states.shape
    pred_states = np.zeros((T, C), dtype=np.int32)

    if procedure_order:
        # Sequential procedure order: fire comp0 first, then comp1, etc.
        # Each component's GT scores are only available after its predecessor
        # has fired. Before that, the component's score is forced to 0
        # (it cannot transition because the order constraint blocks it).

        # Pre-initialize: components already ON at frame 0 stay ON.
        # For components OFF at frame 0, the oracle GT score is their true
        # label. With procedure order, they can only transition after their
        # predecessor has transitioned.

        # We process components in order and apply the constraint:
        #   comp c can only fire at frame t if comp c-1 has fired before or at t.

        # The approach: for each component c, create a masked score where
        #   - frames before comp c-1 fires get score 0 (cannot transition)
        #   - frames after get the true GT score

        # We use the "order frame" technique: compute the frame at which
        # the predecessor transitions, and mask all earlier frames.

        pred_states = _decode_with_order_constraint(
            gt_states, sustain_hi, sustain_lo, sustain_min
        )
    else:
        # Independent decoding per component
        decoder = MonotonicDecoder(
            sustain_hi=sustain_hi,
            sustain_lo=sustain_lo,
            sustain_min=sustain_min,
        )
        for c in range(C):
            scores = gt_states[:, c].copy()
            # Pre-initialize: if GT starts at 1 at frame 0, set first
            # sustain_min frames to 1 so the decoder's sustain counter doesn't
            # delay the transition
            if gt_states[0, c] > 0.5:
                # Already ON at frame 0 — ensure decoder starts in state 1
                # by providing strong evidence for the first sustain_min frames
                scores[:sustain_min] = np.maximum(scores[:sustain_min], 1.0)

            # Decode but handle the init: we need the decoder to know
            # that frame 0 state should be 1 if GT[0] = 1.
            # The simplest approach: set sustain_min frames to 1 and run
            # the decoder normally.
            st, _ = decoder.decode(scores)
            pred_states[:, c] = st

        # However, the above has a subtle issue: the decoder's sustain_min
        # starts counting from frame 0. If GT[0] = 1, the first sustain_min
        # frames should all be 1. But the decoder starts with state 0 and
        # needs sustain_min frames of evidence to transition to 1.

        # Fix: after decoding, if GT[0, c] = 1, ensure the first
        # sustain_min frames are also 1 in the output.
        for c in range(C):
            if gt_states[0, c] > 0.5:
                pred_states[:sustain_min, c] = 1
                # Also back-fill: the decoder might have transitioned later
                # than frame 0. We need the transition to be at or before
                # the true GT transition.
                # Find the first GT transition for this component
                gt_diff = np.diff(gt_states[:, c], prepend=0)
                first_trans = np.where(gt_diff > 0.5)[0]
                if len(first_trans) > 0:
                    first_gt = first_trans[0]
                    # The decoder should fire by first_gt at the latest
                    # Ensure pred_states[:first_gt+1, c] is correct
                    # by re-decoding with a leading 1.0 sequence
                    pass  # We'll handle this in the main function

    return pred_states


def _decode_with_order_constraint(
    gt_states: np.ndarray,
    sustain_hi: float = 0.5,
    sustain_lo: float = 0.3,
    sustain_min: int = 3,
) -> np.ndarray:
    """Decode with sequential procedure-order constraint.

    Components fire in order: comp0, then comp1, ..., then comp10.
    Each component c can only fire after comp c-1 has fired.
    """
    T, C = gt_states.shape
    pred = np.zeros((T, C), dtype=np.int32)
    decoder = MonotonicDecoder(
        sustain_hi=sustain_hi, sustain_lo=sustain_lo, sustain_min=sustain_min
    )

    # Track when each component fires (first frame of state=1)
    first_fire = np.full(C, T + 1, dtype=np.int32)  # default: never fired

    for c in range(C):
        # Build oracle scores for this component:
        # - If GT starts at 1 at frame 0, pre-init: provide strong evidence
        #   from frame 0 so decoder transitions immediately
        scores = np.zeros(T, dtype=np.float32)

        # Fill in GT scores at transition points
        gt_diff = np.diff(gt_states[:, c], prepend=0)
        trans_frames = np.where(gt_diff > 0.5)[0]

        # Pre-init: if already ON at frame 0
        if gt_states[0, c] > 0.5:
            # Provide sustain_min frames of 1.0 evidence starting frame 0
            scores[:min(sustain_min, T)] = 1.0
            first_fire[c] = 0
        else:
            # Provide 1.0 at each transition frame and sustain_min-1 following
            for tf in trans_frames:
                for offset in range(sustain_min):
                    frame = tf + offset
                    if frame < T:
                        scores[frame] = 1.0

        # Before predecessor fires, suppress scores to 0
        if c > 0:
            predecessor_fire = first_fire[c - 1]
            if predecessor_fire < T:
                # Zero out scores before predecessor fires
                scores[:predecessor_fire] = 0.0
                # After predecessor fires, the GT score can take effect
            else:
                # Predecessor never fired — component can never transition
                scores[:] = 0.0

        # Decode
        st, tr = decoder.decode(scores)
        pred[:, c] = st

        # Record first fire frame
        if len(tr) > 0:
            first_fire[c] = tr[0]
        elif gt_states[0, c] > 0.5:
            first_fire[c] = 0
        # else: never fired

    return pred


def decode_relaxed(
    gt_states: np.ndarray,
    sustain_hi: float = 0.5,
    sustain_lo: float = 0.3,
    sustain_min: int = 3,
) -> np.ndarray:
    """Decode with no ordering constraint — only hysteresis.

    Each component is decoded independently. Components already ON at
    frame 0 get pre-initialized.
    """
    T, C = gt_states.shape
    pred = np.zeros((T, C), dtype=np.int32)
    decoder = MonotonicDecoder(
        sustain_hi=sustain_hi, sustain_lo=sustain_lo, sustain_min=sustain_min
    )

    for c in range(C):
        # Build oracle scores
        scores = np.zeros(T, dtype=np.float32)

        # Pre-init: if GT starts at 1 at frame 0, provide evidence
        if gt_states[0, c] > 0.5:
            scores[:min(sustain_min, T)] = 1.0
        else:
            # Provide evidence at transition frames
            gt_diff = np.diff(gt_states[:, c], prepend=0)
            trans_frames = np.where(gt_diff > 0.5)[0]
            for tf in trans_frames:
                for offset in range(sustain_min):
                    frame = tf + offset
                    if frame < T:
                        scores[frame] = 1.0

        # For components that never transition in GT, ensure they stay 0
        # (already zero-initialized)

        st, tr = decoder.decode(scores)
        pred[:, c] = st

    return pred


# ============================================================================
# Metrics
# ============================================================================

def compute_transition_f1(
    pred_states: np.ndarray,
    gt_states: np.ndarray,
    tolerance: int = 3,
) -> dict:
    """Compute per-component and aggregate transition F1.

    Transition F1 matches the B3/STORM protocol: greedy bi-directional
    matching within +/- tolerance frames.
    """
    # Extract transition events (0->1)
    pred_tr = np.clip(pred_states[1:] - pred_states[:-1], a_min=0, a_max=None)
    gt_tr = np.clip(gt_states[1:] - gt_states[:-1], a_min=0, a_max=None)

    C = pred_states.shape[1]
    per_comp = {}
    all_tp = 0
    all_fp = 0
    all_fn = 0

    for c in range(C):
        p_frames = set(np.where(pred_tr[:, c] > 0.5)[0])
        g_frames = set(np.where(gt_tr[:, c] > 0.5)[0])

        if not p_frames and not g_frames:
            per_comp[c] = 1.0  # perfect agreement on no transitions
            continue

        # Greedy bi-directional matching
        g_list = sorted(g_frames)
        p_list = sorted(p_frames)
        g_matched = [False] * len(g_list)
        p_matched = [False] * len(p_list)

        for pi, pf in enumerate(p_list):
            best_dist = tolerance + 1
            best_gi = -1
            for gi, gf in enumerate(g_list):
                if g_matched[gi]:
                    continue
                dist = abs(pf - gf)
                if dist < best_dist:
                    best_dist = dist
                    best_gi = gi
            if best_gi >= 0:
                g_matched[best_gi] = True
                p_matched[pi] = True

        tp = sum(g_matched)
        fp = len(p_list) - tp
        fn = len(g_list) - tp

        all_tp += tp
        all_fp += fp
        all_fn += fn

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * prec * rec / (prec + rec)
            if (prec + rec) > 0
            else 0.0
        )
        per_comp[c] = f1

    # Macro F1
    macro_f1 = float(np.mean(list(per_comp.values()))) if per_comp else 0.0

    # Micro F1
    micro_prec = all_tp / (all_tp + all_fp) if (all_tp + all_fp) > 0 else 0.0
    micro_rec = all_tp / (all_tp + all_fn) if (all_tp + all_fn) > 0 else 0.0
    micro_f1 = (
        2 * micro_prec * micro_rec / (micro_prec + micro_rec)
        if (micro_prec + micro_rec) > 0
        else 0.0
    )

    return {
        "per_component_f1": {str(c): float(v) for c, v in per_comp.items()},
        "macro_f1": macro_f1,
        "micro_f1": float(micro_f1),
        "micro_precision": float(micro_prec),
        "micro_recall": float(micro_rec),
        "n_tp": all_tp,
        "n_fp": all_fp,
        "n_fn": all_fn,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    import sys

    # Output directory
    save_dir = Path(
        "src/runs/rf_stages/checkpoints/decoder_oracle_cpu"
    )
    save_dir.mkdir(parents=True, exist_ok=True)

    tolerance = 3
    sustain_hi = 0.5
    sustain_lo = 0.3
    sustain_min = 3

    print("=" * 60)
    print("MonotonicDecoder Oracle Bound (CPU-only, OOM-safe)")
    print("Opus 141 Q46 — decoder-is-bottleneck test")
    print("=" * 60)
    print(f"  sustain_hi={sustain_hi}, sustain_lo={sustain_lo}, sustain_min={sustain_min}")
    print(f"  tolerance=+/-{tolerance} frames")
    print(f"  Device: CPU (no GPU needed)")

    # Discover val recordings
    recordings_root = RECORDINGS_VAL
    if not recordings_root.exists():
        print(f"ERROR: recordings root not found: {recordings_root}")
        sys.exit(1)

    rec_ids = sorted(
        [d.name for d in recordings_root.iterdir() if d.is_dir()]
    )
    # Filter to only directories with PSR_labels_raw.csv
    rec_ids = [
        r for r in rec_ids
        if (recordings_root / r / "PSR_labels_raw.csv").exists()
    ]
    print(f"\nFound {len(rec_ids)} val recordings with PSR labels")
    for r in rec_ids:
        print(f"  - {r}")

    # ==================================================================
    # Run sustained oracle (procedure_order=True)
    # ==================================================================
    print(f"\n{'=' * 60}")
    print("SUSTAINED ORACLE (procedure_order=True, sustain_min=3)")
    print(f"{'=' * 60}")

    sustained_per_rec = {}
    n_total_frames = 0
    total_gt_trans = 0
    total_pred_trans = 0

    for rec_id in rec_ids:
        rec_dir = recordings_root / rec_id
        num_frames = count_frames(rec_dir)
        if num_frames == 0:
            print(f"  WARNING: {rec_id} has 0 frames, skipping")
            continue

        gt_states = load_psr_labels(rec_dir, num_frames)
        gt_bin = (gt_states > 0.5).astype(np.float32)
        n_total_frames += num_frames

        # Decode with procedure-order constraint
        pred_states = _decode_with_order_constraint(
            gt_bin,
            sustain_hi=sustain_hi,
            sustain_lo=sustain_lo,
            sustain_min=sustain_min,
        )

        # Compute metrics
        gt_tr = np.clip(gt_bin[1:] - gt_bin[:-1], a_min=0, a_max=None)
        pred_tr = np.clip(pred_states[1:] - pred_states[:-1], a_min=0, a_max=None)
        n_gt = int(gt_tr.sum())
        n_pred = int(pred_tr.sum())
        total_gt_trans += n_gt
        total_pred_trans += n_pred

        f1 = compute_transition_f1(pred_states, gt_bin, tolerance=tolerance)

        # Delay analysis
        gt_diff = np.clip(gt_bin[1:] - gt_bin[:-1], a_min=0, a_max=None)
        pred_diff = np.clip(pred_states[1:] - pred_states[:-1], a_min=0, a_max=None)
        delays = []
        for c in range(11):
            g_frames = set(np.where(gt_diff[:, c] > 0.5)[0])
            p_frames = set(np.where(pred_diff[:, c] > 0.5)[0])
            matched_g = set()
            for pf in sorted(p_frames):
                best_gf = None
                best_dist = tolerance + 1
                for gf in sorted(g_frames):
                    if gf not in matched_g and abs(pf - gf) <= tolerance:
                        if best_gf is None or abs(pf - gf) < best_dist:
                            best_gf = gf
                            best_dist = abs(pf - gf)
                if best_gf is not None:
                    matched_g.add(best_gf)
                    delays.append(int(pf - best_gf))

        delay_stats = {}
        if delays:
            delay_stats = {
                "mean": float(np.mean(delays)),
                "median": float(np.median(delays)),
                "std": float(np.std(delays)),
                "min": int(min(delays)),
                "max": int(max(delays)),
                "p90": float(np.percentile(delays, 90)),
                "n": len(delays),
            }

        sustained_per_rec[rec_id] = {
            "num_frames": num_frames,
            "n_gt_transitions": int(n_gt),
            "n_pred_transitions": int(n_pred),
            "component_f1": f1["per_component_f1"],
            "macro_f1": f1["macro_f1"],
            "micro_f1": f1["micro_f1"],
            "delay_stats": delay_stats,
        }

        print(
            f"  {rec_id}: {num_frames:5d}f, "
            f"GT={n_gt:2d}t, Pred={n_pred:2d}, "
            f"macro={f1['macro_f1']:.4f}, micro={f1['micro_f1']:.4f}"
        )

    # Aggregate sustained
    sustained_macro = float(
        np.mean([r["macro_f1"] for r in sustained_per_rec.values()])
    )
    sustained_micro = float(
        np.mean([r["micro_f1"] for r in sustained_per_rec.values()])
    )

    # Per-component sustained across recordings
    per_comp_sustained = defaultdict(list)
    for rec_data in sustained_per_rec.values():
        for c_str, f1v in rec_data["component_f1"].items():
            per_comp_sustained[c_str].append(f1v)

    sustained_per_component = {}
    for c_str in sorted(per_comp_sustained.keys(), key=int):
        vals = per_comp_sustained[c_str]
        sustained_per_component[c_str] = {
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
        }

    print(
        f"\n  SUSTAINED MACRO-F1: {sustained_macro:.4f}"
        f"  (across {len(sustained_per_rec)} recordings)"
    )

    # ==================================================================
    # Run relaxed oracle (procedure_order=False)
    # ==================================================================
    print(f"\n{'=' * 60}")
    print("RELAXED ORACLE (procedure_order=False)")
    print(f"{'=' * 60}")

    relaxed_per_rec = {}
    total_gt_trans_r = 0
    total_pred_trans_r = 0

    for rec_id in rec_ids:
        rec_dir = recordings_root / rec_id
        num_frames = count_frames(rec_dir)
        if num_frames == 0:
            continue

        gt_states = load_psr_labels(rec_dir, num_frames)
        gt_bin = (gt_states > 0.5).astype(np.float32)

        # Decode without procedure-order constraint
        pred_states = decode_relaxed(
            gt_bin,
            sustain_hi=sustain_hi,
            sustain_lo=sustain_lo,
            sustain_min=sustain_min,
        )

        # Compute metrics
        gt_tr = np.clip(gt_bin[1:] - gt_bin[:-1], a_min=0, a_max=None)
        pred_tr = np.clip(pred_states[1:] - pred_states[:-1], a_min=0, a_max=None)
        n_gt = int(gt_tr.sum())
        n_pred = int(pred_tr.sum())
        total_gt_trans_r += n_gt
        total_pred_trans_r += n_pred

        f1 = compute_transition_f1(pred_states, gt_bin, tolerance=tolerance)

        # Delay analysis
        gt_diff = np.clip(gt_bin[1:] - gt_bin[:-1], a_min=0, a_max=None)
        pred_diff = np.clip(pred_states[1:] - pred_states[:-1], a_min=0, a_max=None)
        delays = []
        for c in range(11):
            g_frames = set(np.where(gt_diff[:, c] > 0.5)[0])
            p_frames = set(np.where(pred_diff[:, c] > 0.5)[0])
            matched_g = set()
            for pf in sorted(p_frames):
                best_gf = None
                best_dist = tolerance + 1
                for gf in sorted(g_frames):
                    if gf not in matched_g and abs(pf - gf) <= tolerance:
                        if best_gf is None or abs(pf - gf) < best_dist:
                            best_gf = gf
                            best_dist = abs(pf - gf)
                if best_gf is not None:
                    matched_g.add(best_gf)
                    delays.append(int(pf - best_gf))

        delay_stats = {}
        if delays:
            delay_stats = {
                "mean": float(np.mean(delays)),
                "median": float(np.median(delays)),
                "std": float(np.std(delays)),
                "min": int(min(delays)),
                "max": int(max(delays)),
                "p90": float(np.percentile(delays, 90)),
                "n": len(delays),
            }

        relaxed_per_rec[rec_id] = {
            "num_frames": num_frames,
            "n_gt_transitions": int(n_gt),
            "n_pred_transitions": int(n_pred),
            "component_f1": f1["per_component_f1"],
            "macro_f1": f1["macro_f1"],
            "micro_f1": f1["micro_f1"],
            "delay_stats": delay_stats,
        }

        print(
            f"  {rec_id}: {num_frames:5d}f, "
            f"GT={n_gt:2d}t, Pred={n_pred:2d}, "
            f"macro={f1['macro_f1']:.4f}, micro={f1['micro_f1']:.4f}"
        )

    # Aggregate relaxed
    relaxed_macro = float(
        np.mean([r["macro_f1"] for r in relaxed_per_rec.values()])
    )
    relaxed_micro = float(
        np.mean([r["micro_f1"] for r in relaxed_per_rec.values()])
    )

    # Per-component relaxed across recordings
    per_comp_relaxed = defaultdict(list)
    for rec_data in relaxed_per_rec.values():
        for c_str, f1v in rec_data["component_f1"].items():
            per_comp_relaxed[c_str].append(f1v)

    relaxed_per_component = {}
    for c_str in sorted(per_comp_relaxed.keys(), key=int):
        vals = per_comp_relaxed[c_str]
        relaxed_per_component[c_str] = {
            "mean": float(np.mean(vals)),
            "std": float(np.std(vals)),
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
        }

    print(
        f"\n  RELAXED MACRO-F1: {relaxed_macro:.4f}"
        f"  (across {len(relaxed_per_rec)} recordings)"
    )

    # ==================================================================
    # Comparison with Agent-25 (GPU) result
    # ==================================================================
    print(f"\n{'=' * 60}")
    print("VERIFICATION vs Agent-25 (GPU)")
    print(f"{'=' * 60}")

    agent25_sustained = 0.5947
    agent25_relaxed = 0.8750

    sustained_diff = sustained_macro - agent25_sustained
    relaxed_diff = relaxed_macro - agent25_relaxed

    print(f"  Sustained: CPU={sustained_macro:.4f}, GPU={agent25_sustained:.4f}, "
          f"diff={sustained_diff:+.4f}")
    print(f"  Relaxed:   CPU={relaxed_macro:.4f}, GPU={agent25_relaxed:.4f}, "
          f"diff={relaxed_diff:+.4f}")

    match = (abs(sustained_diff) < 0.01) and (abs(relaxed_diff) < 0.01)
    if match:
        print(f"\n  RESULT: VERIFIED ✓ — CPU oracle matches GPU result within 0.01")
    else:
        print(
            f"\n  RESULT: DIFFERS — see analysis above. "
            f"The numpy decoder implementation diverges from the "
            f"torch-based decoder used by Agent-25."
        )

    # ==================================================================
    # Build results dict
    # ==================================================================
    results = {
        "description": (
            "MonotonicDecoder Oracle Bound (Opus 141 Q46), CPU-only, OOM-safe. "
            "Oracle F1 = decoder F1 when fed perfect GT transition logits. "
            "This is the theoretical upper bound of the decoder."
        ),
        "device": "cpu",
        "config": {
            "tolerance": tolerance,
            "num_components": 11,
            "sustain_hi": sustain_hi,
            "sustain_lo": sustain_lo,
            "sustain_min": sustain_min,
        },
        "sustained": {
            "description": (
                "procedure_order=True, sustain_min=3. "
                "Full decoder with hardcoded sequential ordering constraint."
            ),
            "n_recordings": len(sustained_per_rec),
            "n_total_frames": n_total_frames,
            "n_total_gt_transitions": total_gt_trans,
            "n_total_pred_transitions": total_pred_trans,
            "oracle_macro_f1": sustained_macro,
            "oracle_micro_f1": sustained_micro,
            "per_component_oracle_f1": sustained_per_component,
            "per_recording": {k: sustained_per_rec[k] for k in sorted(sustained_per_rec.keys())},
        },
        "relaxed": {
            "description": (
                "procedure_order=False. "
                "Hysteresis only, no ordering constraint."
            ),
            "n_recordings": len(relaxed_per_rec),
            "n_total_frames": n_total_frames,
            "n_total_gt_transitions": total_gt_trans_r,
            "n_total_pred_transitions": total_pred_trans_r,
            "oracle_macro_f1": relaxed_macro,
            "oracle_micro_f1": relaxed_micro,
            "per_component_oracle_f1": relaxed_per_component,
            "per_recording": {k: relaxed_per_rec[k] for k in sorted(relaxed_per_rec.keys())},
        },
        "agent25_comparison": {
            "agent25_device": "gpu",
            "agent25_sustained_macro_f1": agent25_sustained,
            "agent25_relaxed_macro_f1": agent25_relaxed,
            "cpu_sustained_macro_f1": sustained_macro,
            "cpu_relaxed_macro_f1": relaxed_macro,
            "sustained_diff": round(sustained_diff, 4),
            "relaxed_diff": round(relaxed_diff, 4),
            "verified": match,
        },
        "agent25_source": "src/runs/rf_stages/checkpoints/decoder_oracle_bound/",
    }

    # ==================================================================
    # Save JSON
    # ==================================================================
    json_path = save_dir / "oracle_f1.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nJSON saved to {json_path}")

    # ==================================================================
    # Save Markdown report
    # ==================================================================
    # Interpretation
    sustained_interp = ""
    if sustained_macro >= 0.95:
        sustained_interp = (
            f"**Sustained Oracle Macro F1 = {sustained_macro:.4f} >= 0.95.** "
            f"The decoder is NOT the bottleneck (with ordering). Upstream "
            f"transition prediction is the binding constraint."
        )
    elif sustained_macro >= 0.85:
        sustained_interp = (
            f"**Sustained Oracle Macro F1 = {sustained_macro:.4f} (0.85-0.95).** "
            f"The decoder imposes moderate constraints with ordering. Some "
            f"headroom from upstream, but decoder changes could help."
        )
    else:
        sustained_interp = (
            f"**Sustained Oracle Macro F1 = {sustained_macro:.4f} < 0.85.** "
            f"The decoder IS a significant bottleneck when procedure order "
            f"is enforced. The hardcoded sequential chain (comp0->comp10) "
            f"suppresses many valid GT transitions."
        )

    relaxed_interp = ""
    if relaxed_macro >= 0.95:
        relaxed_interp = (
            f"**Relaxed Oracle Macro F1 = {relaxed_macro:.4f} >= 0.95.** "
            f"Without ordering constraints, hysteresis alone is nearly lossless."
        )
    elif relaxed_macro >= 0.85:
        relaxed_interp = (
            f"**Relaxed Oracle Macro F1 = {relaxed_macro:.4f} (0.85-0.95).** "
            f"Hysteresis alone causes mild degradation. Some transitions close "
            f"together are suppressed by sustain_min={sustain_min}."
        )
    else:
        relaxed_interp = (
            f"**Relaxed Oracle Macro F1 = {relaxed_macro:.4f} < 0.85.** "
            f"Even without ordering, hysteresis significantly impacts recall."
        )

    md_lines = [
        f"# MonotonicDecoder Oracle Bound (Opus 141 Q46) — CPU Verification",
        f"",
        f"**Date:** 2026-07-07",
        f"**Device:** CPU-only (numpy), OOM-safe",
        f"**Tolerance:** +/-{tolerance} frames",
        f"**Hysteresis:** sustain_hi={sustain_hi}, sustain_lo={sustain_lo}, sustain_min={sustain_min}",
        f"",
        f"## Summary",
        f"",
        f"| Condition | Oracle Macro F1 | Oracle Micro F1 | GT Transitions | Pred Transitions |",
        f"|-----------|----------------|----------------|----------------|------------------|",
        f"| **Sustained** (procedure_order=True) | **{sustained_macro:.4f}** | {sustained_micro:.4f} | {total_gt_trans} | {total_pred_trans} |",
        f"| **Relaxed** (procedure_order=False) | **{relaxed_macro:.4f}** | {relaxed_micro:.4f} | {total_gt_trans_r} | {total_pred_trans_r} |",
        f"",
        f"## Verification vs Agent-25 (GPU)",
        f"",
        f"| Metric | Agent-25 (GPU) | This Run (CPU) | Diff |",
        f"|--------|----------------|----------------|------|",
        f"| Sustained Macro F1 | {agent25_sustained:.4f} | {sustained_macro:.4f} | {sustained_diff:+.4f} |",
        f"| Relaxed Macro F1 | {agent25_relaxed:.4f} | {relaxed_macro:.4f} | {relaxed_diff:+.4f} |",
        f"",
    ]
    if match:
        md_lines.append("**Result: VERIFIED** - CPU oracle matches Agent-25 GPU result within 0.01.")
    else:
        md_lines.append(
            "**Result: DIFFERS** - numpy decoder diverges from torch-based "
            "implementation used by Agent-25."
        )

    # Per-component sustained
    md_lines.extend([
        f"",
        f"## Per-Component Oracle F1 (Sustained)",
        f"",
        f"| Component | Mean F1 | Std | Min | Max |",
        f"|-----------|---------|-----|-----|-----|",
    ])
    for c_str in sorted(sustained_per_component.keys(), key=int):
        v = sustained_per_component[c_str]
        md_lines.append(
            f"| comp{c_str} | {v['mean']:.4f} | {v['std']:.4f} | "
            f"{v['min']:.4f} | {v['max']:.4f} |"
        )

    md_lines.extend([
        f"",
        f"## Per-Component Oracle F1 (Relaxed)",
        f"",
        f"| Component | Mean F1 | Std | Min | Max |",
        f"|-----------|---------|-----|-----|-----|",
    ])
    for c_str in sorted(relaxed_per_component.keys(), key=int):
        v = relaxed_per_component[c_str]
        md_lines.append(
            f"| comp{c_str} | {v['mean']:.4f} | {v['std']:.4f} | "
            f"{v['min']:.4f} | {v['max']:.4f} |"
        )

    md_lines.extend([
        f"",
        f"## Interpretation",
        f"",
        sustained_interp,
        f"",
        relaxed_interp,
        f"",
        f"### Bottleneck Analysis",
        f"",
        f"The gap between sustained ({sustained_macro:.4f}) and relaxed "
        f"({relaxed_macro:.4f}) reveals that the hardcoded sequential "
        f"procedure-order constraint (comp0->comp1->...->comp10) is the "
        f"primary bottleneck, suppressing ~{int((1 - sustained_macro/relaxed_macro)*100):.0f}% "
        f"of achievable F1. Hysteresis alone (sustain_min={sustain_min}) accounts for "
        f"only {(1 - relaxed_macro):.1%} F1 loss.",
        f"",
        f"## Per-Recording Results (Sustained)",
        f"",
        f"| Recording | Frames | GT Trans | Pred Trans | Macro F1 | Micro F1 |",
        f"|-----------|--------|----------|------------|----------|----------|",
    ])
    for rec_id in sorted(sustained_per_rec.keys()):
        r = sustained_per_rec[rec_id]
        md_lines.append(
            f"| {rec_id} | {r['num_frames']} | {r['n_gt_transitions']} | "
            f"{r['n_pred_transitions']} | {r['macro_f1']:.4f} | {r['micro_f1']:.4f} |"
        )

    md_lines.extend([
        f"",
        f"## Per-Recording Results (Relaxed)",
        f"",
        f"| Recording | Frames | GT Trans | Pred Trans | Macro F1 | Micro F1 |",
        f"|-----------|--------|----------|------------|----------|----------|",
    ])
    for rec_id in sorted(relaxed_per_rec.keys()):
        r = relaxed_per_rec[rec_id]
        md_lines.append(
            f"| {rec_id} | {r['num_frames']} | {r['n_gt_transitions']} | "
            f"{r['n_pred_transitions']} | {r['macro_f1']:.4f} | {r['micro_f1']:.4f} |"
        )

    md_path = save_dir / "oracle_f1.md"
    with open(md_path, "w") as f:
        f.write("\n".join(md_lines) + "\n")
    print(f"Markdown report saved to {md_path}")

    # ==================================================================
    # Summary print
    # ==================================================================
    print(f"\n{'=' * 60}")
    print(f"DECODER ORACLE BOUND — CPU VERIFICATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Sustained Macro F1:  {sustained_macro:.6f}")
    print(f"  Relaxed Macro F1:    {relaxed_macro:.6f}")
    print(f"  Agent-25 Sustained:  {agent25_sustained:.4f} (GPU)")
    print(f"  Agent-25 Relaxed:    {agent25_relaxed:.4f} (GPU)")
    print(f"  Verified:            {'YES' if match else 'NO'}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
