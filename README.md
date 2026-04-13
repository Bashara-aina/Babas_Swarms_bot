# LegionSwarm v10

Multi-agent Telegram copilot for Linux, designed for real workflows: coding, research, memory, automation, and controlled computer actions.

## What this project is

Legion is an async-first AI operating layer built on:

- `aiogram 3.4+` for Telegram command routing
- `litellm` for model/provider routing and fallbacks
- Memory + wiki synthesis for long-horizon context
- Tool bridges (browser, docs, messaging, integrations)

The bot is intended for owner-controlled operation via Telegram with strong environment-driven configuration.

## Current architecture snapshot

- **Entry point**: `main.py`
- **Model + agent routing**: `agents.py`, `llm_client.py`, `core/intent_router.py`
- **System prompt composition**: `core/system_prompt_builder.py`
- **Memory facade**: `core/memory/memory_manager.py`
- **Computer control**: `computer_agent/`
- **Feature handlers**: `handlers/`
- **Knowledge base**: `wiki/`

## Quick start

### 1) Prerequisites

- Linux (Ubuntu/Debian recommended)
- Python `3.11+`
- `ffmpeg` (for media paths)
- Optional but common: Ollama, Playwright, GPU drivers/CUDA

### 2) Install

```bash
git clone https://github.com/Bashara-aina/Babas_Swarms_bot.git
cd Babas_Swarms_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 3) Configure environment

```bash
cp .env.example .env
```

Minimum required variables:

```env
TELEGRAM_BOT_TOKEN=
ALLOWED_USER_ID=
MINIMAX_API_KEY=
GROQ_API_KEY=
```

Then enable optional providers/tools you use (OpenRouter, Anthropic, Gemini, Mem0, Dify, Tavily, Firecrawl, etc.).

### 4) Run

```bash
source .venv/bin/activate
python main.py
```

## Commands (common)

Command coverage evolves quickly; use `/help` inside Telegram for the live list.

Frequently used:

- `/start` – bot status/help
- `/run <task>` – general LLM task
- `/swarm <task>` – multi-agent execution
- `/research <topic>` – deep research flow
- `/screen` – screenshot capture + analysis
- `/do <task>` – computer-action workflow
- `/cmd <shell>` – controlled shell execution
- `/debate <topic>` and `/opinion <question>`
- `/budget` – spend visibility

## Development workflow

```bash
# lint
ruff check .

# tests
pytest tests/ -x --asyncio-mode=auto -q
```

If you touch prompt/routing/memory wiring, run smoke checks for:

- `core/soul_engine.py`
- `core/intent_router.py`
- `core/system_prompt_builder.py`
- `core/debate_engine.py`

## Security and operations

- Never commit `.env`, `.env.local`, `.env.production`, or `secrets.json`
- Keep `ALLOWED_USER_ID` / owner checks enabled in handlers
- Route LLM calls through `llm_client.py` (not direct provider SDK calls)
- Prefer async I/O; avoid blocking operations in handlers

## Project layout

```text
main.py                  # bot startup + router registration
agents.py                # agent/model registry
llm_client.py            # LLM call entrypoint + fallback routing
computer_agent/          # desktop and shell tooling
core/                    # orchestration, memory, prompts, routing
handlers/                # Telegram command handlers
tools/                   # integrations and utility agents
tests/                   # pytest suite
wiki/                    # synthesized project knowledge base
```

## Troubleshooting

**Bot doesn’t respond**

```bash
python main.py
```

or if running under systemd:

```bash
sudo journalctl -u swarm-bot -n 100 -f
```

**Playwright errors**

```bash
playwright install chromium
```

**Provider/rate-limit issues**

Check your API keys and fallback providers in `.env` and `config/models.yaml`.

---

Built by [@Bashara-aina](https://github.com/Bashara-aina)
