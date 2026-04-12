"""tests/test_nihongo_isolation.py — Per-user nihongo mode isolation tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_nihongo_mode_activation_is_per_user():
    """NihongoModeManager.activate() for user A must NOT affect user B."""
    from skills.nihongo.mode_manager import NihongoModeManager, NihongoSubMode

    user_a = 111111
    user_b = 222222

    # Clear any existing state
    NihongoModeManager.deactivate(user_a)
    NihongoModeManager.deactivate(user_b)

    # Activate for user A only
    NihongoModeManager.activate(user_a, NihongoSubMode.CHAT)

    # User A should be active
    assert NihongoModeManager.is_active(user_a) is True

    # User B should NOT be active (isolation)
    assert NihongoModeManager.is_active(user_b) is False


async def test_nihongo_mode_deactivation_is_per_user():
    """NihongoModeManager.deactivate() for user A must NOT affect user B."""
    from skills.nihongo.mode_manager import NihongoModeManager, NihongoSubMode

    user_a = 111111
    user_b = 222222

    # Activate both
    NihongoModeManager.activate(user_a, NihongoSubMode.CHAT)
    NihongoModeManager.activate(user_b, NihongoSubMode.CHAT)

    # Both should be active
    assert NihongoModeManager.is_active(user_a) is True
    assert NihongoModeManager.is_active(user_b) is True

    # Deactivate user A only
    NihongoModeManager.deactivate(user_a)

    # User A should be inactive
    assert NihongoModeManager.is_active(user_a) is False

    # User B should STILL be active (isolation)
    assert NihongoModeManager.is_active(user_b) is True


async def test_nihongo_sessions_are_independent():
    """Each user gets their own NihongoSession — settings are independent."""
    from skills.nihongo.mode_manager import NihongoModeManager, NihongoSubMode

    user_a = 111111
    user_b = 222222

    # Clear state
    NihongoModeManager.deactivate(user_a)
    NihongoModeManager.deactivate(user_b)

    # User A activates with CHAT mode
    NihongoModeManager.activate(user_a, NihongoSubMode.CHAT)

    # User B activates with QUIZ mode
    NihongoModeManager.activate(user_b, NihongoSubMode.QUIZ)

    session_a = NihongoModeManager.get_session(user_a)
    session_b = NihongoModeManager.get_session(user_b)

    # Sessions have different sub_modes
    assert session_a.sub_mode == NihongoSubMode.CHAT
    assert session_b.sub_mode == NihongoSubMode.QUIZ

    # User A's session is active, user B's session is also active
    assert session_a.active is True
    assert session_b.active is True


async def test_user_id_different_means_isolation():
    """Prove with different user IDs that sessions are completely isolated."""
    from skills.nihongo.mode_manager import NihongoModeManager, NihongoSubMode

    user_1 = 999001
    user_2 = 999002

    # Clear state
    NihongoModeManager.deactivate(user_1)
    NihongoModeManager.deactivate(user_2)

    # User 1 activates nihongo
    NihongoModeManager.activate(user_1, NihongoSubMode.CHAT)

    # User 2 sends a message (checks is_active before routing to nihongo handler)
    # User 2 should NOT be in nihongo mode
    is_user2_active = NihongoModeManager.is_active(user_2)
    assert is_user2_active is False

    # User 1 sends another message — should still be in nihongo mode
    is_user1_active = NihongoModeManager.is_active(user_1)
    assert is_user1_active is True
