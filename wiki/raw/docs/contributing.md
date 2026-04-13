# Contributing to Legion (Babas Swarms Bot)

This is a personal AI workstation bot, but contributions and suggestions are welcome.

## Adding a New Agent

1. Open `agents.py`
2. Add your agent key + model to `AGENT_MODELS`
3. Add keywords to `TASK_KEYWORDS` so `detect_agent()` routes to it
4. Add a `SYSTEM_PROMPTS` entry in `llm_client.py`
5. Update `DEPLOYMENT.md` with the new agent key

## Adding a New Command Handler

1. Pick the right module in `handlers/` (or create a new one)
2. Create a `Router()` instance in that file
3. Register your handler with `@router.message(Command("yourcommand"))`
4. Add `from handlers.yourmodule import router as yourmodule_router` in `handlers/__init__.py`
5. Call `dp.include_router(yourmodule_router)` in `register_all_routers()`
6. Add the command to the `/start` help text in `handlers/system.py`

## Adding a New Computer Tool

1. Implement the async function in `computer_agent.py`
2. Add a JSON schema entry to `TOOL_DEFINITIONS`
3. Add a dispatch case to `execute_tool()`
4. Add a `_tool_label` entry in `llm_client.py`

## Running Tests

```bash
make install
make test
```

## Linting

```bash
make lint        # check
make format      # auto-fix
```

## Commit Style

Use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` new feature
- `fix:` bug fix
- `chore:` maintenance, tooling
- `docs:` documentation
- `refactor:` code restructure (no behavior change)
- `test:` tests only
