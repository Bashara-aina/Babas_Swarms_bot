"""
POPW v2/v3 Smoke Test
======================
Basic sanity checks to verify the model, losses, and config
load correctly without GPU or large data.

Run: python smoke_test.py

Author: Bashara | Date: May 2026
"""

from __future__ import annotations

import sys


def test_imports():
    """Verify all modules import without errors."""
    print("[1/7] Testing imports...")
    try:
        import numpy as np
        import torch
        import torch.nn as nn
        from evaluate import (
            compute_activity_metrics,
            compute_assembly_state_f1,
            compute_error_verification_metrics,
            compute_head_pose_mae,
            compute_psr_precision_recall,
            evaluate_batch,
            measure_batched_fps,
            measure_streaming_fps,
        )
        from losses import (
            AssemblyStateLoss,
            ErrorVerificationLoss,
            FocalLoss,
            HeadPoseLoss,
            LDAMLoss,
            MultiTaskLoss,
            PSRContrastiveLoss,
            WingLoss,
        )
        from model import POPWMultiTaskModel

        import config as C
        print("  ✅ All imports OK")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_config_values():
    """Verify critical config values."""
    print("[2/7] Testing config values...")
    import config as C

    checks = [
        ("BATCH_SIZE = 2", C.BATCH_SIZE == 2),
        ("GRAD_ACCUM_STEPS = 16", C.GRAD_ACCUM_STEPS == 16),
        ("EFFECTIVE_BATCH_SIZE = 32", C.EFFECTIVE_BATCH_SIZE == 32),
        ("USE_EMA = True", C.USE_EMA is True),
        ("USE_AMP = True", C.USE_AMP is True),
        ("LABEL_SMOOTHING = 0.1", C.LABEL_SMOOTHING == 0.1),
        ("NUM_ACT_CLASSES = 33", C.NUM_ACT_CLASSES == 33),
        ("NUM_HEAD_POSE = 6", C.NUM_HEAD_POSE == 6),
        ("NUM_ASSEMBLY_STATES = 3", C.NUM_ASSEMBLY_STATES == 3),
        ("IMG_HEIGHT = 224", C.IMG_HEIGHT == 224),
        ("IMG_WIDTH = 224", C.IMG_WIDTH == 224),
        ("DROP_PATH_RATE = 0.1", C.DROP_PATH_RATE == 0.1),
        ("EMA_DECAY = 0.9998", C.EMA_DECAY == 0.9998),
    ]

    all_ok = True
    for name, ok in checks:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False

    return all_ok


def test_model_forward():
    """Test model forward pass with dummy input."""
    print("[3/7] Testing model forward pass...")
    try:
        import torch
        from model import POPWMultiTaskModel

        model = POPWMultiTaskModel(pretrained=False, use_psr_sequence_mode=True)
        model.eval()

        # Dummy input [B=2, C=3, H=224, W=224]
        dummy_images = torch.randn(2, 3, 224, 224)
        dummy_video_ids = ["vid_001", "vid_002"]

        with torch.no_grad():
            out = model(images=dummy_images, video_ids=dummy_video_ids, clip_rgb=None)

        # Verify output keys
        expected_keys = [
            "act_logits",
            "head_pose",
            "assembly_state_logits",
            "error_verification_logits",
            "psr_logits",
            "psr_dict",
            "worker_boxes",
            "bottle_boxes",
            "temporal_features",
            "backbone_features",
        ]
        missing = [k for k in expected_keys if k not in out]
        if missing:
            print(f"  ❌ Missing output keys: {missing}")
            return False

        # Verify shapes
        B = 2
        assert out["act_logits"].shape == (B, 33), f"act_logits shape mismatch: {out['act_logits'].shape}"
        assert out["head_pose"].shape == (B, 6), f"head_pose shape mismatch: {out['head_pose'].shape}"
        assert out["assembly_state_logits"].shape == (B, 3), "assembly_state shape mismatch"
        assert out["error_verification_logits"].shape == (B, 1), "error_verification shape mismatch"
        assert out["psr_logits"].shape == (B, 2), "psr_logits shape mismatch"

        # Verify psr_dict keys
        for tol in [3, 5]:
            assert f"psr_cos_t{tol}" in out["psr_dict"], f"Missing psr_cos_t{tol}"
            assert f"psr_valid_t{tol}" in out["psr_dict"], f"Missing psr_valid_t{tol}"

        print("  ✅ Forward pass OK — output shapes verified")
        print(f"     act_logits:      {out['act_logits'].shape}")
        print(f"     head_pose:       {out['head_pose'].shape}")
        print(f"     assembly_state:  {out['assembly_state_logits'].shape}")
        print(f"     error_verif:     {out['error_verification_logits'].shape}")
        print(f"     psr_logits:      {out['psr_logits'].shape}")
        return True
    except Exception as e:
        print(f"  ❌ Forward pass failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_losses():
    """Test all loss functions."""
    print("[4/7] Testing loss functions...")
    try:
        import torch
        import torch.nn.functional as F
        from losses import (
            AssemblyStateLoss,
            ErrorVerificationLoss,
            FocalLoss,
            HeadPoseLoss,
            LDAMLoss,
            MultiTaskLoss,
            PSRContrastiveLoss,
            WingLoss,
        )

        B, num_classes = 4, 33

        # LDAMLoss (Issue C check: label_smoothing=0.1)
        ldam = LDAMLoss(num_classes=num_classes, label_smoothing=0.1)
        logits = torch.randn(B, num_classes)
        targets = torch.randint(0, num_classes, (B,))
        loss = ldam(logits, targets)
        assert loss.numel() == 1, f"LDAMLoss should return scalar, got shape {loss.shape}"
        print(f"  ✅ LDAMLoss: {loss.item():.4f} (label_smoothing=0.1 verified)")

        # HeadPoseLoss
        pose_loss_fn = HeadPoseLoss()
        pred_pose = torch.randn(B, 6)
        tgt_pose = torch.randn(B, 6)
        pose_loss = pose_loss_fn(pred_pose, tgt_pose)
        print(f"  ✅ HeadPoseLoss: {pose_loss.item():.4f}")

        # AssemblyStateLoss
        as_loss_fn = AssemblyStateLoss()
        as_logits = torch.randn(B, 3)
        as_targets = torch.randint(0, 3, (B,))
        as_loss = as_loss_fn(as_logits, as_targets)
        print(f"  ✅ AssemblyStateLoss: {as_loss.item():.4f}")

        # ErrorVerificationLoss
        ev_loss_fn = ErrorVerificationLoss(pos_weight=3.0)
        ev_logits = torch.randn(B, 1)
        ev_targets = torch.randint(0, 2, (B,)).float()
        ev_loss = ev_loss_fn(ev_logits, ev_targets)
        print(f"  ✅ ErrorVerificationLoss: {ev_loss.item():.4f}")

        # MultiTaskLoss
        mt_loss_fn = MultiTaskLoss(num_tasks=5)
        task_losses = torch.tensor([0.5, 0.3, 0.2, 0.1, 0.4])
        mt_loss = mt_loss_fn(task_losses)
        print(f"  ✅ MultiTaskLoss: {mt_loss.item():.4f}")

        return True
    except Exception as e:
        print(f"  ❌ Loss test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_parameters():
    """Count model parameters."""
    print("[5/7] Counting model parameters...")
    try:
        import torch
        from model import POPWMultiTaskModel, count_parameters

        model = POPWMultiTaskModel(pretrained=False)
        counts = count_parameters(model)

        print(f"  Backbone:       {counts['backbone']:,}")
        print(f"  TemporalEncoder:{counts['temporal_encoder']:,}")
        print(f"  PSR:            {counts['psr']:,}")
        print(f"  Activity Head:  {counts['activity_head']:,}")
        print(f"  Head Pose Head:  {counts['head_pose_head']:,}")
        print(f"  Assembly State:  {counts['assembly_state_head']:,}")
        print(f"  Error Verif:    {counts['error_verification_head']:,}")
        print(f"  PDD:            {counts['pdd']:,}")
        print("  ─────────────────────────────")
        print(f"  Total:          {counts['total']:,}")
        print(f"  Trainable:      {counts['total_trainable']:,}")

        # Basic sanity: should be > 10M params
        if counts["total"] < 10_000_000:
            print(f"  ⚠️  Model seems small ({counts['total']:,} < 10M) — check backbone")
            return False

        print(f"  ✅ Parameter count OK ({counts['total']:,} total)")
        return True
    except Exception as e:
        print(f"  ❌ Parameter count failed: {e}")
        return False


def test_evaluate_metrics():
    """Test evaluate metric functions."""
    print("[6/7] Testing evaluate metrics...")
    try:
        import numpy as np
        import torch
        from evaluate import (
            compute_activity_metrics,
            compute_assembly_state_f1,
            compute_error_verification_metrics,
            compute_head_pose_mae,
            compute_psr_precision_recall,
        )

        B = 4

        # Activity metrics
        act_logits = torch.randn(B, 33)
        act_targets = torch.randint(0, 33, (B,))
        metrics = compute_activity_metrics(act_logits, act_targets)
        assert "act_top1_acc" in metrics
        assert "act_top5_acc" in metrics
        assert "act_mcAP" in metrics
        print(f"  ✅ compute_activity_metrics: {metrics}")

        # Head pose MAE
        pred_pose = torch.randn(B, 6)
        tgt_pose = torch.randn(B, 6)
        ang_mae, pos_mae = compute_head_pose_mae(pred_pose, tgt_pose)
        assert isinstance(ang_mae, float)
        assert isinstance(pos_mae, float)
        print(f"  ✅ compute_head_pose_mae: ang={ang_mae:.4f}deg, pos={pos_mae:.4f}mm")

        # Assembly state F1
        as_logits = torch.randn(B, 3)
        as_targets = torch.randint(0, 3, (B,))
        f1 = compute_assembly_state_f1(as_logits, as_targets)
        assert isinstance(f1, float)
        print(f"  ✅ compute_assembly_state_f1: {f1:.4f}")

        # Error verification
        ev_logits = torch.randn(B, 1)
        ev_targets = torch.randint(0, 2, (B,))
        err_metrics = compute_error_verification_metrics(ev_logits, ev_targets)
        assert "error_ap" in err_metrics
        assert "error_f1" in err_metrics
        print(f"  ✅ compute_error_verification_metrics: {err_metrics}")

        # PSR precision/recall
        psr_dict = {
            "psr_cos_t3": torch.randn(B),
            "psr_valid_t3": torch.ones(B, dtype=torch.bool),
            "psr_cos_t5": torch.randn(B),
            "psr_valid_t5": torch.ones(B, dtype=torch.bool),
        }
        p3, r3, n3 = compute_psr_precision_recall(psr_dict, tolerance=3)
        p5, r5, n5 = compute_psr_precision_recall(psr_dict, tolerance=5)
        print(f"  ✅ compute_psr_precision_recall: t3=({p3:.4f},{r3:.4f},{n3}), t5=({p5:.4f},{r5:.4f},{n5})")

        return True
    except Exception as e:
        print(f"  ❌ Evaluate metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_droppath_fix():
    """Verify Issue B fix: _drop_path is called with correct args."""
    print("[7/7] Verifying Issue B fix (DropPath closure capture)...")
    try:
        import torch
        from model import TemporalConvBlock, _drop_path

        # Create a block and verify it runs without closure capture errors
        block = TemporalConvBlock(in_channels=768, temporal_kernel=3, drop_prob=0.1)

        # Forward pass with training=True (triggers drop_path)
        x = torch.randn(2, 768, 1, 7, 7)
        block.train()  # set training mode to enable DropPath
        out = block(x)  # Uses self.training internally — no explicit training= arg

        print("  ✅ TemporalConvBlock forward OK with training=True")
        print(f"     Input:  {x.shape}")
        print(f"     Output: {out.shape}")
        return True
    except UnboundLocalError as e:
        print(f"  ❌ Issue B not fixed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ DropPath test failed: {e}")
        return False


def main():
    print("=" * 60)
    print("POPW v2/v3 — Smoke Test Suite")
    print("=" * 60)
    print()

    results = []
    results.append(("imports", test_imports()))
    results.append(("config", test_config_values()))
    results.append(("forward", test_model_forward()))
    results.append(("losses", test_losses()))
    results.append(("parameters", test_model_parameters()))
    results.append(("evaluate_metrics", test_evaluate_metrics()))
    results.append(("droppath_fix", test_droppath_fix()))

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = True
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}  {name}")
        if not ok:
            all_passed = False

    print()
    if all_passed:
        print("🎉 All smoke tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed — review output above")
        sys.exit(1)


if __name__ == "__main__":
    main()