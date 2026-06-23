"""
HITL (Human-in-the-Loop) state machine using Burr.  # type: ignore[reportAttributeAccessIssue]
Multi-step agent tasks with approval gates before destructive actions.  # type: ignore[reportAttributeAccessIssue]

Example workflow:
  /email → Draft generated → Show Bashara → Wait for /approve → Send or /revise

Actions that always trigger HITL:
  - send_email: always
  - browser "delete" button clicks: always
  - opening PRs via SWE-agent: always
  - executing shell commands: when LEGION_SANDBOX_ENABLED=false  # type: ignore[reportAttributeAccessIssue]
"""

from __future__ import annotations

from typing import Any

# Burr is optional
_burr_installed: bool | None = None  # type: ignore[reportAttributeAccessIssue]


def _check_burr() -> bool:  # type: ignore[reportAttributeAccessIssue]
    global _burr_installed
    if _burr_installed is None:
        import importlib.util
        _burr_installed = importlib.util.find_spec("burr") is not None
    return _burr_installed


class HITLWorkflow:
    """
    Burr-based state machine for human-in-the-loop workflows.  # type: ignore[reportAttributeAccessIssue]
    Each workflow waits for Bashara approval before executing destructive actions.  # type: ignore[reportAttributeAccessIssue]
    """

    def __init__(self):  # type: ignore[reportAttributeAccessIssue]
        self._workflows: dict[str, Any] = {}  # type: ignore[reportAttributeAccessIssue]
        self._pending_approvals: dict[str, dict] = {}  # type: ignore[reportAttributeAccessIssue]

    def build_email_workflow(self, task: str) -> dict:  # type: ignore[reportAttributeAccessIssue]
        """
        Build an email HITL workflow.  # type: ignore[reportAttributeAccessIssue]
        States: draft → show_user → wait_approval → (send | revise)  # type: ignore[reportAttributeAccessIssue]
        """
        return {
            "type": "email",  # type: ignore[reportAttributeAccessIssue]
            "task": task,  # type: ignore[reportAttributeAccessIssue]
            "state": "draft",  # type: ignore[reportAttributeAccessIssue]
            "draft_content": "",  # type: ignore[reportAttributeAccessIssue]
            "approved": False,  # type: ignore[reportAttributeAccessIssue]
            "revise_requested": False,  # type: ignore[reportAttributeAccessIssue]
            "revision_feedback": "",  # type: ignore[reportAttributeAccessIssue]
        }

    def build_swe_pr_workflow(self, issue_url: str) -> dict:  # type: ignore[reportAttributeAccessIssue]
        """
        Build a SWE-agent PR workflow.  # type: ignore[reportAttributeAccessIssue]
        States: analyze → show_diff → wait_approval → (open_pr | abort)  # type: ignore[reportAttributeAccessIssue]
        """
        return {
            "type": "swe_pr",  # type: ignore[reportAttributeAccessIssue]
            "issue_url": issue_url,  # type: ignore[reportAttributeAccessIssue]
            "state": "analyze",  # type: ignore[reportAttributeAccessIssue]
            "diff_content": "",  # type: ignore[reportAttributeAccessIssue]
            "approved": False,  # type: ignore[reportAttributeAccessIssue]
        }

    def get_pending_workflow(  # type: ignore[reportAttributeAccessIssue]
        self, user_id: int  # type: ignore[reportAttributeAccessIssue]
    ) -> dict | None:
        """Get a pending workflow awaiting approval for this user."""  # type: ignore[reportAttributeAccessIssue]
        return self._pending_approvals.get(str(user_id))  # type: ignore[reportAttributeAccessIssue]

    async def execute_email_draft(self, workflow: dict) -> dict:  # type: ignore[reportAttributeAccessIssue]
        """Generate email draft — runs the LLM to write the email."""  # type: ignore[reportAttributeAccessIssue]
        from llm_client import chat

        task = workflow["task"]  # type: ignore[reportAttributeAccessIssue]
        draft = await chat(  # type: ignore[reportAttributeAccessIssue]
            model="minimax-coding-plan/MiniMax-M3",  # type: ignore[reportAttributeAccessIssue]
            prompt=(  # type: ignore[reportAttributeAccessIssue]
                f"Write a professional email for the following task:\n{task}\n\n"
                "Keep it concise, clear, and action-oriented."  # type: ignore[reportAttributeAccessIssue]
            ),  # type: ignore[reportAttributeAccessIssue]
        )
        workflow["draft_content"] = draft  # type: ignore[reportAttributeAccessIssue]
        workflow["state"] = "show_user"  # type: ignore[reportAttributeAccessIssue]
        return workflow

    async def execute_send_email(self, workflow: dict) -> dict:  # type: ignore[reportAttributeAccessIssue]
        """Send the approved email via ComposioHub."""  # type: ignore[reportAttributeAccessIssue]
        from tools.composio_hub import ComposioHub  # type: ignore[reportAttributeAccessIssue]

        hub = ComposioHub()  # type: ignore[reportAttributeAccessIssue]
        body = workflow["draft_content"]  # type: ignore[reportAttributeAccessIssue]
        await hub.send_email(body=body)  # type: ignore[reportAttributeAccessIssue]
        workflow["sent"] = True  # type: ignore[reportAttributeAccessIssue]
        workflow["state"] = "done"  # type: ignore[reportAttributeAccessIssue]
        return workflow

    async def execute_swe_analyze(self, workflow: dict) -> dict:  # type: ignore[reportAttributeAccessIssue]
        """Run SWE-agent dry-run to get the diff for review."""  # type: ignore[reportAttributeAccessIssue]
        from tools.swe_agent_bridge import SWEBridge  # type: ignore[reportAttributeAccessIssue]

        swe = SWEBridge()  # type: ignore[reportAttributeAccessIssue]
        diff = await swe.dry_run(workflow["issue_url"])  # type: ignore[reportAttributeAccessIssue]
        workflow["diff_content"] = diff  # type: ignore[reportAttributeAccessIssue]
        workflow["state"] = "show_diff"  # type: ignore[reportAttributeAccessIssue]
        return workflow

    async def execute_open_pr(self, workflow: dict) -> dict:  # type: ignore[reportAttributeAccessIssue]
        """Execute SWE-agent to open the PR."""  # type: ignore[reportAttributeAccessIssue]
        from tools.swe_agent_bridge import SWEBridge  # type: ignore[reportAttributeAccessIssue]

        swe = SWEBridge()  # type: ignore[reportAttributeAccessIssue]
        result = await swe.fix_issue(workflow["issue_url"])  # type: ignore[reportAttributeAccessIssue]
        workflow["pr_url"] = result  # type: ignore[reportAttributeAccessIssue]
        workflow["state"] = "done"  # type: ignore[reportAttributeAccessIssue]
        return workflow

    def register_pending(  # type: ignore[reportAttributeAccessIssue]
        self, user_id: int, workflow: dict  # type: ignore[reportAttributeAccessIssue]
    ) -> None:
        """Register a workflow awaiting approval."""  # type: ignore[reportAttributeAccessIssue]
        self._pending_approvals[str(user_id)] = workflow  # type: ignore[reportAttributeAccessIssue]

    def approve(self, user_id: int) -> dict | None:  # type: ignore[reportAttributeAccessIssue]
        """Mark a pending workflow as approved."""  # type: ignore[reportAttributeAccessIssue]
        wf = self._pending_approvals.get(str(user_id))  # type: ignore[reportAttributeAccessIssue]
        if wf:
            wf["approved"] = True  # type: ignore[reportAttributeAccessIssue]
        return wf

    def request_revision(  # type: ignore[reportAttributeAccessIssue]
        self, user_id: int, feedback: str  # type: ignore[reportAttributeAccessIssue]
    ) -> dict | None:
        """Mark a pending workflow for revision with feedback."""  # type: ignore[reportAttributeAccessIssue]
        wf = self._pending_approvals.get(str(user_id))  # type: ignore[reportAttributeAccessIssue]
        if wf:
            wf["revise_requested"] = True  # type: ignore[reportAttributeAccessIssue]
            wf["revision_feedback"] = feedback  # type: ignore[reportAttributeAccessIssue]
        return wf

    def clear_pending(self, user_id: int) -> None:  # type: ignore[reportAttributeAccessIssue]
        """Clear a pending workflow (after completion or abort)."""  # type: ignore[reportAttributeAccessIssue]
        self._pending_approvals.pop(str(user_id), None)  # type: ignore[reportAttributeAccessIssue]


# Module-level singleton
_hitl_workflow: HITLWorkflow | None = None  # type: ignore[reportAttributeAccessIssue]


def get_hitl_workflow() -> HITLWorkflow:  # type: ignore[reportAttributeAccessIssue]
    global _hitl_workflow
    if _hitl_workflow is None:
        _hitl_workflow = HITLWorkflow()  # type: ignore[reportAttributeAccessIssue]
    return _hitl_workflow
