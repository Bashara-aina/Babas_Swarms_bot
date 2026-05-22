"""
SWE-agent Environment — sandbox workspace management.

Manages the isolated workspace where the SWE-agent operates:
- Clones repositories
- Sets up working directory
- Tracks environment state
- Cleans up after run
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class EnvironmentError(Exception):
    """Raised when environment setup or operations fail."""


class CloneError(EnvironmentError):
    """Raised when git clone fails."""


# ---------------------------------------------------------------------------
# Environment config
# ---------------------------------------------------------------------------


@dataclass
class EnvConfig:
    """Configuration for the SWE-agent environment."""

    repo_url: str = ""
    repo_path: str = ""  # Local path to the repository
    commit: str = ""  # Specific commit to checkout (optional)
    branch: str = ""  # Branch to clone (optional)
    instance_id: str = ""  # Unique instance ID
    work_dir: str = ""  # Working directory for this run
    env_vars: dict[str, str] | None = None  # Environment variables to set


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


class Environment:
    """Manages the SWE-agent working environment."""

    def __init__(self, config: EnvConfig) -> None:
        """Initialize environment.

        Args:
            config: Environment configuration
        """
        self.config = config
        self._work_dir: Path | None = None
        self._original_cwd: Path = Path.cwd()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(self) -> Path:
        """Set up the environment.

        Returns:
            Path to the working directory

        Raises:
            CloneError: If git clone fails
            EnvironmentError: If other setup fails
        """
        logger.info("Setting up environment for %s", self.config.instance_id)

        # Create temporary working directory
        self._work_dir = Path(tempfile.mkdtemp(prefix="swe_agent_"))
        self.config.work_dir = str(self._work_dir)

        try:
            if self.config.repo_url:
                self._clone_repo()
            elif self.config.repo_path:
                self._setup_local_repo()
            else:
                logger.warning("No repo_url or repo_path provided - using empty environment")

            # Set working directory as current
            os.chdir(self._work_dir)
            logger.info("Environment ready at %s", self._work_dir)
            return self._work_dir

        except Exception as e:
            logger.exception("Environment setup failed")
            self.cleanup()
            raise EnvironmentError(f"Setup failed: {e}") from e

    def _clone_repo(self) -> None:
        """Clone the repository."""
        if not self.config.repo_url:
            return

        repo_name = self._extract_repo_name(self.config.repo_url)
        target_dir = self._work_dir / repo_name if self._work_dir else Path(tempfile.gettempdir()) / repo_name

        cmd = ["git", "clone"]
        if self.config.branch:
            cmd.extend(["--branch", self.config.branch])
        cmd.extend([self.config.repo_url, str(target_dir)])

        logger.info("Cloning %s to %s", self.config.repo_url, target_dir)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout for clone
            )
            if result.returncode != 0:
                raise CloneError(f"Clone failed: {result.stderr}")

            # Checkout specific commit if provided
            if self.config.commit:
                subprocess.run(
                    ["git", "checkout", self.config.commit],
                    cwd=target_dir,
                    check=True,
                )

            self.config.work_dir = str(target_dir)
            logger.info("Clone complete: %s", target_dir)

        except subprocess.TimeoutExpired:
            raise CloneError("Clone timed out after 5 minutes")
        except Exception as e:
            raise CloneError(f"Clone failed: {e}") from e

    def _setup_local_repo(self) -> None:
        """Set up from local repository (for development/testing)."""
        source = Path(self.config.repo_path).resolve()
        if not source.exists():
            raise EnvironmentError(f"Source repo does not exist: {source}")

        if self._work_dir is None:
            raise EnvironmentError("Working directory not set")

        target = self._work_dir / source.name

        # Copy or symlink
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)

        self.config.work_dir = str(target)
        logger.info("Local repo set up at %s", target)

    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL."""
        # Handle both HTTPS and SSH URLs
        # https://github.com/owner/repo.git -> repo
        # git@github.com:owner/repo.git -> repo
        url = url.rstrip("/").replace(".git", "")

        if "/" in url:
            parts = url.split("/")
            return parts[-1]
        return "repo"

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def get_state(self) -> dict[str, Any]:
        """Get current environment state.

        Returns:
            Dict with working_dir, files, git_status, etc.
        """
        if not self._work_dir:
            return {"working_dir": "", "error": "Environment not set up"}

        state: dict[str, Any] = {
            "working_dir": str(self._work_dir),
            "files": [],
        }

        # List files
        try:
            files = list(self._work_dir.rglob("*"))
            state["files"] = [str(f.relative_to(self._work_dir)) for f in files if f.is_file()]
        except Exception as e:
            state["files_error"] = str(e)

        # Git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self._work_dir,
            )
            state["git_status"] = result.stdout
        except Exception as e:
            state["git_status_error"] = str(e)

        return state

    def set_env_vars(self, env_vars: dict[str, str]) -> None:
        """Set environment variables in the environment.

        Args:
            env_vars: Dict of environment variables
        """
        os.environ.update(env_vars)
        self.config.env_vars = env_vars

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Clean up the environment.

        Removes the temporary working directory and restores original cwd.
        """
        if self._work_dir and self._work_dir.exists():
            try:
                shutil.rmtree(self._work_dir)
                logger.info("Cleaned up %s", self._work_dir)
            except Exception as e:
                logger.warning("Failed to clean up %s: %e", self._work_dir, e)

        # Restore original working directory
        try:
            os.chdir(self._original_cwd)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "Environment":
        """Enter context manager - setup environment."""
        self.setup()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager - cleanup environment."""
        self.cleanup()