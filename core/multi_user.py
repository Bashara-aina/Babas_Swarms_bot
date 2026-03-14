"""Multi-user access control.

Replaces single ALLOWED_USER_ID with a set of allowed users + role tiers.

Configuration in .env:
    ALLOWED_USER_IDS=123456789,987654321
    ADMIN_USER_IDS=123456789

Or keep ALLOWED_USER_ID (legacy single-user) — both are supported.

Usage:
    from core.multi_user import MultiUserAuth
    auth = MultiUserAuth()
    if not auth.is_allowed(user_id):
        return
    if auth.is_admin(user_id):
        # admin-only commands
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class MultiUserAuth:
    """Manages allowed user IDs and admin roles from environment variables."""

    def __init__(self):
        self._allowed: set[int] = set()
        self._admins: set[int] = set()
        self._load()

    def _load(self) -> None:
        # Support ALLOWED_USER_IDS (comma-separated) or legacy ALLOWED_USER_ID
        ids_str = os.getenv("ALLOWED_USER_IDS") or os.getenv("ALLOWED_USER_ID", "")
        for part in ids_str.replace(" ", "").split(","):
            if part.isdigit():
                self._allowed.add(int(part))

        admin_str = os.getenv("ADMIN_USER_IDS", "")
        for part in admin_str.replace(" ", "").split(","):
            if part.isdigit():
                self._admins.add(int(part))

        # If no explicit admins set, first allowed user is admin
        if not self._admins and self._allowed:
            self._admins.add(min(self._allowed))

        logger.info(
            "MultiUserAuth: %d allowed user(s), %d admin(s)",
            len(self._allowed), len(self._admins),
        )

    def is_allowed(self, user_id: int) -> bool:
        """Returns True if user_id is in the allowed set."""
        return user_id in self._allowed

    def is_admin(self, user_id: int) -> bool:
        """Returns True if user_id has admin privileges."""
        return user_id in self._admins

    def add_user(self, user_id: int, admin: bool = False) -> None:
        """Dynamically add a user at runtime (does not persist to .env)."""
        self._allowed.add(user_id)
        if admin:
            self._admins.add(user_id)
        logger.info("MultiUserAuth: added user %d (admin=%s)", user_id, admin)

    def remove_user(self, user_id: int) -> None:
        """Dynamically remove a user at runtime."""
        self._allowed.discard(user_id)
        self._admins.discard(user_id)
        logger.info("MultiUserAuth: removed user %d", user_id)

    def list_users(self) -> list[dict]:
        """Return all allowed users with their roles."""
        return [
            {"user_id": uid, "role": "admin" if uid in self._admins else "user"}
            for uid in sorted(self._allowed)
        ]

    @property
    def allowed_ids(self) -> set[int]:
        return set(self._allowed)
