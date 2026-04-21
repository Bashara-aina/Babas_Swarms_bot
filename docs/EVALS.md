# Legiona Agent — Evaluation & Benchmark Procedures

> **Purpose**: Document reproducible benchmarks for the Legiona multi-agent system running on MiniMax-M2.7 with reasoning_split=True.

---

## 1. System Configuration

| Parameter | Value |
|-----------|-------|
| Model | MiniMax-M2.7 |
| Reasoning Split | `reasoning_split=true` (interleaved CoT) |
| Base URL | `https://api.minimax.io/anthropic` |
| Default Temperature | 1.0 |
| Default top_p | 0.95 |
| Default top_k | 40 |
| Primary Client | `lib/legiona/minimax_client.py` |
| Self-Evolution | `lib/legiona/self_evolve.py` |
| Cost Logging | `lib/legiona/memory/cost_log.jsonl` |

---

## 2. Core Metrics Tracked

### Token Efficiency
- `prompt_tokens` — input token count per call
- `completion_tokens` — output token count per call
- `cache_read_input_tokens` — tokens saved via prompt caching
- `input_jpy` / `output_jpy` — cost in Japanese Yen (per 1K tokens)

### Response Quality
- `confidence` — model self-assessment (HIGH / MEDIUM / LOW)
- `verified_from_context` — whether answer is grounded in provided context
- `reasoning_summary` — brief CoT summary from structured output

### Tool Use
- `tool_calls_made` — count and names of tools invoked
- `rounds` — number of tool-call loops to reach final answer
- `reasoning_trace` — per-round reasoning details (when verbose=True)

---

## 3. Benchmark Procedures

### 3.1 Structured Output Validation

**Objective**: Verify M2.7 responds with valid JSON conforming to `LegionaOutput` schema.

**Method**:
```bash
cd /home/newadmin/swarm-bot
python -c "
from lib.legiona.minimax_client import create_structured_completion
import asyncio

async def test():
    result = await create_structured_completion(
        messages=[{'role': 'user', 'content': 'What is 2+2? Just answer.'}],
        preset='coding',
        reasoning_split=True,
    )
    print(f'answer={result.answer}')
    print(f'confidence={result.confidence}')
    assert result.answer, 'Empty answer'
    assert result.confidence in ('HIGH','MEDIUM','LOW')

asyncio.run(test())
"
```

**Pass criteria**: No schema validation errors, `verified_from_context` is False (no context provided), confidence is set.

---

### 3.2 Reasoning Split Verification

**Objective**: Confirm `reasoning_split` is passed to the API via `extra_body`.

**Method** (static check):
```bash
grep -n "extra_body.*reasoning_split" /home/newadmin/swarm-bot/lib/legiona/minimax_client.py
```

**Expected output** (3 occurrences):
```
extra_body={"reasoning_split": reasoning_split}
extra_body={"reasoning_split": reasoning_split}
extra_body={"reasoning_split": reasoning_split}
```

**Live check** — enable verbose logging and inspect the trace:
```bash
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)

from lib.legiona.minimax_client import complete
result = complete(
    messages=[{'role': 'user', 'content': 'Explain why the sky is blue.'}],
    preset='research',
    reasoning_split=True,
    verbose=True,
)
print(result.answer)
" 2>&1 | grep -i 'reasoning'
```

---

### 3.3 Self-Evolution Cycle

**Objective**: Verify `evolve()` reads sessions, generates a rule, and `load_evolved_rules()` prepends it.

**Prerequisites**: Session records must exist in `lib/legiona/memory/sessions.jsonl`.

**Method**:
```bash
cd /home/newadmin/swarm-bot

# 1. Record a dummy session
python -c "
from lib.legiona.self_evolve import record_session
record_session(
    task='test_task',
    tool_calls=[{'function': {'name': 'grep'}}],
    outcome='completed',
    success=True,
)
print('Session recorded')
"

# 2. Run evolution
python -c "
from lib.legiona.self_evolve import evolve, load_evolved_rules
new_rule = evolve(last_n=1)
print(f'evolve() returned: {new_rule}')
rules = load_evolved_rules()
print(f'load_evolved_rules() length: {len(rules)} chars')
assert rules, 'load_evolved_rules() returned empty string'
"

# 3. Verify rules.md was updated
wc -l /home/newadmin/swarm-bot/lib/legiona/memory/rules.md
cat /home/newadmin/swarm-bot/lib/legiona/memory/rules.md | tail -10
```

**Pass criteria**: `evolve()` returns a rule string, `load_evolved_rules()` returns >0 chars, rules.md has new entry.

---

### 3.4 Tool-Call Loop

**Objective**: Verify M2.7 can execute multi-round tool calls with reasoning traces.

**Method**:
```bash
python -c "
from lib.legiona.minimax_client import create_completion_with_tools
import asyncio

async def test():
    # Use a tool that actually does something
    result = await create_completion_with_tools(
        messages=[{'role': 'user', 'content': 'List the files in /home/newadmin/swarm-bot'}],
        preset='coding',
        max_rounds=5,
        verbose=True,
    )
    print(f'rounds={result.rounds}')
    print(f'tool_calls={result.tool_calls_made}')
    print(f'reasoning_trace_count={len(result.reasoning_trace)}')
    assert result.rounds >= 1

asyncio.run(test())
"
```

**Pass criteria**: At least 1 tool call made, reasoning trace captured per round.

---

### 3.5 Streaming Completion

**Objective**: Verify streaming yields reasoning_detail and content tokens separately.

**Method**:
```bash
python -c "
from lib.legiona.minimax_client import stream_complete
import asyncio

async def test():
    reasoning_chunks = 0
    content_chunks = 0
    async for event in stream_complete(
        messages=[{'role': 'user', 'content': 'Count to 3.'}],
        preset='coding',
        reasoning_split=True,
    ):
        if event['reasoning']:
            reasoning_chunks += 1
        if event['content']:
            content_chunks += 1
        if event['done']:
            print(f'done — reasoning_chunks={reasoning_chunks}, content_chunks={content_chunks}')

asyncio.run(test())
"
```

**Pass criteria**: Both reasoning and content chunks observed (reasoning_split interleaves both).

---

### 3.6 Preset Profiles

**Objective**: Verify different sampling presets produce different parameter sets.

**Method**:
```bash
python -c "
from lib.legiona.minimax_client import get_profile

profiles = ['coding', 'research', 'creative', 'debate', 'memory_consolidation']
for p in profiles:
    params = get_profile(p)
    print(f'{p}: temp={params[\"temperature\"]}, top_p={params[\"top_p\"]}, freq_pen={params[\"frequency_penalty\"]}')

# Verify all have reasoning_split default via complete()
# (parameters returned here are from PRESET_PROFILES dict)
"
```

**Pass criteria**: Each profile returns a dict with temperature, top_p, frequency_penalty, presence_penalty.

---

### 3.7 Cost Logging

**Objective**: Verify token usage + ¥ cost appended to cost_log.jsonl after each call.

**Method**:
```bash
cd /home/newadmin/swarm-bot

# Clear existing log
rm -f lib/legiona/memory/cost_log.jsonl

# Make one call
python -c "
from lib.legiona.minimax_client import complete
result = complete([{'role': 'user', 'content': 'Say hello.'}], preset='coding')
print(f'answered: {result.answer[:30]}')
"

# Check log
echo "=== cost_log.jsonl ==="
cat lib/legiona/memory/cost_log.jsonl
```

**Pass criteria**: cost_log.jsonl has one JSON line with `prompt_tokens`, `completion_tokens`, `input_jpy`, `output_jpy`, `total_jpy`.

---

### 3.8 OpenRouter Fallback

**Objective**: Verify fallback=True routes to OpenRouter instead of MiniMax direct.

**Method** (static check):
```bash
grep -n "OPENROUTER_BASE_URL\|OPENROUTER_MODEL\|fallback" /home/newadmin/swarm-bot/lib/legiona/minimax_client.py | head -10
```

**Expected**: `fallback: bool = False` in function signature, `if fallback: return _build_openrouter_client()` in `get_client()`.

---

## 4. Continuous Monitoring

### Weekly Health Check

```bash
cd /home/newadmin/swarm-bot
pytest tests/ -x --asyncio-mode=auto -q 2>&1 | tail -20
```

### Token Cost Tracker

```bash
# Summarize last 7 days of cost_log.jsonl
python -c "
import json
from pathlib import Path
from datetime import datetime, timedelta

log = Path('lib/legiona/memory/cost_log.jsonl')
if not log.exists():
    print('No cost log found')
    exit()

lines = log.read_text().strip().splitlines()
recent = []
cutoff = datetime.now() - timedelta(days=7)
for line in lines:
    rec = json.loads(line)
    ts = datetime.fromisoformat(rec['ts'])
    if ts >= cutoff:
        recent.append(rec)

total_input = sum(r['prompt_tokens'] for r in recent)
total_output = sum(r['completion_tokens'] for r in recent)
total_jpy = sum(r['total_jpy'] for r in recent)

print(f'Last 7 days: {len(recent)} calls')
print(f'Input tokens: {total_input:,}')
print(f'Output tokens: {total_output:,}')
print(f'Total cost: ¥{total_jpy:.2f}')
"
```

---

## 5. Known Limitations

| Issue | Workaround |
|-------|------------|
| `imghdr` deprecated in Python 3.11+ | Image format detected by extension first, fallback to extension-based mime |
| `response_model=` from `instructor` removed | Uses `response_format={"type": "json_object"}` + manual JSON parsing |
| OpenRouter M2.7 slug unverified | Check `https://openrouter.ai/models` before using `OPENROUTER_MODEL` |
| Self-evolution runs synchronously | `evolve()` calls `complete()` which blocks — run in background task if needed |

---

## 6. Revision History

| Date | Change |
|------|--------|
| 2026-04-21 | Initial benchmark procedures documented |