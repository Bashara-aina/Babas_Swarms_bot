"""Datetime utilities for SwarmBot — JST time helpers.

Consolidated from 6 copies of _jst_now() and 3 copies of _now_jst()
across the codebase into a single canonical location.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytz

_JST_TZ = pytz.timezone("Asia/Tokyo")


def jst_now() -> datetime:
    """Return current time in JST."""
    return datetime.now(_JST_TZ)


def now_jst() -> str:
    """Return current time in JST as formatted string."""
    return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M JST")
