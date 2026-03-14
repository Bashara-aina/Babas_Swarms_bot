"""Tests for screenshot tmpfile cleanup."""
import os
import time
import tempfile
import pytest
from unittest.mock import patch
from core.tmp_cleanup import cleanup_screenshots


class TestTmpCleanup:
    def test_deletes_old_files(self, tmp_path):
        old_file = tmp_path / "legion_old.png"
        old_file.write_bytes(b"PNG")
        # Make it appear old
        old_time = time.time() - 3600
        os.utime(old_file, (old_time, old_time))

        with patch("core.tmp_cleanup.SCREENSHOT_PATTERN", str(tmp_path / "legion_*.png")):
            deleted = cleanup_screenshots(max_age_seconds=60)
        assert deleted == 1
        assert not old_file.exists()

    def test_preserves_fresh_files(self, tmp_path):
        fresh_file = tmp_path / "legion_new.png"
        fresh_file.write_bytes(b"PNG")

        with patch("core.tmp_cleanup.SCREENSHOT_PATTERN", str(tmp_path / "legion_*.png")):
            deleted = cleanup_screenshots(max_age_seconds=3600)
        assert deleted == 0
        assert fresh_file.exists()

    def test_empty_dir_returns_zero(self, tmp_path):
        with patch("core.tmp_cleanup.SCREENSHOT_PATTERN", str(tmp_path / "legion_*.png")):
            assert cleanup_screenshots() == 0
