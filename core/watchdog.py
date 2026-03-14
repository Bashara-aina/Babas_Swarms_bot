"""Watchdog wrapper — keeps Legion running forever with zero-downtime restarts.

Run this INSTEAD of main.py:
    python core/watchdog.py

The watchdog:
1. Launches main.py as a subprocess
2. Monitors data/.restart_requested flag (written by SelfUpgradeEngine)
3. When flag appears: waits for Telegram to drain, kills main.py, relaunches
4. If main.py crashes: auto-relaunches after 3 seconds
5. Sends Telegram message on every restart (via BOT_TOKEN + ADMIN_USER_ID)

This means the Telegram bot is NEVER truly offline:
- During upgrade: <3 second gap (Telegram long-poll reconnects automatically)
- During crash: <5 second auto-recovery
- You never need to be at your computer
"""
import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [watchdog] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("watchdog")

RESTART_FLAG = Path("data/.restart_requested")
RESTART_FLAG.parent.mkdir(parents=True, exist_ok=True)

CRASH_COOLDOWN = 3      # seconds before relaunch after crash
FLAG_POLL_INTERVAL = 1  # seconds between flag checks
MAX_RESTARTS_PER_HOUR = 20


async def notify_telegram(message: str) -> None:
    """Send a Telegram message to admin on restart events."""
    token = os.getenv("BOT_TOKEN", "")
    admin_id = os.getenv("ADMIN_USER_ID", os.getenv("ALLOWED_USER_ID", ""))
    if not token or not admin_id:
        return
    try:
        import aiohttp
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with aiohttp.ClientSession() as session:
            await session.post(url, json={
                "chat_id": admin_id,
                "text": message,
                "parse_mode": "HTML",
            }, timeout=aiohttp.ClientTimeout(total=10))
    except Exception as e:
        logger.warning("Telegram notify failed: %s", e)


class Watchdog:
    def __init__(self):
        self.proc: subprocess.Popen | None = None
        self.restart_times: list[float] = []
        self.total_restarts = 0
        self.running = True

    def launch(self) -> None:
        """Start main.py as a child process."""
        cmd = [sys.executable, "-u", "main.py"]
        self.proc = subprocess.Popen(
            cmd,
            cwd=Path(".").resolve(),
            env=os.environ.copy(),
        )
        self.total_restarts += 1
        self.restart_times.append(time.time())
        # Clean up old timestamps (keep last hour)
        cutoff = time.time() - 3600
        self.restart_times = [t for t in self.restart_times if t > cutoff]
        logger.info("Launched main.py (pid=%d) restart #%d", self.proc.pid, self.total_restarts)

    def kill(self) -> None:
        """Gracefully terminate main.py."""
        if self.proc and self.proc.poll() is None:
            logger.info("Terminating main.py (pid=%d)", self.proc.pid)
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()

    def is_throttled(self) -> bool:
        """Prevent restart storms."""
        if len(self.restart_times) >= MAX_RESTARTS_PER_HOUR:
            logger.error("Too many restarts (%d/hour). Pausing.", MAX_RESTARTS_PER_HOUR)
            return True
        return False

    async def run(self) -> None:
        """Main watchdog loop."""
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigterm)

        logger.info("👁️  Watchdog started")
        self.launch()

        while self.running:
            await asyncio.sleep(FLAG_POLL_INTERVAL)

            # Check restart flag
            if RESTART_FLAG.exists():
                logger.info("🔄 Restart flag detected — upgrading")
                RESTART_FLAG.unlink(missing_ok=True)
                if not self.is_throttled():
                    self.kill()
                    await asyncio.sleep(1)  # brief drain
                    self.launch()
                    asyncio.ensure_future(
                        notify_telegram(
                            f"🔄 <b>Legion restarted</b> (upgrade)\n"
                            f"Restart #{self.total_restarts} | "
                            f"{time.strftime('%H:%M:%S')}"
                        )
                    )
                continue

            # Check crash
            if self.proc and self.proc.poll() is not None:
                exit_code = self.proc.returncode
                logger.warning("⚠️  main.py exited (code=%d). Restarting in %ds", exit_code, CRASH_COOLDOWN)
                asyncio.ensure_future(
                    notify_telegram(
                        f"⚠️ <b>Legion crashed</b> (code={exit_code})\n"
                        f"Auto-restarting in {CRASH_COOLDOWN}s…"
                    )
                )
                await asyncio.sleep(CRASH_COOLDOWN)
                if not self.is_throttled():
                    self.launch()
                else:
                    asyncio.ensure_future(
                        notify_telegram("🚨 Restart storm detected. Manual intervention needed.")
                    )
                    self.running = False

    def _handle_sigterm(self, signum, frame) -> None:
        logger.info("Watchdog received signal %d — shutting down", signum)
        self.kill()
        self.running = False
        sys.exit(0)


if __name__ == "__main__":
    watchdog = Watchdog()
    asyncio.run(watchdog.run())
