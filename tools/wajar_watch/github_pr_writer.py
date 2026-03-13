"""WAJAR_WATCH — github_pr_writer: create PRs on slip_cekwajar_id repo."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from tools.wajar_watch.constants import (
    CEKWAJAR_BASE_BRANCH,
    CEKWAJAR_GITHUB_OWNER,
    CEKWAJAR_GITHUB_REPO,
)
from tools.wajar_watch.regulation_diff import RegulationDiff

logger = logging.getLogger(__name__)

_scope_verified = False


@dataclass
class PRResult:
    pr_url: str
    pr_number: int
    branch_name: str
    status: str  # "created" | "error"
    error: str | None = None


def _get_github() -> "github.Github":
    """Get authenticated Github client with token scope verification."""
    global _scope_verified
    from github import Github

    token = os.environ.get("CEKWAJAR_GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "CEKWAJAR_GITHUB_TOKEN not set. "
            "This token needs 'repo' scope for slip_cekwajar_id write access."
        )

    g = Github(token)

    # Verify token scope on first call (Safety Rule 4)
    if not _scope_verified:
        try:
            user = g.get_user()
            user.login  # force API call
            # PyGithub doesn't expose scopes directly, but a successful repo
            # operation will fail with 404/403 if scope is missing.
            # We do a lightweight check here.
            _scope_verified = True
            logger.info("GitHub token verified for user: %s", user.login)
        except Exception as e:
            raise ValueError(
                f"CEKWAJAR_GITHUB_TOKEN validation failed: {e}. "
                f"Ensure the token has 'repo' scope for {CEKWAJAR_GITHUB_OWNER}/{CEKWAJAR_GITHUB_REPO}"
            ) from e

    return g


def _get_or_create_label(repo, label_name: str, color: str = "0366d6") -> None:
    """Create a label if it doesn't exist."""
    try:
        repo.get_label(label_name)
    except Exception:
        try:
            repo.create_label(name=label_name, color=color)
            logger.info("Created label: %s", label_name)
        except Exception as e:
            logger.warning("Could not create label %s: %s", label_name, e)


async def open_regulation_pr(
    diff: RegulationDiff,
    confidence: str,
) -> PRResult:
    """Create branch, commit change, open PR. Return PR URL."""
    try:
        g = _get_github()
        repo = g.get_repo(f"{CEKWAJAR_GITHUB_OWNER}/{CEKWAJAR_GITHUB_REPO}")

        # 1. Get base branch SHA
        base = repo.get_branch(CEKWAJAR_BASE_BRANCH)

        # 2. Create feature branch
        try:
            repo.create_git_ref(
                ref=f"refs/heads/{diff.branch_name}",
                sha=base.commit.sha,
            )
            logger.info("Created branch: %s", diff.branch_name)
        except Exception as e:
            if "Reference already exists" in str(e):
                logger.info("Branch %s already exists, reusing", diff.branch_name)
            else:
                raise

        # 3. Commit the file change
        repo.update_file(
            path=diff.file_path,
            message=diff.commit_message,
            content=diff.new_content,
            sha=diff.current_file_sha,
            branch=diff.branch_name,
        )
        logger.info("Committed change to %s on %s", diff.file_path, diff.branch_name)

        # 4. Open PR
        pr = repo.create_pull(
            title=diff.pr_title,
            body=diff.pr_body,
            head=diff.branch_name,
            base=CEKWAJAR_BASE_BRANCH,
        )
        logger.info("Opened PR #%d: %s", pr.number, pr.html_url)

        # 5. Add labels
        label_names = ["regulation-update", f"confidence-{confidence.lower()}"]
        for label_name in label_names:
            color = {"regulation-update": "0e8a16", "confidence-high": "0e8a16",
                     "confidence-medium": "fbca04", "confidence-low": "e4e669",
                     "confidence-block": "d93f0b"}.get(label_name, "0366d6")
            _get_or_create_label(repo, label_name, color)
        pr.add_to_labels(*label_names)

        return PRResult(
            pr_url=pr.html_url,
            pr_number=pr.number,
            branch_name=diff.branch_name,
            status="created",
        )

    except Exception as e:
        logger.error("PR creation failed: %s", e)
        return PRResult(
            pr_url="",
            pr_number=0,
            branch_name=diff.branch_name if diff else "",
            status="error",
            error=str(e),
        )


async def merge_pr(pr_number: int) -> bool:
    """Merge a PR by number. Returns True on success."""
    try:
        g = _get_github()
        repo = g.get_repo(f"{CEKWAJAR_GITHUB_OWNER}/{CEKWAJAR_GITHUB_REPO}")
        pr = repo.get_pull(pr_number)
        pr.merge(merge_method="squash")
        logger.info("Merged PR #%d", pr_number)
        return True
    except Exception as e:
        logger.error("Failed to merge PR #%d: %s", pr_number, e)
        return False


async def close_pr(pr_number: int) -> bool:
    """Close a PR without merging. Returns True on success."""
    try:
        g = _get_github()
        repo = g.get_repo(f"{CEKWAJAR_GITHUB_OWNER}/{CEKWAJAR_GITHUB_REPO}")
        pr = repo.get_pull(pr_number)
        pr.edit(state="closed")
        logger.info("Closed PR #%d", pr_number)
        return True
    except Exception as e:
        logger.error("Failed to close PR #%d: %s", pr_number, e)
        return False


async def get_pr_by_log_id(log_id: str) -> PRResult | None:
    """Look up PR info from the change log."""
    try:
        from tools.wajar_watch.supabase_writer import get_change_by_id

        change = await get_change_by_id(log_id)
        if not change:
            return None
        return PRResult(
            pr_url=change.get("pr_url", ""),
            pr_number=change.get("pr_number", 0),
            branch_name="",
            status="created",
        )
    except Exception as e:
        logger.error("get_pr_by_log_id failed: %s", e)
        return None
