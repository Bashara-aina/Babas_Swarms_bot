# LegionSwarm — Local Autonomous AI Swarm via Telegram

## Project Purpose
A Telegram bot that acts as a remote control for my Linux PC. It routes tasks to
local LLMs via Ollama + Open Interpreter, allowing me to administer my machine,
manage my PyTorch training project (WorkerNet), run web automation, and perform
data science tasks — all from my iPhone.

## Project Structure
```
~/swarm-bot/
├── .env                    # Secrets — NEVER log, commit, or print these
├── main.py                 # Telegram bot (aiogram 3.x, async)
├── agents.py               # Model router + keyword detection
├── interpreter_bridge.py   # Open Interpreter ↔ Ollama bridge
└── playwright_agent.py     # Headless Chromium web automation
```

## Tech Stack
- **Bot framework**: aiogram 3.x (async, NOT python-telegram-bot)
- **LLM execution**: open-interpreter with auto_run=True, safe_mode=False
- **Ollama API**: http://localhost:11434 (always local, never remote)
- **Web automation**: Playwright (headless Chromium, sync_api wrapper)
- **Env management**: python-dotenv via .env file
- **Python venv**: ~/swarm-bot/.venv

## Active Agent Roster
| Agent Key  | Model                    | Task Domain                        |
|------------|--------------------------|------------------------------------|
| vision     | ollama_chat/gemma3:12b   | Screenshot analysis, UI, multimodal|
| coding     | ollama_chat/qwen3.5:35b  | Code generation, MoE               |
| debug      | ollama_chat/exaone-deep:32b | CoT reasoning, PyTorch errors   |
| math       | ollama_chat/phi4         | Tensors, gradients, math           |
| architect  | ollama_chat/llama3.3:70b | High-level design, long context    |

## Critical Rules
1. NEVER hardcode TELEGRAM_BOT_TOKEN or ALLOWED_USER_ID — always use os.getenv()
2. ALWAYS check `message.from_user.id == ALLOWED_USER_ID` before processing any command
3. Open Interpreter responses must be chunked at 4000 chars for Telegram's API limit
4. Ollama model strings must use prefix `ollama_chat/` — not bare model names
5. interpreter.offline = True must always be set (no external API calls)
6. Playwright always runs headless=True — this is a headless Linux server environment

## Systemd Service (reference)
```
[Unit]
Description=LegionSwarm Telegram Bot

[Service]
User=newadmin
WorkingDirectory=/home/newadmin/swarm-bot
ExecStart=/home/newadmin/swarm-bot/.venv/bin/python main.py
EnvironmentFile=/home/newadmin/swarm-bot/.env
Restart=always
Environment="CUDA_VISIBLE_DEVICES=0"

[Install]
WantedBy=multi-user.target
```

## Common Errors I Have Encountered
- `aiogram.exceptions.TelegramBadRequest`: usually caused by unsupported Markdown
  → Fix: escape special chars or use parse_mode="HTML"
- Open Interpreter hanging: caused by model not yet loaded in Ollama
  → Fix: call `ollama run <model> ""` to pre-warm before interpreter.chat()
- Playwright timeout: headless Chromium needs `--no-sandbox` on Linux without display
  → Fix: launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
- GPU not used by systemd service:
  → Fix: add Environment="CUDA_VISIBLE_DEVICES=0" in the systemd override unit

## Testing Protocol
- Test bot commands in this order: /start → /models → /run → /agent → /scrape → /shot
- Validate systemd service with: sudo journalctl -u swarm-bot -f
- Check Ollama GPU usage with: watch -n1 nvidia-smi

## Dependencies (requirements.txt)
```
aiogram>=3.0
open-interpreter
playwright
python-dotenv
asyncio
```

## What NOT to Do
- Do NOT refactor agents.py routing logic without showing me the updated TASK_KEYWORDS dict
- Do NOT suggest cloud deployments — this is intentionally 100% local/offline
- Do NOT add logging of user message content — privacy requirement
- Do NOT use threading — this project is fully async (asyncio)
