"""
Tests for TriAttention KV Cache.
"""

import torch
import pytest
from triattention.cache import TriAttentionCache, StreamingCache, CacheEntry


class TestTriAttentionCache:
    """Tests for TriAttention KV Cache."""

    @pytest.fixture
    def cache(self):
        """Create a test cache."""
        return TriAttentionCache(
            num_kv_heads=8,
            head_dim=128,
            kv_budget=64,
            window_size=32,
            device="cpu",
        )

    def test_init(self):
        """Test cache initialization."""
        cache = TriAttentionCache(
            num_kv_heads=8,
            head_dim=128,
            kv_budget=2048,
            device="cpu",
        )

        assert cache.num_kv_heads == 8
        assert cache.head_dim == 128
        assert cache.kv_budget == 2048
        assert len(cache.keys) == 0

    def test_update_single(self, cache):
        """Test adding a single batch."""
        keys = torch.randn(1, 8, 128)
        values = torch.randn(1, 8, 128)
        positions = torch.tensor([0])

        cache.update(keys, values, positions, layer=0)

        assert len(cache.keys) == 1
        assert cache.current_position == 1

    def test_update_batch(self, cache):
        """Test adding a batch."""
        batch_size = 8
        keys = torch.randn(batch_size, 8, 128)
        values = torch.randn(batch_size, 8, 128)
        positions = torch.arange(batch_size)

        cache.update(keys, values, positions, layer=0)

        assert len(cache.keys) == batch_size
        assert cache.current_position == batch_size

    def test_get_empty(self, cache):
        """Test get on empty cache."""
        keys, values, positions = cache.get()

        assert keys.shape[0] == 0
        assert values.shape[0] == 0
        assert positions.shape[0] == 0

    def test_get_after_update(self, cache):
        """Test get after updates."""
        keys = torch.randn(4, 8, 128)
        values = torch.randn(4, 8, 128)
        positions = torch.arange(4)

        cache.update(keys, values, positions, layer=0)
        got_keys, got_values, got_positions = cache.get()

        assert got_keys.shape[0] == 4
        assert got_positions.tolist() == [0, 1, 2, 3]

    def test_prune(self, cache):
        """Test basic pruning."""
        # Add more entries than budget (10 single-batch updates)
        for i in range(10):
            keys = torch.randn(1, 8, 128)
            values = torch.randn(1, 8, 128)
            cache.update(keys, values, torch.tensor([i]), layer=0)

        assert len(cache.keys) == 10  # 10 updates, each adding 1 entry

        # Prune to 3 entries
        indices = torch.tensor([0, 2, 5])
        cache.prune(indices)

        assert len(cache.keys) == 3

    def test_prune_if_needed_false(self, cache):
        """Test prune_if_needed when under budget."""
        # Add fewer than budget - 4 single-entry batches
        for i in range(4):
            keys = torch.randn(1, 8, 128)
            values = torch.randn(1, 8, 128)
            cache.update(keys, values, torch.tensor([i]), layer=0)

        assert len(cache.keys) == 4
        # tokens_since_prune < window_size, so should not prune
        assert not cache.prune_if_needed(torch.ones(4))

    def test_prune_if_needed_true(self, cache):
        """Test prune_if_needed when over budget."""
        # Add entries to exceed kv_budget=64
        # Each update adds 1 entry (batch_size=1)
        for i in range(70):
            keys = torch.randn(1, 8, 128)
            values = torch.randn(1, 8, 128)
            cache.update(keys, values, torch.tensor([i]), layer=0)

        # Should now exceed window_size and kv_budget
        assert len(cache.keys) == 70
        assert cache.kv_budget == 64
        assert cache.window_size == 32

        # tokens_since_prune=70 >= window_size=32, and len(keys)=70 > kv_budget=64
        scores = torch.randn(70)
        assert cache.prune_if_needed(scores)

    def test_should_prune(self, cache):
        """Test should_prune logic."""
        # Empty cache
        assert not cache.should_prune()

        # Under window size - add 4 batches, each with 1 entry
        for i in range(4):
            keys = torch.randn(1, 8, 128)
            values = torch.randn(1, 8, 128)
            cache.update(keys, values, torch.tensor([i]), layer=0)

        assert not cache.should_prune()
        assert len(cache.keys) == 4

    def test_reset(self, cache):
        """Test cache reset."""
        # Add one batch with 4 entries
        keys = torch.randn(4, 8, 128)
        values = torch.randn(4, 8, 128)
        positions = torch.arange(4)

        cache.update(keys, values, positions, layer=0)
        assert len(cache.keys) == 4  # 4 entries, one per batch item

        cache.reset()
        assert len(cache.keys) == 0
        assert cache.current_position == 0

    def test_get_stats(self, cache):
        """Test stats retrieval."""
        stats = cache.get_stats()

        assert "current_size" in stats
        assert "kv_budget" in stats
        assert "num_prunes" in stats
        assert stats["current_size"] == 0
        assert stats["kv_budget"] == 64


class TestStreamingCache:
    """Tests for streaming cache variant."""

    def test_sink_preserved(self):
        """Test that sink tokens are preserved during pruning."""
        cache = StreamingCache(
            num_kv_heads=8,
            head_dim=128,
            kv_budget=16,
            sink_size=4,
            device="cpu",
        )

        # Add entries (16 entries, one per batch)
        for i in range(16):
            keys = torch.randn(1, 8, 128)
            values = torch.randn(1, 8, 128)
            cache.update(keys, values, torch.tensor([i]), layer=0)

        assert len(cache.keys) == 16

        # Manually prune - should keep sink indices
        indices = torch.tensor([0, 1, 2, 3])  # First 4 positions
        cache.prune(indices)

        # Sink positions should be in the list
        positions_set = set(cache.positions)
        assert 0 in positions_set
        assert 1 in positions_set
        assert 2 in positions_set
        assert 3 in positions_set


class TestCacheEntry:
    """Tests for CacheEntry."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        key = torch.randn(8, 128)
        value = torch.randn(8, 128)

        entry = CacheEntry(
            key=key,
            value=value,
            position=10,
            layer=2,
        )

        assert entry.position == 10
        assert entry.layer == 2
        assert entry.key.shape == key.shape


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
