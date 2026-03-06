"""
Fix imports in all moved Python files.
Rewrites old flat-module imports to new core.* paths.
Run from the project root: python scripts/fix_imports.py
"""

from __future__ import annotations
import re
from pathlib import Path

# Mapping: old import token → new import token
IMPORT_MAPPINGS: dict[str, str] = {
    # Core modules
    "from interpreter_bridge import": "from core.interpreter_bridge import",
    "import interpreter_bridge": "import core.interpreter_bridge as interpreter_bridge",
    # Utils
    "from formatters import": "from core.utils.formatters import",
    "from streaming_response import": "from core.utils.streaming_response import",
    "from progress_tracker import": "from core.utils.progress_tracker import",
    "from notifications import": "from core.utils.notifications import",
    "from telegram_ui import": "from core.utils.telegram_ui import",
    "from multimodal_processor import": "from core.utils.multimodal_processor import",
    "import formatters": "import core.utils.formatters as formatters",
    "import telegram_ui": "import core.utils.telegram_ui as telegram_ui",
    "import multimodal_processor": "import core.utils.multimodal_processor as multimodal_processor",
    "import notifications": "import core.utils.notifications as notifications",
    "import streaming_response": "import core.utils.streaming_response as streaming_response",
    "import progress_tracker": "import core.utils.progress_tracker as progress_tracker",
    # Tools
    "from computer_control import": "from core.tools.computer_control import",
    "from playwright_agent import": "from core.tools.playwright_agent import",
    "from vscode_bridge import": "from core.tools.vscode_bridge import",
    "import computer_control": "import core.tools.computer_control as computer_control",
    "import playwright_agent": "import core.tools.playwright_agent as playwright_agent",
    "import vscode_bridge": "import core.tools.vscode_bridge as vscode_bridge",
    # Memory
    "from memory.memory_manager import": "from core.memory.memory_manager import",
    "from memory.semantic_cache import": "from core.memory.semantic_cache import",
    "from memory import": "from core.memory import",
    # Reliability
    "from reliability.error_recovery import": "from core.reliability.error_recovery import",
    "from reliability.model_router import": "from core.reliability.model_router import",
    "from reliability import": "from core.reliability import",
    # Orchestration
    "from orchestration.supervisor import": "from core.orchestration.supervisor import",
    "from orchestration.swarm_patterns import": "from core.orchestration.swarm_patterns import",
    "from orchestration import": "from core.orchestration import",
    # Optimization
    "from optimization.usage_tracker import": "from core.optimization.usage_tracker import",
    "from optimization.feedback_learner import": "from core.optimization.feedback_learner import",
    "from optimization import": "from core.optimization import",
    # Observability
    "from observability.metrics import": "from core.observability.metrics import",
    "from observability import": "from core.observability import",
    # Agent registry (old agents.py)
    "from agents import": "from core.agent_registry import",
    "import agents": "import core.agent_registry as agents",
    # Task orchestrator
    "from task_orchestrator import": "from core.nexus_orchestrator import",
    "import task_orchestrator": "import core.nexus_orchestrator as task_orchestrator",
}

SEARCH_PATHS = [
    Path("core"),
    Path("tests"),
    Path("main.py"),
]


def fix_file(filepath: Path) -> int:
    """Return number of replacements made."""
    original = filepath.read_text(encoding="utf-8")
    modified = original
    for old, new in IMPORT_MAPPINGS.items():
        pattern = re.compile(r"^" + re.escape(old), re.MULTILINE)
        modified = pattern.sub(new, modified)
    if modified != original:
        filepath.write_text(modified, encoding="utf-8")
        count = sum(
            len(re.findall(r"^" + re.escape(new), modified, re.MULTILINE))
            for new in IMPORT_MAPPINGS.values()
        )
        return 1
    return 0


def main() -> None:
    changed = 0
    for search_path in SEARCH_PATHS:
        if search_path.is_file():
            changed += fix_file(search_path)
        elif search_path.is_dir():
            for pyfile in search_path.rglob("*.py"):
                if "__pycache__" in str(pyfile):
                    continue
                changed += fix_file(pyfile)
    print(f"✓ Fixed imports in {changed} files")


if __name__ == "__main__":
    main()
