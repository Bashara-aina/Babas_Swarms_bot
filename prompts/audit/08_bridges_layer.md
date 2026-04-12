# AUDIT 08 — Bridges Layer Connectivity
> Paste this entire prompt into a new OpenCode session.
> Goal: every bridge connects to its target service and is imported by at least one handler.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 08 — Bridges Layer Connectivity                   ║
║  Fix: every bridge wired to both its service and its handler    ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — LIST ALL BRIDGES
List every file in bridges/ directory.

STEP 2 — FOR EACH BRIDGE: UPSTREAM CHECK (handler → bridge)
Grep: which handler files import this bridge?
If NO handler imports it → orphan bridge → fix or disable.

STEP 3 — FOR EACH BRIDGE: DOWNSTREAM CHECK (bridge → service)
Find the function in the bridge that makes the actual external call.
Verify it is:
  - Properly async (uses aiohttp/httpx, not requests.get)
  - Has a timeout set
  - Has error handling that propagates to the caller

STEP 4 — VOICEVOX BRIDGE
Find bridges/voicevox*.py or similar.
Expected wire: handlers/voice.py → voicevox bridge → VoiceVox HTTP API
  POST http://localhost:50021/audio_query
  POST http://localhost:50021/synthesis
Verify the bridge returns audio bytes.
Verify handlers/voice.py sends audio with: await update.message.reply_voice(audio_bytes)
If VoiceVox is not running: bridge must catch ConnectionRefusedError and fall back to gTTS.

STEP 5 — GITHUB BRIDGE (if exists)
Find any bridge that calls GitHub API.
Verify handlers/github_intel_handler.py imports and uses it.
Verify GitHub token loaded from env: GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

STEP 6 — WHATSAPP BRIDGE (if exists)
Find bridges/whatsapp*.py.
If it's not yet deployed: add FEATURE_WHATSAPP_ENABLED = False guard in the handler.
If intended to work: verify webhook URL, verify incoming message is normalized
to same format as Telegram update before feeding into main pipeline.

STEP 7 — bridges/__init__.py
Read bridges/__init__.py.
Verify it exports the right class/function names.
Verify no ImportError risks (wrap optional bridge imports in try/except).

STEP 8 — VERIFY
Run: python -c "import bridges; print('bridges OK')"
Fix any ImportError.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
