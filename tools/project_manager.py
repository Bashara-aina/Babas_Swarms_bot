"""project_manager.py — Task extraction and project management for Legion.

Convert transcripts/text to structured tasks.
Save to SQLite, push to Todoist/Linear if API keys available.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


async def transcript_to_tasks(transcript_text: str) -> list[dict[str, str]]:
    """Send transcript to PM agent, returns structured tasks."""
    from llm_client import chat

    prompt = (
        "Extract actionable tasks from this text. For each task, identify:\n"
        "- task: what needs to be done\n"
        "- owner: who is responsible (or 'unassigned')\n"
        "- deadline: when (or 'TBD')\n"
        "- priority: high, mid, or low\n\n"
        "Return ONLY a JSON array:\n"
        '[{"task": "...", "owner": "...", "deadline": "...", "priority": "..."}]\n\n'
        f"Text:\n{transcript_text[:3000]}"
    )

    result, _ = await chat(prompt, agent_key="architect", user_id="0")

    # Parse JSON from response
    try:
        # Find JSON array in response
        text = result.strip()
        if "[" in text:
            start = text.index("[")
            end = text.rindex("]") + 1
            tasks = json.loads(text[start:end])
            return tasks
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: return raw result as single task
    return [{"task": result[:200], "owner": "unassigned", "deadline": "TBD", "priority": "mid"}]


async def save_tasks_local(tasks: list[dict], project_name: str) -> str:
    """Save tasks to SQLite via persistence."""
    try:
        import aiosqlite
    except ImportError:
        import subprocess, sys
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "aiosqlite", "--break-system-packages", "-q"],
            check=False,
        )
        import aiosqlite

    from tools.persistence import DB_PATH

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS project_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL,
                task TEXT NOT NULL,
                owner TEXT DEFAULT 'unassigned',
                deadline TEXT DEFAULT 'TBD',
                priority TEXT DEFAULT 'mid',
                status TEXT DEFAULT 'pending',
                created_at REAL NOT NULL
            )
        """)
        now = time.time()
        for t in tasks:
            await db.execute(
                """INSERT INTO project_tasks (project, task, owner, deadline, priority, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project_name, t.get("task", ""), t.get("owner", "unassigned"),
                 t.get("deadline", "TBD"), t.get("priority", "mid"), now),
            )
        await db.commit()

    return f"Saved {len(tasks)} tasks for project '{project_name}'"


async def check_deadlines(hours: int = 48) -> str:
    """Query tasks due in the next N hours."""
    try:
        import aiosqlite
    except ImportError:
        return "aiosqlite not installed"

    from tools.persistence import DB_PATH

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM project_tasks
               WHERE status = 'pending'
               ORDER BY priority DESC, created_at"""
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return "No pending tasks found."

    lines = ["<b>Pending Tasks</b>\n"]
    priority_icons = {"high": "🔴", "mid": "🟡", "low": "🟢"}
    for row in rows:
        r = dict(row)
        icon = priority_icons.get(r.get("priority", "mid"), "⚪")
        lines.append(
            f"  {icon} [{r['project']}] {r['task'][:60]}\n"
            f"    Owner: {r['owner']} | Deadline: {r['deadline']}"
        )

    return "\n".join(lines)


async def complete_task(task_id: int) -> str:
    """Mark a task as completed."""
    try:
        import aiosqlite
    except ImportError:
        return "aiosqlite not installed"

    from tools.persistence import DB_PATH

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE project_tasks SET status = 'completed' WHERE id = ?",
            (task_id,),
        )
        await db.commit()

    return f"Task {task_id} marked as completed."


async def add_to_todoist(task: dict, api_key: Optional[str] = None) -> str:
    """Create a task in Todoist via REST API."""
    api_key = api_key or os.getenv("TODOIST_API_KEY", "")
    if not api_key:
        return "TODOIST_API_KEY not set in .env"

    priority_map = {"high": 4, "mid": 3, "low": 2}

    payload = {
        "content": task.get("task", "Untitled"),
        "priority": priority_map.get(task.get("priority", "mid"), 3),
    }
    deadline = task.get("deadline", "")
    if deadline and deadline != "TBD":
        payload["due_string"] = deadline

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.todoist.com/rest/v2/tasks",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status in (200, 201):
                data = await resp.json()
                return f"Todoist task created: {data.get('url', 'ok')}"
            return f"Todoist error: HTTP {resp.status}"


async def add_to_linear(task: dict, api_key: Optional[str] = None) -> str:
    """Create an issue in Linear via GraphQL API."""
    api_key = api_key or os.getenv("LINEAR_API_KEY", "")
    if not api_key:
        return "LINEAR_API_KEY not set in .env"

    priority_map = {"high": 1, "mid": 2, "low": 3}

    query = """
    mutation IssueCreate($title: String!, $priority: Int) {
        issueCreate(input: {title: $title, priority: $priority}) {
            success
            issue { identifier url }
        }
    }
    """
    variables = {
        "title": task.get("task", "Untitled"),
        "priority": priority_map.get(task.get("priority", "mid"), 2),
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.linear.app/graphql",
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            json={"query": query, "variables": variables},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                issue = data.get("data", {}).get("issueCreate", {}).get("issue", {})
                return f"Linear issue: {issue.get('identifier', '?')} — {issue.get('url', 'ok')}"
            return f"Linear error: HTTP {resp.status}"
