"""
Tests for TriAttention calibration utilities.
"""

import torch
import pytest
from triattention.calibration import (
    CalibrationResult,
    calibrate_from_hidden_states,
    compute_band_frequencies,
    validate_concentration,
)


class TestCalibration:
    """Tests for calibration utilities."""

    @pytest.fixture
    def mock_hidden_states(self):
        """Create mock pre-RoPE hidden states."""
        seq_len, num_heads, head_dim = 128, 8, 128
        # Simple sinusoid-like pattern for testing
        q_hidden = torch.randn(seq_len, num_heads, head_dim)
        k_hidden = torch.randn(seq_len, num_heads, head_dim)
        return q_hidden, k_hidden

    def test_calibrate_from_hidden_states(self, mock_hidden_states):
        """Test calibration from hidden states."""
        q_hidden, k_hidden = mock_hidden_states

        result = calibrate_from_hidden_states(q_hidden, k_hidden)

        assert isinstance(result, CalibrationResult)
        assert result.q_centers.shape == (8, 64)  # num_bands = head_dim // 2
        assert result.k_centers.shape == (8, 64)
        assert result.q_norms.shape == (8, 64)
        assert result.k_norms.shape == (8, 64)
        assert result.mrl.shape == (8, 64)
        assert result.selected_bands.shape == (8, 4)  # default select_bands=4

    def test_calibrate_different_head_dims(self):
        """Test calibration with different head dimensions."""
        seq_len, num_heads, head_dim = 64, 4, 64
        q_hidden = torch.randn(seq_len, num_heads, head_dim)
        k_hidden = torch.randn(seq_len, num_heads, head_dim)

        result = calibrate_from_hidden_states(q_hidden, k_hidden, head_dim=head_dim)

        num_bands = head_dim // 2
        assert result.q_centers.shape == (num_heads, num_bands)

    def test_compute_band_frequencies(self):
        """Test RoPE frequency computation."""
        num_bands = 32
        head_dim = 128

        freqs = compute_band_frequencies(num_bands, head_dim)

        assert freqs.shape == (num_bands,)
        # First frequency should be 1.0 (θ^0)
        assert torch.isclose(freqs[0], torch.tensor(1.0), atol=1e-5)
        # Frequencies should be decreasing
        assert (freqs[1:] <= freqs[:-1]).all()

    def test_compute_band_frequencies_theta(self):
        """Test frequency computation with custom theta."""
        num_bands = 16
        head_dim = 64
        theta = 5000.0

        freqs = compute_band_frequencies(num_bands, head_dim, theta=theta)

        # First frequency should still be 1.0
        assert torch.isclose(freqs[0], torch.tensor(1.0), atol=1e-5)

    def test_validate_concentration_high(self):
        """Test concentration validation with high MRL."""
        mrl = torch.tensor([[0.98, 0.96, 0.94], [0.97, 0.95, 0.93]])
        threshold = 0.95

        result = validate_concentration(mrl, threshold=threshold)

        # 0.95 is NOT > 0.95 (equal doesn't count), so index [1][1] is False
        expected = torch.tensor([[True, True, False], [True, False, False]])
        assert torch.equal(result, expected)

    def test_validate_concentration_low(self):
        """Test concentration validation with low MRL."""
        mrl = torch.tensor([[0.5, 0.6, 0.7], [0.4, 0.5, 0.6]])
        threshold = 0.95

        result = validate_concentration(mrl, threshold=threshold)

        expected = torch.tensor([[False, False, False], [False, False, False]])
        assert torch.equal(result, expected)

    def test_mrl_bounds(self, mock_hidden_states):
        """Test that MRL values are in valid range [0, 1]."""
        q_hidden, k_hidden = mock_hidden_states

        result = calibrate_from_hidden_states(q_hidden, k_hidden)

        assert (result.mrl >= 0).all()
        assert (result.mrl <= 1).all()

    def test_selected_bands_indices_valid(self, mock_hidden_states):
        """Test that selected band indices are within valid range."""
        q_hidden, k_hidden = mock_hidden_states

        result = calibrate_from_hidden_states(q_hidden, k_hidden)

        num_bands = 64
        assert (result.selected_bands >= 0).all()
        assert (result.selected_bands < num_bands).all()


class TestBandFrequencies:
    """Tests for band frequency computation."""

    def test_frequencies_positive(self):
        """Test that all frequencies are positive."""
        freqs = compute_band_frequencies(num_bands=32, head_dim=128)
        assert (freqs > 0).all()

    def test_frequencies_decrease_exponentially(self):
        """Test that frequencies decrease exponentially."""
        freqs = compute_band_frequencies(num_bands=64, head_dim=128)

        # Ratio between consecutive frequencies should be constant
        ratios = freqs[1:] / freqs[:-1]
        # All ratios should be approximately equal (θ^(-2/d))
        assert torch.allclose(ratios, ratios[0].expand_as(ratios), atol=1e-3)

    def test_frequencies_cuda(self):
        """Test frequency computation on CUDA if available."""
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available")

        freqs = compute_band_frequencies(
            num_bands=32,
            head_dim=128,
            device=torch.device("cuda"),
        )
        assert freqs.device.type == "cuda"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
