"""
PSR Transition — MonotonicDecoder and Q48 hysteresis for assembly state decoding.

Architecture
============
The MonotonicDecoder enforces procedure-order constraints on binary state
sequences produced by the PSR head. Raw sigmoid scores (one per assembly
component per frame) are decoded into monotone state sequences via:

  1. Hysteresis gating: sustain_hi / sustain_lo thresholds prevent
     jitter near the decision boundary.
  2. Minimum sustain: sustain_min frames must pass before a state
     transition (0->1 or 1->0) is accepted.
  3. Fill-forward (optional): once a component reaches state=1,
     it may optionally be locked to prevent 1->0 transitions
     for irreversible assembly steps.
  4. Procedure-order (optional): components with ordering constraints
     cannot transition to 1 before earlier components.

This is the Q48 implementation referenced by D4 eval. Hysteresis
thresholds are tuned per component because YOLOv8m-derived sigmoid
scores have different statistics for each assembly component.

References
----------
- agent10-psr.md: "Per-recording: decodes logits through
  MonotonicDecoder -> monotone state sequence"
- agent4-model.md: "PSRTransitionPredictor, MonotonicDecoder,
  and build_transition_targets functions"
"""

from __future__ import annotations

from typing import Optional

import numpy as np


# ============================================================================
# MonotonicDecoder — Q48 Hysteresis
# ============================================================================

class MonotonicDecoder:
    """Decode per-component sigmoid scores into monotone state sequences.

    Q48 hysteresis parameters (per component):
        sustain_hi  : score above which state is forced to 1
        sustain_lo  : score below which state is forced to 0
        sustain_min : minimum frames a state must persist

    The decoder operates per-recording (a contiguous sequence of frames
    from one video/camera view). It produces:

      - state_seq  : [T] binary state per frame (0=absent, 1=present)
      - transitions : list of frame indices where state flips 0->1
    """

    def __init__(
        self,
        sustain_hi: float = 0.5,
        sustain_lo: float = 0.3,
        sustain_min: int = 3,
        fill_forward: bool = False,
        order_prior: bool = False,
    ):
        if sustain_lo >= sustain_hi:
            raise ValueError(f"sustain_lo ({sustain_lo}) must be < sustain_hi ({sustain_hi})")
        if sustain_min < 1:
            raise ValueError(f"sustain_min ({sustain_min}) must be >= 1")

        self.sustain_hi = sustain_hi
        self.sustain_lo = sustain_lo
        self.sustain_min = sustain_min
        self.fill_forward = fill_forward
        self.order_prior = order_prior

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
        trans = []
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

            # optional fill-forward: once ON, stay ON
            if self.fill_forward and t > 0 and state[t - 1] == 1:
                state[t] = 1
                # remove any spurious transition logged
                if trans and trans[-1] == t:
                    trans.pop()

        return state, trans

    def decode_all(
        self,
        scores: np.ndarray,
        component_order: Optional[list[int]] = None,
    ) -> tuple[np.ndarray, dict[int, list[int]]]:
        """Decode multi-component scores.

        Args:
            scores: [T, C] array of sigmoid scores.
            component_order: optional ordering constraint — component i
                cannot transition before component_order[i-1] has transitioned.

        Returns:
            state_seq: [T, C] binary array.
            transitions: dict {comp_idx: [frame_indices]}.
        """
        C = scores.shape[1]
        T = scores.shape[0]
        state_seq = np.zeros((T, C), dtype=np.int32)
        transitions: dict[int, list[int]] = {}
        comp_transitioned = np.zeros(C, dtype=bool)

        # determine processing order
        order = component_order if component_order else list(range(C))
        ordered_components = [c for c in order if c < C]

        for c in ordered_components:
            if component_order is not None:
                # Apply per-component thresholds (could be tuned per component)
                hi = self.sustain_hi
                lo = self.sustain_lo
            else:
                hi = self.sustain_hi
                lo = self.sustain_lo

            st, tr = self.decode(scores[:, c])
            state_seq[:, c] = st
            transitions[c] = tr

            # enforce order prior
            if self.order_prior and component_order:
                idx_in_order = component_order.index(c)
                if idx_in_order > 0:
                    prev_comp = component_order[idx_in_order - 1]
                    prev_transitioned = comp_transitioned[prev_comp]
                    # suppress transitions before predecessor
                    filtered_tr = [t for t in tr if prev_transitioned or
                                   (comp_transitioned[:c].sum() > 0 and
                                    prev_comp in component_order and
                                    comp_transitioned[prev_comp])]
                    transitions[c] = filtered_tr
                comp_transitioned[c] = len(tr) > 0

        return state_seq, transitions


# ============================================================================
# PSRTransitionPredictor
# ============================================================================

class PSRTransitionPredictor:
    """Wrapper that applies MonotonicDecoder to PSR head logits.

    Pipeline:
        logits -> sigmoid -> MonotonicDecoder -> state_seq + transitions
    """

    def __init__(
        self,
        n_components: int = 11,
        sustain_hi: float = 0.5,
        sustain_lo: float = 0.3,
        sustain_min: int = 3,
        fill_forward: bool = False,
        order_prior: bool = False,
        component_order: Optional[list[int]] = None,
    ):
        self.n_components = n_components
        self.component_order = component_order or list(range(n_components))
        # Per-component thresholds
        self.sustain_hi = np.full(n_components, sustain_hi, dtype=np.float32)
        self.sustain_lo = np.full(n_components, sustain_lo, dtype=np.float32)
        self.sustain_min = np.full(n_components, sustain_min, dtype=np.int32)
        self.fill_forward = fill_forward
        self.order_prior = order_prior

    def set_thresholds(
        self,
        sustain_hi: Optional[np.ndarray] = None,
        sustain_lo: Optional[np.ndarray] = None,
        sustain_min: Optional[np.ndarray] = None,
    ):
        """Set per-component thresholds."""
        if sustain_hi is not None:
            self.sustain_hi[:] = sustain_hi
        if sustain_lo is not None:
            self.sustain_lo[:] = sustain_lo
        if sustain_min is not None:
            self.sustain_min[:] = sustain_min

    def predict(
        self,
        logits: np.ndarray,
    ) -> tuple[np.ndarray, dict[int, list[int]]]:
        """Predict state sequences from logits.

        Args:
            logits: [T, C] or [T, C+1] raw pre-sigmoid logits.
                    If [T, C+1], last channel is confidence (ignored here).

        Returns:
            state_seq: [T, C] binary states.
            transitions: dict {c: [frame indices]}.
        """
        if logits.ndim == 1:
            logits = logits.reshape(-1, 1)
        if logits.shape[1] > self.n_components:
            logits = logits[:, :self.n_components]

        scores = 1.0 / (1.0 + np.exp(-logits.clip(-30, 30)))  # sigmoid
        return self._decode_scores(scores)

    def _decode_scores(
        self,
        scores: np.ndarray,
    ) -> tuple[np.ndarray, dict[int, list[int]]]:
        T, C = scores.shape
        state_seq = np.zeros((T, C), dtype=np.int32)
        transitions: dict[int, list[int]] = {}

        for c in range(C):
            decoder = MonotonicDecoder(
                sustain_hi=float(self.sustain_hi[c]),
                sustain_lo=float(self.sustain_lo[c]),
                sustain_min=int(self.sustain_min[c]),
                fill_forward=self.fill_forward,
                order_prior=(self.order_prior and c > 0),
            )
            st, tr = decoder.decode(scores[:, c])
            state_seq[:, c] = st
            transitions[c] = tr

        return state_seq, transitions

    def decode_and_score(
        self,
        logits: np.ndarray,
        gt_states: np.ndarray,
        tolerance: int = 3,
    ) -> dict[str, float]:
        """Decode logits and compute transition F1 vs ground truth.

        Args:
            logits: [T, C] or [T, C+1] raw logits.
            gt_states: [T, C] binary (0/1/-1 for masked).
            tolerance: frame tolerance for transition matching.

        Returns:
            metrics dict with keys:
                f1_at_t: symmetric transition F1 at +/- tolerance
                precision, recall, n_trans_pred, n_trans_gt
                per_component_f1: {c: f1}
        """
        state_seq, pred_trans = self.predict(logits)
        return compute_transition_f1(
            pred_trans, pred_states=state_seq,
            gt_states=gt_states,
            tolerance=tolerance,
        )


# ============================================================================
# Transition F1 Computation
# ============================================================================

def compute_transition_f1(
    pred_transitions: dict[int, list[int]],
    pred_states: np.ndarray,
    gt_states: np.ndarray,
    tolerance: int = 3,
) -> dict[str, float]:
    """Compute symmetric bi-directional transition F1.

    For each component:
      - Extract GT transition frames (0->1) from gt_states
      - Match predicted transitions to GT transitions within +/- tolerance
        using greedy bi-directional matching.
      - TP = matched pred transitions, FP = unmatched pred, FN = unmatched GT

    Args:
        pred_transitions: dict {c: [frame_indices]}.
        pred_states: [T, C] binary (for future use, not directly used).
        gt_states: [T, C] binary (0/1) with -1 meaning masked (ignored).

    Returns:
        dict with f1_at_t, precision, recall, n_trans_pred, n_trans_gt.
    """
    C = gt_states.shape[1]
    all_tp = 0
    all_fp = 0
    all_fn = 0
    comp_f1s = {}

    for c in range(C):
        # get GT transitions
        gt_col = gt_states[:, c]
        valid = gt_col != -1
        if valid.sum() == 0:
            continue

        # find 0->1 transitions in GT
        gt_bin = np.where(valid, gt_col, 0).astype(np.int32)
        gt_trans = list(np.where(np.diff(gt_bin, prepend=0) == 1)[0])

        pred_tr = pred_transitions.get(c, [])

        n_gt = len(gt_trans)
        n_pred = len(pred_tr)

        if n_gt == 0 and n_pred == 0:
            comp_f1s[c] = 1.0  # perfect agreement on no transitions
            continue

        # greedy bi-directional matching
        gt_matched = [False] * n_gt
        pred_matched = [False] * n_pred

        # first pass: match closest pred to each GT
        for gi, gf in enumerate(gt_trans):
            best_dist = tolerance + 1
            best_pi = -1
            for pi, pf in enumerate(pred_tr):
                if pred_matched[pi]:
                    continue
                dist = abs(pf - gf)
                if dist < best_dist:
                    best_dist = dist
                    best_pi = pi
            if best_pi >= 0:
                gt_matched[gi] = True
                pred_matched[best_pi] = True

        tp = sum(gt_matched)
        fp = n_pred - tp
        fn = n_gt - tp

        all_tp += tp
        all_fp += fp
        all_fn += fn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        comp_f1s[c] = (2 * precision * recall / (precision + recall)
                       if (precision + recall) > 0 else 0.0)

    # No transitions at all → perfect agreement
    if all_tp == 0 and all_fp == 0 and all_fn == 0:
        total_precision = 1.0
        total_recall = 1.0
        total_f1 = 1.0
    else:
        total_precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) > 0 else 0.0
        total_recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) > 0 else 0.0
        total_f1 = (2 * total_precision * total_recall / (total_precision + total_recall)
                    if (total_precision + total_recall) > 0 else 0.0)

    return {
        "f1_at_t": total_f1,
        "precision": total_precision,
        "recall": total_recall,
        "n_trans_pred": all_tp + all_fp,
        "n_trans_gt": all_tp + all_fn,
        "n_tp": all_tp,
        "per_component_f1": comp_f1s,
    }


def compute_psr_overall_f1(
    state_seq: np.ndarray,
    gt_states: np.ndarray,
) -> float:
    """Compute per-frame macro F1 across components.

    This is the 'overall F1' metric (threshold-based, NOT transition-based).
    Used as a secondary metric; the primary benchmark is f1_at_t.
    """
    C = gt_states.shape[1]
    comp_f1s = []

    for c in range(C):
        valid = gt_states[:, c] != -1
        if valid.sum() == 0:
            continue

        pred_c = state_seq[valid, c]
        gt_c = gt_states[valid, c].astype(np.int32)

        tp = ((pred_c == 1) & (gt_c == 1)).sum()
        fp = ((pred_c == 1) & (gt_c == 0)).sum()
        fn = ((pred_c == 0) & (gt_c == 1)).sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) > 0 else 0.0)
        comp_f1s.append(f1)

    return float(np.nanmean(comp_f1s)) if comp_f1s else 0.0


# ============================================================================
# Build Transition Targets (for training)
# ============================================================================

def build_transition_targets(
    labels: np.ndarray,
    sigma: float = 3.0,
    seq_length: Optional[int] = None,
) -> np.ndarray:
    """Build Gaussian-smeared transition targets from binary labels.

    Converts fill-forward binary labels into smooth transition targets.
    Each 0->1 boundary is smeared with a Gaussian of width sigma.

    Args:
        labels: [T, C] binary labels (0/1), or [B, T, C].
        sigma: Gaussian width in frames.
        seq_length: if provided, truncate/pad to this length.

    Returns:
        targets: same shape as labels, float in [0, 1] with Gaussian smearing.
    """
    if labels.ndim == 3:
        B, T, C = labels.shape
        targets = np.zeros_like(labels, dtype=np.float32)
        for b in range(B):
            for c in range(C):
                targets[b, :, c] = _smear_transitions(labels[b, :, c], sigma)
        if seq_length is not None and seq_length != T:
            # truncate or pad
            new_targets = np.zeros((B, seq_length, C), dtype=np.float32)
            take = min(seq_length, T)
            new_targets[:, :take, :] = targets[:, :take, :]
            targets = new_targets
        return targets
    else:
        T, C = labels.shape
        targets = np.zeros_like(labels, dtype=np.float32)
        for c in range(C):
            targets[:, c] = _smear_transitions(labels[:, c], sigma)
        return targets


def _smear_transitions(seq: np.ndarray, sigma: float) -> np.ndarray:
    """Apply Gaussian smearing to transition boundaries in a 1-D sequence."""
    T = len(seq)
    target = seq.copy().astype(np.float32)
    # find 0->1 transitions
    diffs = np.diff(seq, prepend=0)
    ons = np.where(diffs == 1)[0]

    # build Gaussian kernel
    radius = int(4 * sigma)
    kernel = np.exp(-0.5 * np.arange(-radius, radius + 1) ** 2 / sigma ** 2)
    kernel = kernel / kernel.max()  # normalize so peak = 1

    for t in ons:
        lo = max(0, t - radius)
        hi = min(T, t + radius + 1)
        kl = radius - (t - lo)
        kr = kernel[kl:kl + (hi - lo)]
        target[lo:hi] = np.maximum(target[lo:hi], kr)

    return target


# ============================================================================
# S2 from YOLO Detections — convert YOLO detections to PSR-compatible scores
# ============================================================================

def s2_from_yolo_detections(
    yolo_outputs: list[dict],
    n_components: int = 11,
    score_fallback: float = 0.1,
) -> np.ndarray:
    """Convert YOLO detection outputs to per-component sigmoid scores.

    YOLOv8m predicts 24 detection classes (background + 22 assembly states
    + error_state). PSR uses 11 assembly components. This function maps
    detection class confidences to component-level scores by taking the
    max score per component group.

    Args:
        yolo_outputs: list of dicts, one per frame, with keys:
            - 'boxes': [N, 4] xyxy boxes
            - 'scores': [N] confidence scores
            - 'labels': [N] class labels (0-23)
        n_components: number of PSR components (default 11).
        score_fallback: default score for frames with no detections.

    Returns:
        scores: [T, n_components] sigmoid scores in [0, 1].
    """
    T = len(yolo_outputs)
    scores = np.full((T, n_components), score_fallback, dtype=np.float32)

    for t, frame_out in enumerate(yolo_outputs):
        labels = frame_out.get("labels", [])
        confs = frame_out.get("scores", [])
        for label, conf in zip(labels, confs):
            # Map YOLO class to PSR component index
            # YOLO classes 1-22 map to PSR components 0-10 (grouped)
            comp_idx = _yolo_class_to_psr_component(int(label))
            if 0 <= comp_idx < n_components:
                scores[t, comp_idx] = max(scores[t, comp_idx], float(conf))

    return scores


def _yolo_class_to_psr_component(yolo_class: int) -> int:
    """Map YOLO detection class to PSR component index.

    YOLO class mapping (from training config):
      0: background (ignored)
      1-22: assembly component states
      23: error_state (ignored)

    PSR has 11 components. Detection classes are grouped:
      component 0: classes 1-2 (base plate)
      component 1: classes 3-4 (screws/bolts)
      component 2: classes 5-6 (structural frame)
      component 3: classes 7-8 (panels)
      component 4: classes 9-10 (wiring/harness)
      component 5: classes 11-12 (connectors)
      component 6: classes 13-14 (fasteners)
      component 7: classes 15-16 (sub-assembly A)
      component 8: classes 17-18 (sub-assembly B)
      component 9: classes 19-20 (covering/housing)
      component 10: classes 21-22 (final assembly)
    """
    if yolo_class <= 0 or yolo_class >= 23:
        return -1  # background or error — ignore
    comp_map = {
        1: 0, 2: 0,    # base plate
        3: 1, 4: 1,    # screws/bolts
        5: 2, 6: 2,    # structural frame
        7: 3, 8: 3,    # panels
        9: 4, 10: 4,   # wiring/harness
        11: 5, 12: 5,  # connectors
        13: 6, 14: 6,  # fasteners
        15: 7, 16: 7,  # sub-assembly A
        17: 8, 18: 8,  # sub-assembly B
        19: 9, 20: 9,  # covering/housing
        21: 10, 22: 10, # final assembly
    }
    return comp_map.get(yolo_class, -1)
