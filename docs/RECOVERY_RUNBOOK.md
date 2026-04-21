# Recovery Runbook — Legion Swarm Bot

This runbook provides step-by-step recovery procedures for each failure mode.

---

## Runbook 1: Bot Offline (No Response to Messages)

**Priority**: CRITICAL — restore bot functionality immediately.

### Step 1: Check Health Endpoint
```bash
curl http://localhost:8080/health
```
If returns `{"status":"ok"}`, bot is running. Move to Step 2.
If connection refused, bot is not running. Move to Step 3.

### Step 2: Check Telegram Token
```bash
grep TELEGRAM_BOT_TOKEN /home/newadmin/swarm-bot/.env
```
If empty or shows `YOUR_TOKEN_HERE`, token is missing. Obtain from @BotFather.

### Step 3: Restart Bot
```bash
cd /home/newadmin/swarm-bot
pkill -f "python main.py" || true
python main.py &
sleep 5
curl http://localhost:8080/health
```

### Step 4: Verify Commands
Send `/start` to the bot. If no response, check `bot.log` for Python traceback.

---

## Runbook 2: LLM Commands All Fail

**Priority**: HIGH — bot works but LLM-dependent features are down.

### Step 1: Verify API Key
```bash
grep -E "MINIMAX_API_KEY|ANTHROPIC_AUTH_TOKEN" /home/newadmin/swarm-bot/.env
```
If empty, key is not loaded.

### Step 2: Test API Connectivity
```bash
curl -X POST https://api.minimax.io/anthropic/v1/messages \
  -H "Authorization: Bearer $(grep ANTHROPIC_AUTH_TOKEN .env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"model":"MiniMax-M2.7","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```
If returns `401` or `429`, key is invalid or rate-limited.

### Step 3: Rotate Key
1. Log into MiniMax dashboard
2. Generate new API key
3. Edit `.env`: `ANTHROPIC_AUTH_TOKEN=sk-...`
4. Restart bot

### Step 4: Alternative Model
If MiniMax is down, set fallback in `.env`:
```
LEGION_LLM_MODEL=gpt-4o-mini
```
Bot will route to OpenAI until MiniMax recovers.

---

## Runbook 3: Bot Boots But Memory Features Broken

**Priority**: MEDIUM.

### Step 1: Check ChromaDB
```bash
ls -la /home/newadmin/swarm-bot/data/chroma/
```
If directory exists but DB is corrupted, it will be empty or have strange file sizes.

### Step 2: Clear ChromaDB
```bash
pkill -f "python main.py"
rm -rf /home/newadmin/swarm-bot/data/chroma/
python main.py &
```

### Step 3: Verify
After bot starts, `/memory` command should work. Historical memories are lost.

---

## Runbook 4: Commands Silently Not Registered

**Priority**: MEDIUM.

### Step 1: Check Import Errors
```bash
cd /home/newadmin/swarm-bot
python -c "from handlers import register_all_routers"
```
If throws `ModuleNotFoundError` or `AttributeError`, identify which handler is broken.

### Step 2: Check Shared State
```bash
grep -n "_shared\." /home/newadmin/swarm-bot/main.py | head -20
```
Ensure `_shared.ALLOWED_USER_ID`, `_shared._bot`, `_shared._scheduler` are all set before router registration.

### Step 3: Restart
```bash
pkill -f "python main.py"
python main.py &
```

---

## Runbook 5: GitNexus Shows Wrong Results

**Priority**: LOW — only affects code intelligence tools.

### Step 1: Refresh Index
```bash
cd /home/newadmin/swarm-bot
npx gitnexus analyze
```

### Step 2: Verify
```bash
npx gitnexus status
```
Should show `indexed` with recent timestamp.

---

## Runbook 6: Scheduled Tasks Stop Firing

**Priority**: MEDIUM.

### Step 1: Restart Bot
```bash
pkill -f "python main.py"
python main.py &
```

### Step 2: Verify Scheduler
Check `bot.log` for lines like `DailyHarvesterScheduler started` and `ProactiveScheduler started`.

### Step 3: Manually Trigger
Send `/briefing` to bot. If it works, scheduler is likely the issue (tasks not registered properly).

---

## Runbook 7: Sidecar Processes Not Starting

**Priority**: MEDIUM.

### Step 1: Check Node Installation
```bash
node --version
which node
```

### Step 2: Check OpenCode Installation
```bash
opencode --version
which opencode
```

### Step 3: Disable Auto-Launch
If sidecars are not needed, set in `.env`:
```
OPENROUTER_API_KEY=
ANTHROPIC_API_KEY=
```
Bot will skip ruflo sidecar. OpenCode sidecar requires explicit use via `/opencode` command.

---

## Runbook 8: Database Lock Errors

**Priority**: MEDIUM.

### Step 1: Clear Locks
```bash
pkill -f "python main.py"
```

### Step 2: Increase Timeout
Edit `tools/persistence.py` or `tools/memory.py` and add:
```python
conn.execute("PRAGMA busy_timeout = 5000")
```

### Step 3: Restart
```bash
python main.py &
```

---

## Runbook 9: .env Not Loading (CRITICAL)

**Priority**: CRITICAL — bot cannot start.

### Step 1: Check File Encoding
```bash
file /home/newadmin/swarm-bot/.env
hexdump -C /home/newadmin/swarm-bot/.env | head -1
```
Look for `EF BB BF` at start (UTF-8 BOM — bad).

### Step 2: Fix Line Endings
```bash
sed -i 's/\r$//' /home/newadmin/swarm-bot/.env
```

### Step 3: Remove BOM if Present
```bash
sed -i '1s/^\xEF\xBB\xBF//' /home/newadmin/swarm-bot/.env
```

### Step 4: Verify Load
```bash
cd /home/newadmin/swarm-bot
python -c "from dotenv import load_dotenv; from pathlib import Path; print(load_dotenv(Path('.env'))); import os; print(os.getenv('TELEGRAM_BOT_TOKEN'))"
```
Should print `True` and the token value.

---

## Runbook 10: Emergency Full Restart

**Priority**: CRITICAL — use when nothing else works.

```bash
cd /home/newadmin/swarm-bot

# 1. Kill everything
pkill -9 -f "python main.py" || true
pkill -9 -f "node tools/ruflo" || true
pkill -9 -f "opencode serve" || true

# 2. Clear any stale locks
rm -f data/*.sqlite data/*.db 2>/dev/null || true

# 3. Verify .env is intact
head -5 .env

# 4. Restart
python main.py &
sleep 10

# 5. Verify
curl http://localhost:8080/health
tail -20 bot.log
```

---

*Document generated during security audit. Keep this runbook up-to-date with each incident.*