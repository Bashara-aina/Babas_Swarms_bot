"""Smoke tests for main.py and core bot functionality.

P3-2: Basic test coverage for Legion bot.
"""
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that critical imports work."""
    try:
        import agents
        import computer_agent
        import llm_client
        import main
        from handlers import shared
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_config_loaded():
    """Test that environment configuration is present."""
    import os

    from dotenv import load_dotenv

    load_dotenv()
    assert os.getenv("TELEGRAM_BOT_TOKEN") is not None or os.getenv("BOT_TOKEN") is not None
    assert os.getenv("ALLOWED_USER_ID") is not None or os.getenv("BASHARA_TELEGRAM_ID") is not None


def test_handlers_registered():
    """Test that handler modules exist."""
    try:
        from handlers import (
            admin_handlers,
            ai,
            debate_handlers,
            legion_extras,
            sessions,
            voice,
        )
        assert hasattr(ai, "router")
        assert hasattr(admin_handlers, "router")
        assert hasattr(debate_handlers, "router")
        assert hasattr(voice, "router")
        assert hasattr(sessions, "router")
        assert hasattr(legion_extras, "router")
    except ImportError as e:
        pytest.fail(f"Handler import failed: {e}")


def test_core_modules_exist():
    """Test that core/ modules are accessible."""
    try:
        from core import health_check, observability
        from core.ruflo_manager import start_health_monitor
        assert callable(start_health_monitor)
    except ImportError as e:
        pytest.fail(f"Core module import failed: {e}")


def test_tools_available():
    """Test that key tool modules exist."""
    try:
        from tools import persistence, scheduler
        assert True
    except ImportError as e:
        pytest.fail(f"Tools import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
