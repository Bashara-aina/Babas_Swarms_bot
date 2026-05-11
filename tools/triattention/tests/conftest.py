"""
Pytest configuration and shared fixtures for triattention tests.
"""

import torch
import pytest


@pytest.fixture
def device():
    """Get compute device."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


@pytest.fixture
def dtype():
    """Get compute dtype."""
    return torch.bfloat16 if torch.cuda.is_available() else torch.float32


@pytest.fixture
def batch_size():
    """Standard batch size for tests."""
    return 4


@pytest.fixture
def seq_len():
    """Standard sequence length for tests."""
    return 128


@pytest.fixture
def num_heads():
    """Standard number of heads."""
    return 8


@pytest.fixture
def num_kv_heads():
    """Standard number of KV heads (for GQA)."""
    return 8


@pytest.fixture
def head_dim():
    """Standard head dimension."""
    return 128


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "cuda: marks tests that require CUDA"
    )
