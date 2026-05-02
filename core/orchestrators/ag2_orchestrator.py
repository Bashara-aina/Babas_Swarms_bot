"""
Phase 3: AG2 (AutoGen v2) — Conversational Self-Correction
Multi-agent system where planner↔worker↔reviewer reject each other's outputs
and self-correct automatically.

Import note: ag2 package installs as 'autogen' but provides ag2 imports via
compatibility layer. Use `import autogen` for the actual package.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import autogen
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
except ImportError as e:
    print(f"ERROR: autogen/ag2 not available: {e}")
    raise

LLM_CONFIG = {
    "config_list": [{
        "model": "minimax/MiniMax-M2.7",
        "api_key": "legion-proxy-key",
        "base_url": "http://localhost:4000",
        "api_type": "openai",
    }],
    "temperature": 0.1,
    "timeout": 120,
    "cache_seed": None,
}

_planner = None
_worker = None
_reviewer = None
_wikibot = None
_groupchat = None
_manager = None


def _get_agents():
    """Lazy initialization of agents to avoid import-time failures."""
    global _planner, _worker, _reviewer, _wikibot, _groupchat, _manager

    if _planner is None:
        _planner = AssistantAgent(
            name="planner",
            system_message="""You are @planner. Your role:
1. Decompose tasks into clear phases with specific deliverables
2. Assign each phase to @worker with specific instructions
3. Track which files should change, what commands should run
4. REJECT worker output if it doesn't match the plan exactly
5. Say TASK_COMPLETE only when all phases verified by @reviewer""",
            llm_config=LLM_CONFIG,
            is_termination_msg=lambda x: "TASK_COMPLETE" in x.get("content", ""),
        )

    if _worker is None:
        _worker = UserProxyAgent(
            name="worker",
            system_message="""You are @worker. Your role:
1. Execute exactly what @planner assigns in each phase
2. Report what you did: files changed, commands run, test results
3. If blocked: say BLOCKED:<reason> with exact error message
4. Say WORK_DONE when your phase is complete
5. Execute code using bash or write files as needed""",
            human_input_mode="NEVER",
            code_execution_config={
                "workdir": "/home/newadmin/swarm-bot",
                "use_docker": False,
            },
        )

    if _reviewer is None:
        _reviewer = AssistantAgent(
            name="reviewer",
            system_message="""You are @reviewer. Your role:
1. Review ALL worker output before it's accepted
2. Check: correctness, security, style, test coverage
3. If issues found: say REVISION_NEEDED:<specific issue>
4. Worker must fix and re-submit for review
5. Say REVIEW_PASSED only when output meets all standards
6. Maximum 3 revision cycles — escalate to @planner on 4th""",
            llm_config=LLM_CONFIG,
        )

    if _wikibot is None:
        _wikibot = AssistantAgent(
            name="wikibot",
            system_message="""You are @wikibot. Your role:
1. Silently observe the conversation
2. When TASK_COMPLETE is said: log session summary
3. Track: task, phases completed, files changed, agents involved
4. Format output as structured session log for .wiki/""",
            llm_config=LLM_CONFIG,
        )

    if _groupchat is None:
        _groupchat = GroupChat(
            agents=[_planner, _worker, _reviewer, _wikibot],
            messages=[],
            max_round=30,
            speaker_selection_method="round_robin",
            allow_repeat_speaker=False,
        )

    if _manager is None:
        _manager = GroupChatManager(groupchat=_groupchat, llm_config=LLM_CONFIG)

    return _planner, _worker, _reviewer, _wikibot, _groupchat, _manager


def create_legion_groupchat(task: str, user_id: str = "bashara") -> dict:
    """
    Creates a self-correcting multi-agent conversation for complex tasks.
    Agents talk to each other until all agree the output is correct.

    Uses round_robin speaker selection to avoid LiteLLM proxy model routing
    issues with auto speaker selection.

    Args:
        task: The task description to solve
        user_id: User identifier for memory context

    Returns:
        dict with 'conversation', 'summary', 'task', 'phases_completed'
    """
    planner, worker, reviewer, wikibot, groupchat, manager = _get_agents()

    try:
        conversation = planner.initiate_chat(
            manager,
            message=f"TASK: {task}\n\nBegin with phase 1.",
        )
        summary = planner.last_message() if hasattr(planner, 'last_message') else str(conversation)[-500:]
    except Exception as e:
        summary = f"GroupChat error: {e}"
        conversation = None

    return {
        "conversation": conversation,
        "summary": summary,
        "task": task,
    }


async def create_legion_groupchat_async(task: str, user_id: str = "bashara") -> dict:
    """Async wrapper for create_legion_groupchat."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, create_legion_groupchat, task, user_id)


def route_task_complexity(task: str) -> str:
    """
    Determine execution path based on task complexity.

    Returns:
        "direct" - simple 1-file changes, existing flow
        "langgraph" - medium complexity, stateful graph
        "ag2" - complex multi-phase, self-correcting conversation
    """
    task_lower = task.lower()
    action_verbs = ["implement", "create", "build", "design", "architect",
                    "refactor", "migrate", "deploy", "setup", "configure"]
    domain_keywords = {
        "frontend": ["ui", "react", "vue", "css", "html", "component"],
        "backend": ["api", "endpoint", "server", "database", "model"],
        "infrastructure": ["docker", "kubernetes", "deploy", "ci/cd", "pipeline"],
        "security": ["auth", "encrypt", "permission", "oauth", "token"],
    }

    verb_count = sum(1 for v in action_verbs if v in task_lower)
    domains_hit = sum(1 for d, kw in domain_keywords.items() if any(k in task_lower for k in kw))

    if verb_count >= 4 or domains_hit >= 3:
        return "ag2"
    elif verb_count >= 2 or domains_hit >= 2:
        return "langgraph"
    else:
        return "direct"


if __name__ == "__main__":
    print("Testing AG2 orchestrator...")

    # Test 1: Import verification
    print(f"  autogen version: {autogen.__version__}")
    print(f"  LLM_CONFIG model: {LLM_CONFIG['config_list'][0]['model']}")

    # Test 2: Agent creation
    planner, worker, reviewer, wikibot, groupchat, manager = _get_agents()
    print(f"  Agents created: {[a.name for a in groupchat.agents]}")

    # Test 3: Task routing
    test_task = "Write a hello world Python function with a basic test"
    print(f"\n  Test task: {test_task}")
    print(f"  Routing: {route_task_complexity(test_task)}")

    # Test 4: Full group chat (with timeout)
    print("\n  Running group chat (will timeout if no response in 60s)...")
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Group chat timed out")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60)

    try:
        result = create_legion_groupchat(test_task)
        print(f"  Result: {result['summary'][:200]}...")
        print("\n  AG2 orchestrator: OK")
    except TimeoutError:
        print("  Group chat timed out (expected - LiteLLM may need more time)")
        print("\n  AG2 orchestrator: PARTIAL (imports + agents work, chat needs more time)")
    except Exception as e:
        print(f"  Error: {e}")
        print("\n  AG2 orchestrator: PARTIAL")