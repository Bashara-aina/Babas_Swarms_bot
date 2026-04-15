import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HeartbeatDaemon:
    def __init__(self, interval_minutes: int = 30):
        self.interval = interval_minutes * 60
        self._running = False
        self._last_proactive_check = 0.0

    def _is_active_hours(self) -> bool:
        now = datetime.now()
        hour = now.hour
        return 9 <= hour < 23

    async def _check_proactive_cycle(self, bot, user_id: int) -> None:
        from core.proactive.curiosity_engine import check_and_fire

        await check_and_fire(bot, user_id)

    async def _check_service_health(self) -> None:
        proc = await asyncio.create_subprocess_shell(
            "/usr/bin/systemctl show swarm-bot.service -p ActiveState --value",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        result = stdout.decode().strip()
        if result != "active":
            logger.warning(f"Service health check failed: {repr(result)}")

    async def start(self, bot, user_id: int) -> None:
        self._running = True
        while self._running:
            if self._is_active_hours():
                try:
                    await self._check_proactive_cycle(bot, user_id)
                    await self._check_service_health()
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
            await asyncio.sleep(self.interval)

    def stop(self) -> None:
        self._running = False


_heartbeat = HeartbeatDaemon()
