"""Webhook handlers package."""

from core.webhooks.handlers.github import handle_github_pr_merged
from core.webhooks.handlers.system import handle_system_alert

__all__ = ["handle_github_pr_merged", "handle_system_alert"]
