# LegionSwarm v3 🤖

**Full autonomous AI agent — controls your Linux PC via Telegram. 100% free APIs, real computer use.**

---

## Architecture

| Agent | Model | Provider | Best For |
|-------|-------|----------|----------|
| **vision** | gemma3:12b | Local Ollama 🔒 | Screenshot analysis (stays on your machine) |
| **coding** | llama-3.3-70b | Groq free | Code generation, fast |
| **debug** | GLM-4 | Z.AI free | PyTorch/CUDA errors (GPQA 85.7%) |
| **math** | GLM-4 | Z.AI free | Tensors, gradients, math (AIME 95.7%) |
| **architect** | Qwen3-235B-A22B | Cerebras free | System design (1,500 tok/s) |
| **analyst** | Kimi K2 (1T MoE) | Groq free | Data analysis, deep reasoning |
| **computer** | llama-3.3-70b | Groq free | Agentic tool-calling loop |
| **general** | llama-3.3-70b | Groq free | Default fallback |

Every agent has automatic fallback chains — no rate limit ever blocks you.

---

## Commands

### Computer Control
| Command | Description |
|---------|-------------|
| `/do <task>` | Full agentic computer control — opens apps, clicks, types, browses |
| `/screen` | Take desktop screenshot → AI analysis |
| `/open <app\|url>` | Open an app or URL |
| `/click <x> <y>` | Click at screen coordinates |
| `/type <text>` | Type text on keyboard |
| `/key <combo>` | Press keyboard shortcut (e.g. `ctrl+c`) |
| `/cmd <shell>` | Run raw shell command |

### AI Agents
| Command | Description |
|---------|-------------|
| `/run <task>` | LLM chat (no computer, fast) |
| `/think <query>` | QwQ deep reasoning mode |
| `/agent <key> <task>` | Force a specific agent |
| `/swarm <task>` | Multi-agent parallel execution |

### Web & Research
| Command | Description |
|---------|-------------|
| `/scrape <url>` | JS-rendered page scrape (Playwright) |
| `/research <topic>` | Deep multi-page web research |

### System
| Command | Description |
|---------|-------------|
| `/stats` | CPU / GPU / RAM usage |
| `/monitor <sec> <cmd>` | Background recurring task with optional alert |
| `/schedule <time> <cmd>` | One-time scheduled task |
| `/tasks` | List background tasks |
| `/cancel <id>` | Cancel a background task |
| `/alert <sec> <cmd> --alert "<condition>"` | Alert when condition is met |
| `/maintenance` | Full system health check |
| `/git` | Git status |

### Bot Management
| Command | Description |
|---------|-------------|
| `/install <packages>` | pip install + auto-restart |
| `/upgrade` | git pull + auto-restart |
| `/models` | Agent roster |
| `/keys` | API key status |

---

## Setup

### Prerequisites

- Ubuntu/Debian Linux (tested 22.04+)
- RTX 3060 12GB (or any GPU for local vision)
- Python 3.10+
- [Ollama](https://ollama.ai) installed

```bash
# System tools for computer control
sudo apt install xdotool wmctrl scrot xclip xdg-utils
sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-ind
```

### Install

```bash
git clone https://github.com/Bashara-aina/Babas_Swarms_bot.git
cd Babas_Swarms_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### API Keys

| Provider | URL | Free Tier |
|----------|-----|-----------|
| Groq | https://console.groq.com/keys | 1,000 req/day |
| Z.AI | https://bigmodel.cn/usercenter/apikeys | Reasonable use |
| Cerebras | https://cloud.cerebras.ai | 14,400 req/day |
| Gemini | https://aistudio.google.com | 1,000 req/day |
| OpenRouter | https://openrouter.ai/keys | 50 free/day |
| Telegram | [@BotFather](https://t.me/botfather) | Free |

### Configure

```bash
cp .env.example .env
nano .env
```

```env
TELEGRAM_BOT_TOKEN=your_bot_token
ALLOWED_USER_ID=your_telegram_user_id

GROQ_API_KEY=your_groq_key
ZAI_API_KEY=your_zai_key
CEREBRAS_API_KEY=your_cerebras_key
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
```

### Pull Vision Model

```bash
ollama pull gemma3:12b
```

### Run

```bash
python3 main.py
```

### Run as Service

```bash
sudo nano /etc/systemd/system/swarm-bot.service
```

```ini
[Unit]
Description=Legion Telegram Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/Babas_Swarms_bot
EnvironmentFile=/home/YOUR_USERNAME/Babas_Swarms_bot/.env
ExecStart=/home/YOUR_USERNAME/Babas_Swarms_bot/.venv/bin/python3 main.py
Restart=always
RestartSec=10
Environment="CUDA_VISIBLE_DEVICES=0"

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable swarm-bot
sudo systemctl start swarm-bot
sudo journalctl -u swarm-bot -f
```

---

## Examples

```
# Open WhatsApp Web and check messages
/do open whatsapp web and read my last 3 messages

# Take a screenshot and analyze
/screen

# Research something
/research latest pytorch 2.x performance improvements

# Monitor GPU temperature every 30s
/monitor 30 nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader --alert "int(result) > 85"

# Write and run code
/do write a python script to plot my training logs and save to ~/plots/

# Git workflow
/do git add -A && git commit -m "update" && git push
```

---

## Security

- **Single-user**: `ALLOWED_USER_ID` blocks everyone else
- **Local vision**: Screenshots analyzed by Ollama locally, never sent to cloud
- **No secrets in logs**: Message content is never logged
- **Shell safety**: Dangerous commands blocked in `/cmd`

---

## Troubleshooting

**Bot not responding**
```bash
sudo journalctl -u swarm-bot -n 50
```

**Screenshot black/fails**
```bash
# Check display
echo $DISPLAY
# Pre-warm vision model
ollama run gemma3:12b ""
```

**Rate limited**
Fallback auto-engages. Check: `sudo journalctl -u swarm-bot | grep fallback`

**Playwright missing**
```bash
playwright install chromium
```

---

**Built by [@Bashara-aina](https://github.com/Bashara-aina)**
