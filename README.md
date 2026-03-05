# LegionSwarm 10/10 🤖

**7-Agent AI Swarm controlled via Telegram on your Linux PC**

Every agent uses the best-in-class free model available as of March 2026. From AI training to complex web apps, this system has you covered.

---

## 🎯 Architecture

| Agent | Model | Provider | Best For |
|-------|-------|----------|----------|
| **vision** | gemma3:12b | Local Ollama | Screenshot analysis (privacy-critical) |
| **coding** | Devstral 2 (123B) | OpenRouter free | Agentic multi-file coding (SWE-bench 72.2%) |
| **debug** | GLM-4.7 (355B) | Z.AI free | PyTorch/CUDA error chains (GPQA 85.7%) |
| **math** | GLM-4.7 (355B) | Z.AI free | Symbolic math + verification (AIME 95.7%) |
| **architect** | Qwen3-235B-A22B | Cerebras free | System design (1,500 tok/s, 131K context) |
| **mentor** | Gemini 3.1 Pro | Google AI Studio | Teaching explanations (1M context) |
| **analyst** | Kimi K2 (1T MoE) | Groq free | Data analysis (200+ reasoning steps) |

**Every agent has automatic fallback models** when primary hits rate limits.

---

## ⚡ Features

- **Auto-routing**: Type `/run <task>` and keywords select the best agent
- **Force agent**: `/agent coding write a FastAPI endpoint`
- **Playwright scraping**: `/scrape <url>` extracts page text
- **Screenshots**: `/shot <url>` captures pages as PNG
- **Private vision**: Screenshots never leave your machine
- **Fallback chain**: Automatically switches to backup models on rate limits
- **Open Interpreter**: Every agent executes Python/shell commands locally

---

## 🛠️ Setup

### Prerequisites

- Ubuntu/Debian Linux (tested on 22.04)
- RTX 3060 12GB (or any GPU for local vision model)
- Python 3.10+
- [Ollama](https://ollama.ai) installed

### 1. Clone and Install

```bash
git clone https://github.com/Bashara-aina/Babas_Swarms_bot.git
cd Babas_Swarms_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Get API Keys

| Provider | URL | Notes |
|----------|-----|-------|
| Z.AI | https://bigmodel.cn/usercenter/apikeys | GLM-4.7 for debug + math |
| OpenRouter | https://openrouter.ai/keys | Devstral 2 (add $10 for 1K/day) |
| Cerebras | https://cloud.cerebras.ai | Qwen3-235B, 14,400/day |
| Google AI Studio | https://aistudio.google.com | Use same account as Gemini Pro sub |
| Groq | https://console.groq.com/keys | Kimi K2, 1,000/day |
| Telegram | [@BotFather](https://t.me/botfather) | Create bot, get token |

### 3. Configure Environment

```bash
cp .env.example .env
nano .env
```

Fill in:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
ALLOWED_USER_ID=your_telegram_user_id

ZAI_API_KEY=your_zai_key
OPENROUTER_API_KEY=your_openrouter_key
CEREBRAS_API_KEY=your_cerebras_key
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
```

### 4. Pull Local Model

```bash
ollama pull gemma3:12b
```

### 5. Test Run

```bash
python3 main.py
```

From Telegram:
```
/start
/models
/run calculate the derivative of x^2
```

If it responds, you're good. Press `Ctrl+C`.

### 6. Deploy as Service

```bash
sudo nano /etc/systemd/system/swarm-bot.service
```

Paste:

```ini
[Unit]
Description=LegionSwarm 10/10 Telegram Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/Babas_Swarms_bot
Environment="PATH=/home/YOUR_USERNAME/Babas_Swarms_bot/.venv/bin"
ExecStart=/home/YOUR_USERNAME/Babas_Swarms_bot/.venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` with your actual username.

```bash
sudo systemctl daemon-reload
sudo systemctl enable swarm-bot
sudo systemctl start swarm-bot
sudo journalctl -u swarm-bot -f
```

---

## 💬 Usage Examples

### Coding
```
/run write a python script to scrape product prices from Amazon
```

### Debugging
```
/run my pytorch training crashed with RuntimeError: CUDA out of memory on backward pass
```

### Math
```
/run derive the gradient of f(x,y) = x²y + 3xy² and verify numerically
```

### System Design
```
/run design a microservices architecture for a real-time booking system with payment integration
```

### Learning
```
/run explain transformers and attention mechanism like I'm a beginner
```

### Data Analysis
```
/run analyze this CSV and plot the trend over time
```
*(Then upload your CSV to the chat)*

### Screenshots
```
/shot https://github.com/Bashara-aina/Babas_Swarms_bot
/run vision describe what's in this screenshot
```

---

## 🛡️ Security

- **Single-user only**: `ALLOWED_USER_ID` prevents unauthorized access
- **Local vision**: Screenshots analyzed locally, never sent to APIs
- **Encrypted keys**: Store `.env` safely, never commit to Git
- **Rate limits**: Each provider has daily caps to prevent abuse

---

## 📊 Monitoring

Check API usage:

```bash
# See which agents fire most
sudo journalctl -u swarm-bot --since "1 hour ago" | grep "Detected agent"

# Check for rate limit errors
sudo journalctl -u swarm-bot --since today | grep -i "rate\|limit\|fallback"
```

---

## 🐛 Troubleshooting

### Bot doesn't respond

```bash
sudo systemctl status swarm-bot
sudo journalctl -u swarm-bot -n 50
```

Look for Python tracebacks.

### API key invalid

1. Regenerate key from provider dashboard
2. Update `.env`
3. `sudo systemctl restart swarm-bot`

### Vision agent slow

Pre-load the model:
```bash
ollama run gemma3:12b ""
```

### Hit rate limit

Fallback auto-engages. Check logs:
```bash
sudo journalctl -u swarm-bot | grep fallback
```

---

## 📦 Provider Limits

| Provider | Daily Limit | Notes |
|----------|-------------|-------|
| Z.AI | Reasonable use | GLM-4.7 full model |
| OpenRouter | 50 free / 1,000 with $10 | Devstral 2 + fallbacks |
| Cerebras | 14,400 requests | Shared across 3 agents |
| Google AI Studio | 1,000 (Pro sub) | Auto-applies to API key |
| Groq | 1,000 requests | Kimi K2 |

**Fallback strategy:** Cerebras → OpenRouter → Local Ollama

---

## 📝 License

MIT License - Do whatever you want with it.

---

## 🚀 What's Next

- [ ] Add voice message transcription (Whisper local)
- [ ] Add file upload handling (PDFs, CSVs auto-analyzed)
- [ ] Add conversation memory (Supabase vector store)
- [ ] Add scheduled tasks (cron-like from Telegram)

---

**Built by [@Bashara-aina](https://github.com/Bashara-aina) for real ML research workflows.**
