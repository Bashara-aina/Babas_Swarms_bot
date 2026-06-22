"""Agent 07: CheckpointAgent — file age, sizes, disk usage, corruption check, cleanup."""

from __future__ import annotations
import os
import time
from typing import Any

from ..base_agent import BaseAgent, AgentResult, CheckResult, Verdict
from ..config import CKPT_DIR


class CheckpointAgent(BaseAgent):
    """Monitors checkpoint health: freshness, size, disk, corruption risk."""

    def __init__(self):
        super().__init__("Checkpoint")

    def run(self, ctx: dict[str, Any]) -> AgentResult:
        state = ctx.get("state", {})
        checks: list[CheckResult] = []
        now = time.time()

        epoch = state.get("epoch", 0) or 0
        step = state.get("step", 0) or 0
        training_active = epoch > 0 or step > 0

        ckpt_files = self._scan_checkpoints()
        total_size_mb = sum(f["size_mb"] for f in ckpt_files)

        # CK01: Latest checkpoint freshness
        if ckpt_files:
            latest = ckpt_files[0]
            age_hours = (now - latest["mtime"]) / 3600
            checks.append(CheckResult(
                "CK01", "Checkpoint", "Latest checkpoint freshness",
                Verdict.PASS if age_hours < 1 else Verdict.WARN if age_hours < 6
                else Verdict.FAIL if age_hours < 24 else Verdict.FAIL,
                f"Latest: {latest['name']}, {age_hours:.1f}h old"
            ))
        else:
            checks.append(CheckResult(
                "CK01", "Checkpoint", "Latest checkpoint freshness",
                Verdict.WARN, "No checkpoint files found"
            ))

        # CK02: Total disk usage
        if ckpt_files:
            checks.append(CheckResult(
                "CK02", "Checkpoint", "Checkpoint disk usage",
                Verdict.PASS if total_size_mb < 5000 else Verdict.WARN if total_size_mb < 20000 else Verdict.FAIL,
                f"Total: {total_size_mb:.0f} MB / {len(ckpt_files)} files"
            ))
        else:
            checks.append(CheckResult(
                "CK02", "Checkpoint", "Checkpoint disk usage",
                Verdict.SKIP, "No checkpoint data"
            ))

        # CK03: Stale checkpoint cleanup
        if len(ckpt_files) > 10:
            oldest = ckpt_files[-1]
            oldest_age = (now - oldest["mtime"]) / 3600
            checks.append(CheckResult(
                "CK03", "Checkpoint", "Checkpoint cleanup needed",
                Verdict.WARN if oldest_age > 48 and total_size_mb > 10000 else Verdict.PASS,
                f"{len(ckpt_files)} checkpoints, oldest {oldest_age:.0f}h old"
            ))
        else:
            checks.append(CheckResult(
                "CK03", "Checkpoint", "Checkpoint cleanup needed",
                Verdict.PASS, f"{len(ckpt_files)} checkpoints, no cleanup needed"
            ))

        # CK04: Partial/tmp files
        partial = [f for f in ckpt_files if f["name"].endswith(".tmp") or f["name"].endswith(".part")]
        checks.append(CheckResult(
            "CK04", "Checkpoint", "Partial checkpoint files",
            Verdict.WARN if partial else Verdict.PASS,
            f"{len(partial)} partial/tmp files" if partial else "No partial files"
        ))

        # CK05: Checkpoint size consistency
        if len(ckpt_files) >= 3:
            sizes = [f["size_mb"] for f in ckpt_files[:5]]
            avg_size = sum(sizes) / len(sizes)
            outliers = [s for s in sizes if s < avg_size * 0.5 or s > avg_size * 2]
            checks.append(CheckResult(
                "CK05", "Checkpoint", "Checkpoint size consistency",
                Verdict.WARN if outliers else Verdict.PASS,
                f"Avg: {avg_size:.0f} MB  Outliers: {[f'{s:.1f}' for s in outliers]}" if outliers
                else f"Ckpt sizes consistent, avg={avg_size:.0f} MB"
            ))
        else:
            checks.append(CheckResult(
                "CK05", "Checkpoint", "Checkpoint size consistency",
                Verdict.SKIP, f"Only {len(ckpt_files)} checkpoints"
            ))

        # CK06: Free disk space
        free_gb, total_gb = self._disk_free()
        if free_gb > 0:
            free_ratio = free_gb / total_gb if total_gb > 0 else 0
            checks.append(CheckResult(
                "CK06", "Checkpoint", "Free disk space",
                Verdict.FAIL if free_gb < 10 else Verdict.WARN if free_ratio < 0.1 else Verdict.PASS,
                f"Free: {free_gb:.1f} / {total_gb:.0f} GB ({free_ratio:.0%})"
            ))
        else:
            checks.append(CheckResult(
                "CK06", "Checkpoint", "Free disk space",
                Verdict.SKIP, "Could not get disk space"
            ))

        # CK07: Best checkpoint saved
        best_epoch = state.get("best_epoch")
        if best_epoch is not None:
            best_ckpt = [f for f in ckpt_files if str(best_epoch) in f["name"]]
            checks.append(CheckResult(
                "CK07", "Checkpoint", "Best checkpoint saved",
                Verdict.PASS if best_ckpt else Verdict.WARN,
                f"Best epoch {best_epoch} checkpoint {'saved' if best_ckpt else 'not found'}"
            ))
        else:
            checks.append(CheckResult(
                "CK07", "Checkpoint", "Best checkpoint saved",
                Verdict.INFO, "best_epoch not in state"
            ))

        # CK08: Resume file
        resume_file = CKPT_DIR / "last_checkpoint"
        checks.append(CheckResult(
            "CK08", "Checkpoint", "Resume checkpoint exists",
            Verdict.PASS if resume_file.exists() else Verdict.SKIP,
            "Resume checkpoint exists" if resume_file.exists() else "No resume file (ok for fresh training)"
        ))

        # CK09: Save interval — best-only strategy aware
        # Only best.pth is saved (on val improvement), so file-mtime intervals
        # reflect how often val improves, NOT epoch cadence.
        if training_active and len(ckpt_files) >= 3:
            times = [f["mtime"] for f in ckpt_files[:5]]
            intervals = [times[i] - times[i + 1] for i in range(min(len(times) - 1, 4))]
            avg_interval = (sum(intervals) / len(intervals)) / 60  # minutes
            # With best-only saves, long intervals are expected (no new best model found)
            checks.append(CheckResult(
                "CK09", "Checkpoint", "Checkpoint save interval",
                Verdict.WARN if avg_interval > 240 else Verdict.PASS,
                f"Avg interval: {avg_interval:.0f} min (best-only saves — long = no new best, not stall)"
            ))
        elif len(ckpt_files) >= 3:
            checks.append(CheckResult(
                "CK09", "Checkpoint", "Checkpoint save interval",
                Verdict.FAIL, "Training not active — checkpoints are stale"
            ))
        else:
            checks.append(CheckResult(
                "CK09", "Checkpoint", "Checkpoint save interval",
                Verdict.SKIP, "Not enough checkpoints"
            ))

        return AgentResult(self.name, checks)

    def _scan_checkpoints(self) -> list[dict[str, Any]]:
        """Scan CKPT_DIR for .pth files, return sorted by mtime desc."""
        files: list[dict[str, Any]] = []
        try:
            if not CKPT_DIR.exists():
                return files
            for entry in CKPT_DIR.iterdir():
                if entry.suffix == ".pth":
                    stat = entry.stat()
                    files.append({
                        "name": entry.name,
                        "mtime": stat.st_mtime,
                        "size_mb": stat.st_size / (1024 ** 2),
                    })
            files.sort(key=lambda f: f["mtime"], reverse=True)
        except (OSError, IOError):
            pass
        return files

    @staticmethod
    def _disk_free() -> tuple[float, float]:
        """Return (free_gb, total_gb) for CKPT_DIR filesystem."""
        try:
            stat = os.statvfs(CKPT_DIR)
            free = stat.f_frsize * stat.f_bavail / (1024 ** 3)
            total = stat.f_frsize * stat.f_blocks / (1024 ** 3)
            return free, total
        except OSError:
            return 0.0, 0.0
