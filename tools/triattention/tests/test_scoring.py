"""
Tests for TriAttention scoring functions.
"""

import torch
import pytest
import math
from triattention.scoring import (
    compute_trig_score,
    compute_trig_score_batch,
    compute_norm_score,
    compute_combined_score,
    score_keys_at_offsets,
    reconstruct_attention_from_trig_series,
)


class TestTrigScore:
    """Tests for trigonometric series scoring."""

    @pytest.fixture
    def basic_inputs(self):
        """Basic test inputs."""
        q_center = torch.randn(8, 32)  # [num_heads, num_bands]
        k_center = torch.randn(8, 32)
        rope_freqs = torch.pow(
            torch.tensor(10000.0),
            -torch.arange(0, 64, 2, dtype=torch.float32) / 128
        )  # [num_bands]
        return q_center, k_center, rope_freqs

    def test_trig_score_shape(self, basic_inputs):
        """Test that trig score has correct shape."""
        q_center, k_center, rope_freqs = basic_inputs

        score = compute_trig_score(q_center, k_center, rope_freqs, delta=10)

        assert score.shape == (8,)  # [num_heads]

    def test_trig_score_deterministic(self, basic_inputs):
        """Test that trig score is deterministic."""
        q_center, k_center, rope_freqs = basic_inputs

        score1 = compute_trig_score(q_center, k_center, rope_freqs, delta=10)
        score2 = compute_trig_score(q_center, k_center, rope_freqs, delta=10)

        assert torch.allclose(score1, score2)

    def test_trig_score_delta_zero(self, basic_inputs):
        """Test trig score at delta=0."""
        q_center, k_center, rope_freqs = basic_inputs

        score = compute_trig_score(q_center, k_center, rope_freqs, delta=0)

        # At delta=0, cos(φ) part = cos(φ), amplitude = ||Q||*||K||
        # So score = Σ ||Q||*||K|| * cos(φ)
        # cos(0) = 1, so at minimum we should have some signal
        assert score.shape[0] == q_center.shape[0]

    def test_trig_score_batch(self, basic_inputs):
        """Test batch trig score computation."""
        q_center, k_center, rope_freqs = basic_inputs
        deltas = torch.tensor([0, 10, 20, 50, 100])

        scores = compute_trig_score_batch(q_center, k_center, rope_freqs, deltas)

        assert scores.shape == (5, 8)  # [num_keys, num_heads]

    def test_trig_score_batch_matches_single(self, basic_inputs):
        """Test that batch score matches individual computations."""
        q_center, k_center, rope_freqs = basic_inputs

        # Single deltas
        scores_single = [
            compute_trig_score(q_center, k_center, rope_freqs, delta=d)
            for d in [0, 10, 50]
        ]
        scores_single = torch.stack(scores_single)

        # Batch
        deltas = torch.tensor([0, 10, 50])
        scores_batch = compute_trig_score_batch(q_center, k_center, rope_freqs, deltas)

        assert torch.allclose(scores_single, scores_batch)


class TestNormScore:
    """Tests for norm-based scoring."""

    @pytest.fixture
    def norm_inputs(self):
        """Inputs for norm score tests."""
        q_norms = torch.rand(8, 32) * 2  # [num_heads, num_bands]
        k_norms = torch.rand(8, 32) * 2
        mrl = torch.rand(8, 32) * 0.5 + 0.5  # High concentration
        k_center = torch.randn(8, 32) + 1j * torch.randn(8, 32)
        return q_norms, k_norms, mrl, k_center

    def test_norm_score_shape(self, norm_inputs):
        """Test norm score shape."""
        q_norms, k_norms, mrl, k_center = norm_inputs

        score = compute_norm_score(q_norms, k_norms, mrl)

        assert score.shape == (8,)

    def test_norm_score_with_center(self, norm_inputs):
        """Test norm score with k_center."""
        q_norms, k_norms, mrl, k_center = norm_inputs

        score = compute_norm_score(q_norms, k_norms, mrl, k_center=k_center)

        assert score.shape == (8,)

    def test_norm_score_high_concentration(self):
        """Test that norm score is small when concentration is high."""
        q_norms = torch.ones(8, 32) * 0.5
        k_norms = torch.ones(8, 32) * 0.5
        mrl = torch.ones(8, 32) * 0.99  # Very high concentration

        score = compute_norm_score(q_norms, k_norms, mrl)

        # (1 - 0.99) * 0.5 * 0.5 = 0.0025 per band, sum = 0.08
        assert score.mean().item() < 0.1

    def test_norm_score_low_concentration(self):
        """Test that norm score is larger when concentration is low."""
        q_norms = torch.ones(8, 32) * 0.5
        k_norms = torch.ones(8, 32) * 0.5
        mrl = torch.ones(8, 32) * 0.1  # Low concentration

        score = compute_norm_score(q_norms, k_norms, mrl)

        # (1 - 0.1) * 0.5 * 0.5 = 0.225 per band, sum = 7.2
        assert score.mean().item() > 1.0


class TestCombinedScore:
    """Tests for combined scoring."""

    def test_combined_score_shape(self):
        """Test combined score shape."""
        trig = torch.randn(8)
        norm = torch.randn(8)

        combined = compute_combined_score(trig, norm)

        assert combined.shape == (8,)

    def test_combined_score_with_weights(self):
        """Test combined score with head weights."""
        trig = torch.ones(8)
        norm = torch.ones(8) * 0.5
        weights = torch.tensor([1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0])

        combined = compute_combined_score(trig, norm, head_weights=weights)

        assert combined.shape == (8,)
        # Weighted heads should be doubled
        assert torch.allclose(combined[::2], torch.tensor([1.5, 1.5, 1.5, 1.5]))
        assert torch.allclose(combined[1::2], torch.tensor([3.0, 3.0, 3.0, 3.0]))


class TestScoreKeysAtOffsets:
    """Tests for multi-offset scoring."""

    def test_score_keys_at_offsets_shape(self):
        """Test score keys output shape."""
        num_keys = 100
        key_positions = torch.arange(num_keys)
        q_centers = torch.randn(8, 32)
        k_centers = torch.randn(8, 32)
        q_norms = torch.rand(8, 32)
        mrl = torch.rand(8, 32) * 0.5 + 0.5
        rope_freqs = torch.pow(
            torch.tensor(10000.0),
            -torch.arange(0, 64, 2, dtype=torch.float32) / 128
        )

        scores = score_keys_at_offsets(
            key_positions=key_positions,
            q_centers=q_centers,
            k_centers=k_centers,
            q_norms=q_norms,
            mrl=mrl,
            rope_freqs=rope_freqs,
            current_position=1000,
            offsets=[1, 2, 4],
        )

        assert scores.shape == (num_keys,)

    def test_score_keys_at_offsets_only_future(self):
        """Test that only future keys are scored."""
        key_positions = torch.tensor([0, 10, 20, 30])
        q_centers = torch.randn(8, 32)
        k_centers = torch.randn(8, 32)
        q_norms = torch.rand(8, 32)
        mrl = torch.rand(8, 32) * 0.5 + 0.5
        rope_freqs = torch.pow(
            torch.tensor(10000.0),
            -torch.arange(0, 64, 2, dtype=torch.float32) / 128
        )

        scores = score_keys_at_offsets(
            key_positions=key_positions,
            q_centers=q_centers,
            k_centers=k_centers,
            q_norms=q_norms,
            mrl=mrl,
            rope_freqs=rope_freqs,
            current_position=25,
            offsets=[1, 2, 4],
        )

        # Keys at positions 0, 10, 20 should be scored (all have delta > 0)
        # Key at position 30 should NOT be scored (delta <= 0)
        assert scores[0] != 0 or scores[1] != 0 or scores[2] != 0
        assert scores[3] == 0  # Current position, no future offset


class TestReconstructAttention:
    """Tests for attention reconstruction from trig series."""

    def test_reconstruct_shape(self):
        """Test reconstruction output shape."""
        q_center = torch.randn(8, 32)
        k_center = torch.randn(8, 32)
        rope_freqs = torch.pow(
            torch.tensor(10000.0),
            -torch.arange(0, 64, 2, dtype=torch.float32) / 128
        )
        distances = torch.arange(0, 100)

        dist_out, logits = reconstruct_attention_from_trig_series(
            q_center, k_center, rope_freqs, distances
        )

        assert dist_out.shape == distances.shape
        assert logits.shape == (100, 8)  # [num_distances, num_heads]

    def test_reconstruct_distances(self):
        """Test that output distances match input."""
        q_center = torch.randn(8, 32)
        k_center = torch.randn(8, 32)
        rope_freqs = torch.pow(
            torch.tensor(10000.0),
            -torch.arange(0, 64, 2, dtype=torch.float32) / 128
        )
        distances = torch.tensor([0, 10, 20, 50])

        dist_out, logits = reconstruct_attention_from_trig_series(
            q_center, k_center, rope_freqs, distances
        )

        assert torch.equal(dist_out, distances)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
