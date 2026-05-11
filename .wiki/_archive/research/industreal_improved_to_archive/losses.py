"""
POPW v2/v3 Loss Functions
==========================
LDAMLoss with label_smoothing=0.1 (Issue C fix).
Focal loss for class imbalance.
WingLoss for head pose regression.
BCE for assembly state and error verification.

Author: Bashara | Date: May 2026
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================================
# LDAMLoss — Label-Smoothing LDAM for Activity Recognition
# ============================================================================

class LDAMLoss(nn.Module):
    """
    LDAM (Label-Disturbing Asymmetric Metric) Loss with label smoothing.

    Paper: "LDAM: Learning for Multi-Label Classification" adapted for
    single-label with label smoothing as per POPW v2.

    Fix (Issue C): label_smoothing=0.1 was missing → added to cross_entropy.
    """

    def __init__(
        self,
        num_classes: int,
        label_smoothing: float = 0.1,
        cls_weight: torch.Tensor = None,
    ):
        super().__init__()
        self.num_classes = num_classes
        self.label_smoothing = label_smoothing
        self.cls_weight = cls_weight

        # LDAM margin schedule: margins decrease for later classes
        # c_i = 1 / (num_classes - 1)^(1/4) * i^(1/4)
        self.register_buffer(
            "margins",
            torch.tensor([
                1.0 / (math.pow(num_classes - 1, 0.25)) * math.pow(c, 0.25)
                for c in range(1, num_classes + 1)
            ]),
        )

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            logits   : [B, num_classes] — raw unnormalized scores
            targets  : [B] — class indices

        Returns:
            scalar loss
        """
        B = logits.size(0)
        device = logits.device

        # Convert targets to one-hot
        targets_onehot = F.one_hot(targets, self.num_classes).float().to(device)

        # Apply LDAM margins: shift logits of higher-index classes
        # Margin only applied to positive class in single-label setting
        margins = self.margins.unsqueeze(0)  # [1, num_classes]
        shifted_logits = logits - margins * targets_onehot

        # Label smoothing cross-entropy
        log_probs = F.log_softmax(shifted_logits, dim=1)
        nll_loss = -(targets_onehot * log_probs).sum(dim=1)  # [B]

        # Label smoothing: blend with uniform distribution
        if self.label_smoothing > 0:
            smooth_loss = -log_probs.mean(dim=1)  # [B]
            nll_loss = (
                1.0 - self.label_smoothing
            ) * nll_loss + self.label_smoothing * smooth_loss

        # Class weighting
        if self.cls_weight is not None:
            weights = targets_onehot @ self.cls_weight.unsqueeze(0).t()  # [B]
            nll_loss = nll_loss * weights.squeeze()

        return nll_loss.mean()


# ============================================================================
# Focal Loss — for class-imbalanced activity recognition
# ============================================================================

class FocalLoss(nn.Module):
    """
    Focal Loss for activity recognition (fallback if LDAM not used).
    FL(p_t) = -α_t * (1 - p_t)^γ * log(p_t)
    """

    def __init__(
        self,
        alpha: float = 0.25,
        gamma: float = 2.0,
        label_smoothing: float = 0.0,
    ):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.label_smoothing = label_smoothing

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
    ) -> torch.Tensor:
        p_t = torch.exp(
            F.cross_entropy(logits, targets, reduction="none",
                           label_smoothing=self.label_smoothing)
        )
        focal_weight = (1 - p_t) ** self.gamma
        if self.alpha >= 0:
            alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
            focal_loss = alpha_t * focal_weight * F.cross_entropy(
                logits, targets, reduction="none",
                label_smoothing=self.label_smoothing
            )
        else:
            focal_loss = focal_weight * F.cross_entropy(
                logits, targets, reduction="none",
                label_smoothing=self.label_smoothing
            )
        return focal_loss.mean()


# ============================================================================
# WingLoss — for head pose regression (angles + position)
# ============================================================================

class WingLoss(nn.Module):
    """
    WingLoss for facial/head pose landmark regression.
    Paper: "Wing Loss for Robust Facial Landmark Localisation with
    Convolutional Neural Networks" (CVPR 2018).

    Two regimes:
        - |x| < ω: quadratic loss (Cauchy-like)
        - |x| ≥ ω: log-based loss (Charbonnier-like)
    """

    def __init__(
        self,
        omega: float = 1.0,
        epsilon: float = 2.0,
    ):
        super().__init__()
        self.omega = omega
        self.epsilon = epsilon
        self.C = omega - omega * math.log(1 + omega / epsilon)

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
    ) -> torch.Tensor:
        diff = torch.abs(pred - target)
        loss = torch.where(
            diff < self.omega,
            self.omega * torch.log(1 + diff / self.epsilon),
            diff - self.C,
        )
        return loss.mean()


# ============================================================================
# Combined Head Pose Loss
# ============================================================================

class HeadPoseLoss(nn.Module):
    """
    Combined loss for head pose regression:
      - WingLoss for angular components (3 angles in radians)
      - SmoothL1 for positional components (3 positions in mm)

    Angular and positional components are normalized separately
    before combination.
    """

    def __init__(
        self,
        angle_weight: float = 1.0,
        position_weight: float = 0.1,  # mm scale vs radian scale
    ):
        super().__init__()
        self.angle_weight = angle_weight
        self.position_weight = position_weight
        self.wing_loss = WingLoss()
        self.smooth_l1 = nn.SmoothL1Loss(reduction="mean")

    def forward(
        self,
        pred: torch.Tensor,
        target: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            pred   : [B, 6] — [angle_1, angle_2, angle_3, pos_x, pos_y, pos_z]
            target : [B, 6] — same format

        Returns:
            scalar loss
        """
        # First 3: angular (radians) — WingLoss
        angle_loss = self.wing_loss(pred[:, :3], target[:, :3])

        # Last 3: positional (mm) — SmoothL1
        pos_loss = self.smooth_l1(pred[:, 3:], target[:, 3:])

        return self.angle_weight * angle_loss + self.position_weight * pos_loss


# ============================================================================
# Assembly State Loss — Cross-Entropy (3-class)
# ============================================================================

class AssemblyStateLoss(nn.Module):
    """Cross-entropy for 3-class assembly state: pre/in/post assembly."""

    def __init__(
        self,
        label_smoothing: float = 0.0,
        cls_weight: torch.Tensor = None,
    ):
        super().__init__()
        self.label_smoothing = label_smoothing
        self.cls_weight = cls_weight

    def forward(
        self,
        logits: torch.Tensor,  # [B, 3]
        targets: torch.Tensor,  # [B]
    ) -> torch.Tensor:
        return F.cross_entropy(
            logits,
            targets,
            label_smoothing=self.label_smoothing,
            weight=self.cls_weight,
        )


# ============================================================================
# Error Verification Loss — Binary Cross-Entropy
# ============================================================================

class ErrorVerificationLoss(nn.Module):
    """
    Binary cross-entropy for frame-level assembly error detection.
    Uses pos_weight to handle class imbalance (errors are rare).
    """

    def __init__(
        self,
        pos_weight: float = 3.0,  # errors are rare → upweight positive
    ):
        super().__init__()
        self.pos_weight = pos_weight

    def forward(
        self,
        logits: torch.Tensor,  # [B, 1] or [B]
        targets: torch.Tensor,  # [B] binary 0/1
    ) -> torch.Tensor:
        if logits.dim() == 2:
            logits = logits.squeeze(1)
        return F.binary_cross_entropy_with_logits(
            logits,
            targets.float(),
            pos_weight=torch.tensor(self.pos_weight, device=logits.device),
        )


# ============================================================================
# PSR Contrastive Loss
# ============================================================================

class PSRContrastiveLoss(nn.Module):
    """
    Phase Similarity Representation contrastive loss.

    Encourages:
      - Same phase frames to have similar PSR vectors
      - Different phase frames to have dissimilar PSR vectors

    Uses NT-Xent (Normalized Temperature-scaled Cross Entropy) loss.
    """

    def __init__(
        self,
        temperature: float = 0.1,
        margin: float = 0.5,
    ):
        super().__init__()
        self.temperature = temperature
        self.margin = margin

    def forward(
        self,
        psr_vectors: torch.Tensor,  # [B, feat_dim]
        phase_labels: torch.Tensor,  # [B] — phase indices
    ) -> torch.Tensor:
        """
        Args:
            psr_vectors: [B, D] — normalized PSR vectors
            phase_labels: [B] — integer phase labels

        Returns:
            scalar loss
        """
        B = psr_vectors.size(0)
        device = psr_vectors.device

        # Normalize
        psr_vectors = F.normalize(psr_vectors, dim=1)

        # Similarity matrix
        sim = torch.mm(psr_vectors, psr_vectors.t()) / self.temperature  # [B, B]

        # Mask: same phase = positive, different phase = negative
        labels_equal = phase_labels.unsqueeze(0) == phase_labels.unsqueeze(1)  # [B, B]
        mask_pos = labels_equal.float()
        mask_neg = ~labels_equal

        # Diagonal to 0 (don't contrast with self)
        diag = torch.eye(B, device=device, dtype=torch.bool)
        sim.masked_fill_(diag, 0.0)

        # Numerically stable cross-entropy
        exp_sim = torch.exp(sim)
        log_prob = sim - torch.log(exp_sim.sum(dim=1, keepdim=True))

        # Positive pairs loss
        pos_loss = -(mask_pos * log_prob).sum() / mask_pos.sum()

        # Optional: margin-based triplet push for negatives
        if self.margin > 0:
            pos_sim = (sim * mask_pos).clamp(min=0).sum() / mask_pos.sum()
            neg_sim = (sim * mask_neg).clamp(min=0).sum() / mask_neg.sum()
            margin_loss = torch.clamp(self.margin + neg_sim - pos_sim, min=0).mean()
            return 0.5 * pos_loss + 0.5 * margin_loss

        return pos_loss


# ============================================================================
# Multi-Task Loss Aggregator
# ============================================================================

class MultiTaskLoss(nn.Module):
    """
    Combines all five task losses with learnable uncertainty weighting.

    Reference: "Multi-Task Learning Using Uncertainty to Weigh Losses"
    (Kendall, Gal, et al., CVPR 2018)

    The approach learns per-task log variances, making the loss:
        L = Σ_i (1 / (2 * exp(log_sigma_i)^2)) * task_loss_i + log_sigma_i

    This automatically balances task weights without manual tuning.
    """

    def __init__(
        self,
        num_tasks: int = 5,
    ):
        super().__init__()
        # Learnable log-variance per task
        # Tasks: 0=activity, 1=head_pose, 2=assembly_state, 3=error_verif, 4=psr
        self.log_vars = nn.Parameter(torch.zeros(num_tasks))

    def forward(
        self,
        losses: torch.Tensor,  # [num_tasks] — individual task losses
    ) -> torch.Tensor:
        """
        Args:
            losses: [5] — activity, head_pose, assembly_state, error_verif, psr

        Returns:
            scalar combined loss
        """
        total = 0.0
        for i, task_loss in enumerate(losses):
            precision = torch.exp(-self.log_vars[i])
            total += precision * task_loss + self.log_vars[i]
        return total


# ============================================================================
# Convenience factory
# ============================================================================

def build_loss(name: str, **kwargs) -> nn.Module:
    """Build loss by name."""
    factories = {
        "ldam": LDAMLoss,
        "focal": FocalLoss,
        "wing": WingLoss,
        "head_pose": HeadPoseLoss,
        "assembly_state": AssemblyStateLoss,
        "error_verification": ErrorVerificationLoss,
        "psr_contrastive": PSRContrastiveLoss,
        "multitask": MultiTaskLoss,
    }
    name = name.lower()
    if name not in factories:
        raise ValueError(f"Unknown loss: {name}. Available: {list(factories)}")
    return factories[name](**kwargs)