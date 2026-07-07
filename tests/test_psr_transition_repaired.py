"""
Smoke test for the repaired PSR transition head.

Verifies:
  - Module loads without ImportError
  - Single-batch forward pass with synthetic FPN features
  - Output shape is [B, 12]
  - All output values are finite (no NaN, no Inf)
  - Config toggle (PSR_HEAD_REPAIR = True)
"""

from __future__ import annotations

import sys
import unittest

import torch

# Add src/ to path
sys.path.insert(0, ".")


class TestPSRTransitionRepaired(unittest.TestCase):
    """Smoke tests for the repaired PSR transition model."""

    def setUp(self):
        # Import after potential path setup
        from src.config import PSR_HEAD_REPAIR, PSRConfig

        self.head_repair_enabled = PSR_HEAD_REPAIR
        self.config = PSRConfig()

    def test_config_flag_true(self):
        """PSR_HEAD_REPAIR must be True."""
        self.assertTrue(self.head_repair_enabled)

    def test_module_imports(self):
        """All module components import without error."""
        from src.models.psr_transition_repaired import (
            PSRTransitionModel,
            TransitionHeads,
            TransitionFeatureEncoder,
            CausalTransformer,
        )

        self.assertIsNotNone(PSRTransitionModel)
        self.assertIsNotNone(TransitionHeads)
        self.assertIsNotNone(TransitionFeatureEncoder)
        self.assertIsNotNone(CausalTransformer)

    def test_transition_heads_forward_shape(self):
        """TransitionHeads produces [B, 12] output."""
        from src.models.psr_transition_repaired import TransitionHeads

        heads = TransitionHeads()
        x = torch.randn(4, 256)
        out = heads(x)
        self.assertEqual(out.shape, (4, 12), f"Expected [4, 12], got {out.shape}")

    def test_transition_heads_forward_finite(self):
        """TransitionHeads output is finite (no NaN/Inf)."""
        from src.models.psr_transition_repaired import TransitionHeads

        heads = TransitionHeads()
        x = torch.randn(4, 256)
        out = heads(x)
        self.assertTrue(torch.isfinite(out).all(), "Output contains NaN or Inf")

    def test_transition_heads_zero_input(self):
        """TransitionHeads handles zero input without NaN."""
        from src.models.psr_transition_repaired import TransitionHeads

        heads = TransitionHeads()
        x = torch.zeros(2, 256)
        out = heads(x)
        self.assertTrue(torch.isfinite(out).all(), "Zero input produces NaN or Inf")

    def test_feature_encoder_forward(self):
        """FeatureEncoder maps [B, 768] -> [B, 256]."""
        from src.models.psr_transition_repaired import TransitionFeatureEncoder

        encoder = TransitionFeatureEncoder()
        x = torch.randn(4, 768)
        out = encoder(x)
        self.assertEqual(out.shape, (4, 256))

    def test_causal_transformer_forward(self):
        """CausalTransformer processes [B, T, 256] -> [B, T, 256]."""
        from src.models.psr_transition_repaired import CausalTransformer

        transformer = CausalTransformer()
        x = torch.randn(2, 4, 256)  # T=4
        out = transformer(x)
        self.assertEqual(out.shape, (2, 4, 256))
        self.assertTrue(torch.isfinite(out).all())

    def test_full_model_forward_per_frame(self):
        """Full PSRTransitionModel forward with T=1 (per-frame mode)."""
        from src.models.psr_transition_repaired import PSRTransitionModel

        model = PSRTransitionModel()
        model.eval()

        B = 2
        # Synthetic FPN features: [B, 256, H, W]
        p3 = torch.randn(B, 256, 28, 28)   # H/8
        p4 = torch.randn(B, 256, 14, 14)   # H/16
        p5 = torch.randn(B, 256, 7, 7)     # H/32

        with torch.no_grad():
            logits = model(p3, p4, p5, seq_length=1)

        self.assertEqual(logits.shape, (B, 12), f"Expected [{B}, 12], got {logits.shape}")
        self.assertTrue(torch.isfinite(logits).all(), "Logits contain NaN or Inf")
        # Confidence should be in [0, 1]
        confidence = logits[:, 11:]
        self.assertTrue((confidence >= 0.0).all() and (confidence <= 1.0).all())

    def test_full_model_forward_sequence(self):
        """Full PSRTransitionModel forward with T=2 (sequence mode)."""
        from src.models.psr_transition_repaired import PSRTransitionModel

        model = PSRTransitionModel()
        model.eval()

        B = 4
        T = 2
        # Sequence batch: [B, 256, H, W] with T=2 -> B is B*T, so 4 frames = 2 sequences of 2
        p3 = torch.randn(B, 256, 28, 28)
        p4 = torch.randn(B, 256, 14, 14)
        p5 = torch.randn(B, 256, 7, 7)

        with torch.no_grad():
            logits = model(p3, p4, p5, seq_length=T)

        # After transformer: B//T sequences, each produces [B//T, 12]
        expected_batch = B // T
        self.assertEqual(
            logits.shape, (expected_batch, 12),
            f"Expected [{expected_batch}, 12], got {logits.shape}",
        )
        self.assertTrue(torch.isfinite(logits).all())

    def test_forward_sequence_wrapper(self):
        """forward_sequence handles [B, T, C, H, W] input."""
        from src.models.psr_transition_repaired import PSRTransitionModel

        model = PSRTransitionModel()
        model.eval()

        B, T = 2, 3
        p3_seq = torch.randn(B, T, 256, 28, 28)
        p4_seq = torch.randn(B, T, 256, 14, 14)
        p5_seq = torch.randn(B, T, 256, 7, 7)

        with torch.no_grad():
            logits = model.forward_sequence(p3_seq, p4_seq, p5_seq)

        self.assertEqual(logits.shape, (B, 12), f"Expected [{B}, 12], got {logits.shape}")
        self.assertTrue(torch.isfinite(logits).all())

    def test_config_usage(self):
        """PSRConfig values match the model instantiation parameters."""
        heads = 11
        self.assertEqual(self.config.NUM_COMPONENTS, heads)
        self.assertEqual(self.config.FEAT_DIM, 768)
        self.assertEqual(self.config.HEAD_REPAIR, True)


if __name__ == "__main__":
    unittest.main()
