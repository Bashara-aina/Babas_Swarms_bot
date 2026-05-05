"""System alert webhook handler."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def handle_system_alert(payload: dict[str, Any]) -> None:
    """Handle system alert webhooks (GPU temp, disk usage, etc.).

    Sends Telegram notification when thresholds are exceeded.
    """
    alert_type = payload.get("type", "")
    value = payload.get("value", 0)
    threshold = payload.get("threshold", 0)

    if alert_type == "gpu_temp" and value > threshold:
        msg = f"🔥 GPU temp alert: {value}°C (threshold: {threshold}°C)"
    elif alert_type == "disk_usage" and value > threshold:
        msg = f"💾 Disk usage alert: {value}% (threshold: {threshold}%)"
    else:
        return

    try:
        import handlers.shared as _shared

        if _shared._bot and _shared.ALLOWED_USER_ID:
            await _shared._bot.send_message(_shared.ALLOWED_USER_ID, msg)  # type: ignore[reportGeneralTypeIssues]
    except Exception as e:
        logger.warning("Failed to send system alert notification: %s", e)
