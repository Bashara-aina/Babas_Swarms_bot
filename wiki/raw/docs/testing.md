# Legion v4 — Complete Telegram Test Checklist

Copy-paste each command into Telegram. Check ✅ when it works, ❌ when it fails.

---

## TIER 1 — Core Sanity (test first, everything depends on these)

| # | Send this | Expected result |
|---|---|---|
| 1 | `/start` | Shows Legion v4 uptime, key count, all command list |
| 2 | `/keys` | Shows ✅/❌ for each API key (GROQ, Cerebras, ZAI, Gemini, OpenRouter, HF) |
| 3 | `/models` | Shows agent roster table with provider for each agent + key status |
| 4 | `/stats` | Shows CPU%, RAM, GPU (name/util/mem/temp), disk, display |
| 5 | `/git` | Shows last 5 commits + working tree status from ~/swarm-bot |

---

## TIER 2 — AI Chat (tests LLM routing + fallback chain)

### General / Auto-routing
| # | Send this | Expected result |
|---|---|---|
| 6 | `what is PyTorch?` | Chat response, no tool use, ⚡GROQ provider in button |
| 7 | `apa itu gradient descent?` | Responds in Indonesian, ⚡ auto-routing |
| 8 | `explain softmax step by step` | Routed to **math** agent (ZAI/GLM-4) |
| 9 | `debug this: KeyError: 'labels'` | Routed to **debug** agent |
| 10 | `design a REST API for a booking system` | Routed to **architect** agent |
| 11 | `write a Python function to sort a dict by value` | Routed to **coding** agent |
| 12 | `analyze this training loss: [0.8, 0.6, 0.55, 0.56, 0.58]` | Routed to **analyst** agent |

### Forced agent
| # | Send this | Expected result |
|---|---|---|
| 13 | `/agent math prove that softmax sums to 1` | Uses ZAI/GLM-4, shows derivation |
| 14 | `/agent coding write async hello world in Python` | Uses Groq, clean code output |
| 15 | `/agent debug IndexError on line 42` | Uses ZAI/GLM-4, structured debug output |
| 16 | `/agent general what time is it in Tokyo?` | Uses Groq general model |

### Deep thinking
| # | Send this | Expected result |
|---|---|---|
| 17 | `/think should I use focal loss or CE loss for imbalanced IKEA ASM?` | Uses QwQ/debug model, shows `💭 thinking...` + clean answer |

### Run (chat-only mode)
| # | Send this | Expected result |
|---|---|---|
| 18 | `/run explain the difference between FiLM and LoRA` | Chat mode, no computer use, answer from knowledge |

---

## TIER 3 — Shell & Computer Control (tests computer_agent)

### Direct shell
| # | Send this | Expected result |
|---|---|---|
| 19 | `/cmd echo hello world` | Returns `hello world` in a code block |
| 20 | `/cmd nvidia-smi` | GPU info or "No GPU" (if on a non-GPU machine) |
| 21 | `/cmd pwd` | Returns current working directory |
| 22 | `/cmd ls ~/swarm-bot` | Lists files in the swarm-bot folder |
| 23 | `/cmd python3 --version` | Python version string |
| 24 | `/cmd rm -rf /` | **Must be blocked** with dangerous pattern message |

### Screenshot
| # | Send this | Expected result |
|---|---|---|
| 25 | `/screen` | Sends desktop screenshot image + inline buttons |
| 26 | (after /screen) tap **🔍 Analyze screen** | AI describes what's on screen |
| 27 | (after /screen) tap **🖱 Do task on screen** | Prompts for task to perform |

### GUI control
| # | Send this | Expected result |
|---|---|---|
| 28 | `/key super` | Presses Super key (opens Activities/Launcher) |
| 29 | `/key ctrl+alt+t` | Opens terminal (if configured) |
| 30 | `/type hello from Legion` | Types text into focused window |
| 31 | `/click 500 300` | Clicks at screen coordinate 500,300 |
| 32 | `/open https://github.com` | Opens URL in default browser |
| 33 | `/open terminal` | Opens terminal app |

### Keyboard button shortcuts
| # | Send this | Expected result |
|---|---|---|
| 34 | Tap 📸 Screenshot (keyboard) | Same as /screen |
| 35 | Tap ⚡ Shell (keyboard) | Shows /cmd usage hint |
| 36 | Tap ⚙️ Status (keyboard) | Same as /stats |
| 37 | Tap 🐛 Debug (keyboard) | Shows "debug mode — just type your task" |
| 38 | Tap 💻 Code (keyboard) | Shows "coding mode — just type your task" |

---

## TIER 4 — Agentic Loop (/do — multi-step computer use)

| # | Send this | Expected result |
|---|---|---|
| 39 | `/do check my Python version and disk space` | Shows step counter, runs 2 shell commands, returns both results |
| 40 | `/do what's in my swarm-bot folder and any git changes?` | Lists directory + runs git status |
| 41 | `/do take a screenshot and tell me what's open` | Takes screenshot, analyzes it, returns description |
| 42 | `/do run echo 'Legion test' and return the output` | Executes shell, returns output |

---

## TIER 5 — Web & Research

### Scrape
| # | Send this | Expected result |
|---|---|---|
| 43 | `/scrape https://httpbin.org/html` | Returns page title + text content |
| 44 | `/scrape https://arxiv.org/abs/1705.07115` | Extracts abstract + info from Kendall 2018 paper page |

### Deep research
| # | Send this | Expected result |
|---|---|---|
| 45 | `/research PyTorch 2.5 new features` | Multi-source research report (takes 20-40s) |

### arXiv
| # | Send this | Expected result |
|---|---|---|
| 46 | `/paper multi-task learning uncertainty weigh losses` | Returns top 3 papers with title/authors/abstract/ID |
| 47 | `/ask_paper 1705.07115 what is the key equation?` | Downloads Kendall 2018, extracts text, answers the question |

---

## TIER 6 — Second Brain (Memory)

| # | Send this | Expected result |
|---|---|---|
| 48 | `/remember WorkerNet uses FiLM conditioning for pose estimation` | Returns `saved (id: X)` |
| 49 | `/remember focal loss gamma=2 alpha=0.25 for IKEA ASM` | Returns `saved (id: X)` |
| 50 | `/memories` | Lists last 10 saved memories with IDs and timestamps |
| 51 | `/recall FiLM conditioning` | Returns matching memory entries with relevance score |
| 52 | `/recall focal loss` | Returns memory about focal loss params |
| 53 | `/brain_export` | Exports memories to ~/brain Obsidian vault |

---

## TIER 7 — System & DevOps

| # | Send this | Expected result |
|---|---|---|
| 54 | `/gpu` | GPU name, utilization %, VRAM used/total, temp, power |
| 55 | `/maintenance` | Full health check: disk, memory, GPU, services, updates |
| 56 | `/vuln_scan` | pip-audit scan of installed packages for CVEs |

---

## TIER 8 — Scheduler & Background Tasks

| # | Send this | Expected result |
|---|---|---|
| 57 | `/schedule 1 echo scheduled test` | Schedules shell command for 1 minute from now, returns task ID |
| 58 | `/tasks` | Lists all running/scheduled tasks with IDs |
| 59 | `/monitor 30 echo heartbeat` | Starts recurring command every 30s, returns task ID |
| 60 | `/cancel <task_id from #57>` | Cancels the scheduled task |
| 61 | `/alert gpu 60 nvidia-smi --if "'Error' in result"` | Creates conditional alert, returns ID |
| 62 | `/cancel <alert_id from #61>` | Cancels the alert |

---

## TIER 9 — Conversation Threads

| # | Send this | Expected result |
|---|---|---|
| 63 | `/thread workernet` | Sets thread to "workernet", confirms `📌 thread: workernet` |
| 64 | `explain the FiLM module in my codebase` | Responds in context of workernet thread |
| 65 | `/thread` | Shows current active thread name |
| 66 | `/threads` | Lists all active threads with turn counts |

---

## TIER 10 — Multi-Agent Swarm

| # | Send this | Expected result |
|---|---|---|
| 67 | `/swarm analyze pros and cons of focal loss vs cross entropy for multi-task learning` | Shows decomposed subtasks, runs parallel agents, synthesized report |
| 68 | `/build simple REST API with one endpoint that returns current time` | Runs frontend + backend agents in parallel |

---

## TIER 11 — Content & Project Management

### Social media
| # | Send this | Expected result |
|---|---|---|
| 69 | `/post linkedin my WorkerNet model achieves 60% accuracy on IKEA ASM dataset` | LinkedIn post draft in professional tone |
| 70 | `/post tweet WorkerNet multi-task pose estimation is live` | Tweet draft under 280 chars |
| 71 | `/post thread best practices for multi-task learning` | Thread of 3-5 tweets |
| 72 | `/brand_check WorkerNet` | Searches web for brand mentions |

### Project management
| # | Send this | Expected result |
|---|---|---|
| 73 | `/task_from discussed: fix FiLM module by friday, run benchmark monday, Bas handles deployment` | Extracts structured tasks with owners/deadlines |
| 74 | `/tasks_due` | Lists pending tasks sorted by deadline |
| 75 | `/task_done 1` | Marks task #1 as complete |

---

## TIER 12 — Dev Tools

### Project scaffolding
| # | Send this | Expected result |
|---|---|---|
| 76 | `/scaffold fastapi task manager with auth` | Generates FastAPI project structure with files |
| 77 | `/scaffold nextjs portfolio with blog` | Generates Next.js project structure |

---

## TIER 13 — Briefing

| # | Send this | Expected result |
|---|---|---|
| 78 | `/briefing` | Morning briefing: system health + top RSS + memory summary + task reminders |

---

## TIER 14 — Upgrade & Restart

| # | Send this | Expected result | ⚠️ |
|---|---|---|---|
| 79 | `/upgrade` | Pulls from GitHub, shows diff, restarts bot | **Last** — restarts bot |

---

## Quick Smoke Test (10 commands only)

If you want to just verify the bot is alive after a restart, send these in order:

```
/start
/keys
/stats
/cmd echo ok
what is softmax?
/remember test memory entry
/recall test
/screen
/paper focal loss
/gpu
```

All 10 should work without errors.

---

## Common Failures & Fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `All models exhausted` | No API keys loaded | Run `/keys`, check `.env` |
| `auth error` on a provider | Wrong/expired key | Update key in `.env`, restart bot |
| `/screen` fails with "screenshot failed" | DISPLAY not set or scrot missing | `export DISPLAY=:0`, `sudo apt install scrot` |
| `/do` loop stops at 1 step | Tool calling broken in model | ZAI/GLM-4 should be tried first now (fixed in latest push) |
| `/paper` or `/ask_paper` fails with ImportError | arxiv package missing | Run `/install arxiv` |
| `/research` or `/scrape` fails with Playwright error | playwright not installed | `/install playwright` then in terminal: `playwright install chromium` |
| Memory init error | aiosqlite missing or DB corrupt | `/install aiosqlite`, or delete `~/swarm-bot/memory.db` |
| `ZAI_API_KEY not set` | Missing in .env | Add `ZAI_API_KEY=...` to `.env`, restart |
| Scheduler not initialized | aiosqlite missing | `/install aiosqlite` |
