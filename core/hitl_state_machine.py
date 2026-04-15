"""
HITL (Human-in-the-Loop) state machine using Burr.
Multi-step agent tasks with approval gates before destructive actions.

Example workflow:
  /email → Draft generated → Show Bashara → Wait for /approve → Send or /revise

Actions that always trigger HITL:
  - send_email: always
  - browser "delete" button clicks: always
  - opening PRs via SWE-agent: always
  - executing shell commands: when LEGION_SANDBOX_ENABLED=false
"""

from __future__ import annotations

import asyncio
from typing import Any

# Burr is optional
_burr_installed: bool | None = None


def _check_burr() -> bool:
    global _burr_installed
    if _burr_installed is None:
        try:
            import burr.core  # noqa: F401

            _burr_installed = True
        except ImportError:
            _burr_installed = False
    return _burr_installed


class HITLWorkflow:
    """
    Burr-based state machine for human-in-the-loop workflows.
    Each workflow waits for Bashara approval before executing destructive actions.
    """

    def __init__(self):
        self._workflows: dict[str, Any] = {}
        self._pending_approvals: dict[str, dict] = {}

    def build_email_workflow(self, task: str) -> dict:
        """
        Build an email HITL workflow.
        States: draft → show_user → wait_approval → (send | revise)
        """
        return {
            "type": "email",
            "task": task,
            "state": "draft",
            "draft_content": "",
            "approved": False,
            "revise_requested": False,
            "revision_feedback": "",
        }

    def build_swe_pr_workflow(self, issue_url: str) -> dict:
        """
        Build a SWE-agent PR workflow.
        States: analyze → show_diff → wait_approval → (open_pr | abort)
        """
        return {
            "type": "swe_pr",
            "issue_url": issue_url,
            "state": "analyze",
            "diff_content": "",
            "approved": False,
        }

    def get_pending_workflow(
        self, user_id: int
    ) -> dict | None:
        """Get a pending workflow awaiting approval for this user."""
        return self._pending_approvals.get(str(user_id))

    async def execute_email_draft(self, workflow: dict) -> dict:
        """Generate email draft — runs the LLM to write the email."""
        from llm_client import chat

        task = workflow["task"]
        draft = await chat(
            model="groq/llama-3.3-70b-versatile",
            prompt=(
                f"Write a professional email for the following task:\n{task}\n\n"
                "Keep it concise, clear, and action-oriented."
            ),
        )
        workflow["draft_content"] = draft
        workflow["state"] = "show_user"
        return workflow

    async def execute_send_email(self, workflow: dict) -> dict:
        """Send the approved email via ComposioHub."""
        from tools.composio_hub import ComposioHub

        hub = ComposioHub()
        body = workflow["draft_content"]
        await hub.send_email(body=body)
        workflow["sent"] = True
        workflow["state"] = "done"
        return workflow

    async def execute_swe_analyze(self, workflow: dict) -> dict:
        """Run SWE-agent dry-run to get the diff for review."""
        from tools.swe_agent_bridge import SWEBridge

        swe = SWEBridge()
        diff = await swe.dry_run(workflow["issue_url"])
        workflow["diff_content"] = diff
        workflow["state"] = "show_diff"
        return workflow

    async def execute_open_pr(self, workflow: dict) -> dict:
        """Execute SWE-agent to open the PR."""
        from tools.swe_agent_bridge import SWEBridge

        swe = SWEBridge()
        result = await swe.fix_issue(workflow["issue_url"])
        workflow["pr_url"] = result
        workflow["state"] = "done"
        return workflow

    def register_pending(
        self, user_id: int, workflow: dict
    ) -> None:
        """Register a workflow awaiting approval."""
        self._pending_approvals[str(user_id)] = workflow

    def approve(self, user_id: int) -> dict | None:
        """Mark a pending workflow as approved."""
        wf = self._pending_approvals.get(str(user_id))
        if wf:
            wf["approved"] = True
        return wf

    def request_revision(
        self, user_id: int, feedback: str
    ) -> dict | None:
        """Mark a pending workflow for revision with feedback."""
        wf = self._pending_approvals.get(str(user_id))
        if wf:
            wf["revise_requested"] = True
            wf["revision_feedback"] = feedback
        return wf

    def clear_pending(self, user_id: int) -> None:
        """Clear a pending workflow (after completion or abort)."""
        self._pending_approvals.pop(str(user_id), None)


# Module-level singleton
_hitl_workflow: HITLWorkflow | None = None


def get_hitl_workflow() -> HITLWorkflow:
    global _hitl_workflow
    if _hitl_workflow is None:
        _hitl_workflow = HITLWorkflow()
    return _hitl_workflow
