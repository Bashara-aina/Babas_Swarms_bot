# LegionSwarm — Cloud-First Multi-Agent AI Workstation via Telegram

## Project Purpose
A Telegram bot that acts as a remote control for my Linux PC. It routes tasks to
cloud LLM providers via litellm (Cerebras, Groq, Gemini, OpenRouter, ZAI) with
local Ollama for vision only. I use it to administer my machine, manage my PyTorch
training project (WorkerNet), run web automation, and perform data science tasks —
all from my iPhone.

## Project Structure
```
~/Babas_Swarms_bot/
├── .env                    # Secrets — NEVER log, commit, or print these
├── main.py                 # Telegram bot (aiogram 3.4+, async, 48+ commands)
├── agents.py               # SINGLE source of truth: models, keywords, fallback chains
├── router.py               # Thin re-export shim → delegates to agents.py
├── llm_client.py           # Cloud LLM client: chat(), agent_loop(), fallback chains
├── computer_agent.py       # Desktop control: screenshot, mouse, keyboard, apps, files
├── task_orchestrator.py    # Task chaining, monitoring, swarm debate orchestrator
├── config/
│   ├── models.yaml         # Provider registry + free model tiers
│   ├── departments.yaml    # 76 agents across 9 departments
│   └── routing_keywords.yaml # 200+ keywords → agent mapping
├── tools/                  # 24 feature modules (swarm, research, email, git, etc.)
├── core/                   # Infrastructure (memory, reliability, orchestration, utils)
├── agents/                 # Department packages (engineering, design, research, etc.)
├── tests/                  # Test suite (6 modules)
├── docs/                   # Design documentation
├── scripts/                # Utility scripts
└── docker-compose.yml      # Redis + ChromaDB services
```

## Tech Stack
- **Bot framework**: aiogram 3.4+ (async, NOT python-telegram-bot)
- **LLM routing**: litellm 1.57+ (cloud-first, multi-provider with fallback chains)
- **Cloud providers**: Cerebras (1500 tok/s), Groq (tool-calling), Gemini (1M ctx), OpenRouter (free tier), ZAI/GLM-4 (reasoning)
- **Local vision**: Ollama gemma3:12b on RTX 3060 (http://localhost:11434)
- **Desktop control**: xdotool, wmctrl, scrot, xclip (Linux system tools)
- **Web automation**: Playwright (headless Chromium, JS-rendered pages)
- **Persistence**: aiosqlite (async SQLite)
- **Env management**: python-dotenv via .env file

## Active Agent Roster
| Agent Key  | Model                             | Task Domain                        |
|------------|-----------------------------------|------------------------------------|
| vision     | ollama_chat/gemma3:12b            | Screenshot analysis, OCR (local)   |
| coding     | groq/llama-3.3-70b-versatile      | Code generation, fast + reliable   |
| debug      | zai/glm-4                         | CoT reasoning, PyTorch errors      |
| math       | zai/glm-4                         | Tensors, gradients, math proofs    |
| architect  | cerebras/qwen-3-235b-a22b         | System design, long context        |
| analyst    | groq/moonshotai/kimi-k2-instruct  | Data analysis, 1T MoE reasoning    |
| computer   | groq/llama-3.3-70b-versatile      | Agentic tool-calling loops         |
| general    | groq/llama-3.3-70b-versatile      | Reliable fallback default          |
| researcher | groq/moonshotai/kimi-k2-instruct  | Academic research, citations       |
| marketer   | groq/llama-3.3-70b-versatile      | Content, social media, campaigns   |
| devops     | groq/llama-3.3-70b-versatile      | Infrastructure, CI/CD, deployment  |
| pm         | cerebras/qwen-3-235b-a22b         | Project management, timelines      |
| humanizer  | groq/llama-3.3-70b-versatile      | Humanising AI-generated text       |
| reviewer   | groq/llama-3.3-70b-versatile      | AI code review, security audit     |

Plus 76 specialized agents across 9 departments (see config/departments.yaml).

## Critical Rules
1. NEVER hardcode TELEGRAM_BOT_TOKEN or ALLOWED_USER_ID — always use os.getenv()
2. ALWAYS check `message.from_user.id == ALLOWED_USER_ID` before processing any command
3. LLM responses must be chunked at 4000 chars for Telegram's API limit
4. Model strings must use `provider/model` format (e.g., `groq/llama-3.3-70b-versatile`, `cerebras/qwen-3-235b-a22b`). For local Ollama: `ollama_chat/model`
5. Ollama is ONLY for vision — never use Ollama as a text/coding fallback
6. Playwright always runs headless=True — this is a headless Linux server environment
7. Always use get_fallback_chain(agent_key) for multi-provider resilience
8. agents.py is the SINGLE source of truth — router.py only re-exports from it

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
Note: Adjust User/WorkingDirectory paths to match your deployment.

## Common Errors I Have Encountered
- `aiogram.exceptions.TelegramBadRequest`: usually caused by unsupported Markdown
  → Fix: escape special chars or use parse_mode="HTML"
- `litellm.RateLimitError`: provider rate limit hit
  → Fix: automatic fallback chain handles this (60s cooldown + next provider)
- Groq outputting XML instead of JSON tool calls
  → Fix: `_parse_groq_xml_tool_call()` in llm_client.py recovers automatically
- `'NoneType' object has no attribute 'keys'`: LLM returns null tool arguments
  → Fix: `json.loads(...) or {}` guard + `if args` checks before `.keys()` calls
- Playwright timeout: headless Chromium needs `--no-sandbox` on Linux without display
  → Fix: launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
- GPU not used by systemd service:
  → Fix: add Environment="CUDA_VISIBLE_DEVICES=0" in the systemd override unit

## Testing Protocol
- Test core commands: /start → /models → /keys → /run → /think → /agent
- Test computer control: /screen → /do → /cmd
- Test tools: /scrape → /research → /swarm → /stats → /maintenance
- Test sessions: /save test → /sessions → /resume test
- Test learning: /learn "use type hints" → /instincts → /forget 1
- Test review: /review main.py → /security_review llm_client.py
- Test orchestration: /orchestrate "build a CLI tool" → /multi_plan "design auth"
- Test audit: /audit 1
- Validate systemd service with: sudo journalctl -u swarm-bot -f
- Check Ollama GPU usage with: watch -n1 nvidia-smi

## Dependencies (requirements.txt)
```
# Core
aiogram>=3.4.0,<4.0.0
python-dotenv>=1.0.0
litellm>=1.57.0
httpx>=0.27.0

# Web scraping
requests>=2.31.0
beautifulsoup4>=4.12.0
playwright>=1.40.0

# Vision / images
pillow>=10.0.0

# Async utilities
aiofiles>=23.2.0
aiohttp>=3.9.0

# System monitoring
psutil>=5.9.0

# Persistence
aiosqlite>=0.20.0

# Document processing
openpyxl>=3.1.0
pdfplumber>=0.10.0
pytesseract>=0.3.10
python-docx>=1.0.0

# Email
aioimaplib>=1.1.0
aiosmtplib>=3.0.0

# RSS + arXiv
feedparser>=6.0.0
arxiv>=2.1.0

# Host machine tools (install separately, not pip):
# sudo apt install xdotool wmctrl scrot xclip xdg-utils
# sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-ind
# playwright install chromium
```

## What NOT to Do
- Do NOT refactor agents.py routing logic without showing me the updated TASK_KEYWORDS dict
- Do NOT remove cloud provider support — this is intentionally cloud-first with Ollama for vision only
- Do NOT add logging of user message content — privacy requirement
- Do NOT use threading — this project is fully async (asyncio)
- Do NOT use Ollama as a text/coding fallback — cloud providers are always preferred
