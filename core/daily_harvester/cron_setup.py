"""Cron setup — install and remove the daily harvester cron job."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

CRON_LINE = (
    "0 21 * * * cd /home/newadmin/swarm-bot && python daily_harvester.py >> logs/harvest_$(date +\\%Y\\%m\\%d).log 2>&1"
)
CRON_LABEL = "# Legion daily harvester"


def setup_cron() -> None:
    """
    Add the daily harvester cron job.

    Cron runs at 21:00 UTC = 04:00 WIB the next day.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    cron_cmd = f"cd {repo_root} && python daily_harvester.py >> logs/harvest_$(date +\\%Y\\%m\\%d).log 2>&1"
    full_cron = f"0 21 * * * {cron_cmd}"

    try:
        # Read current crontab
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
        )
        current = result.stdout if result.returncode == 0 else ""

        if CRON_LABEL in current:
            logger.info("Cron job already installed")
            return

        new_crontab = current.rstrip("\n") + "\n"
        if current:
            new_crontab += "\n"
        new_crontab += f"{CRON_LABEL}\n{full_cron}\n"

        subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
        logger.info("Cron job installed: %s", full_cron)

    except subprocess.CalledProcessError as e:
        logger.error("Failed to setup cron: %s", e)
        raise
    except FileNotFoundError:
        logger.warning("crontab command not found — skipping cron setup")


def remove_cron() -> None:
    """Remove the daily harvester cron job."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
        )
        current = result.stdout if result.returncode == 0 else ""

        lines = current.splitlines()
        new_lines = [ln for ln in lines if CRON_LABEL not in ln and "daily_harvester" not in ln]

        if len(new_lines) == len(lines):
            logger.info("No cron job found to remove")
            return

        new_crontab = "\n".join(new_lines).rstrip("\n") + "\n"
        subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
        logger.info("Cron job removed")

    except subprocess.CalledProcessError as e:
        logger.error("Failed to remove cron: %s", e)
        raise
    except FileNotFoundError:
        logger.warning("crontab command not found — skipping")
