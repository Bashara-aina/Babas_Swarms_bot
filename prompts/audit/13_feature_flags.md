# AUDIT 13 — Feature Flag Audit
> Paste this entire prompt into a new OpenCode session.
> Goal: every disabled feature is explicitly flagged; no permanently dead code masquerading as live.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 13 — Feature Flag Audit                           ║
║  Fix: every disabled feature has an explicit flag + user msg    ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — FIND ALL FEATURE FLAGS
Search for all feature flag patterns:
  grep -rn "= False" . --include="*.py" | grep -i "feature\|enabled\|active\|mode"
  grep -rn "ENABLED = " . --include="*.py"
  grep -rn "# TODO\|# FIXME\|# stub\|# disabled" . --include="*.py"

Build a list of every feature flag found.

STEP 2 — FOR EACH FLAG: IS IT EVER SET TRUE?
For each flag found in Step 1:
  Search if it's ever set to True anywhere in the codebase.
  If NEVER set True → permanently dead feature.

STEP 3 — CLASSIFY EACH DEAD FEATURE
For each permanently dead feature, classify:
  PLANNED    — feature is on the roadmap, should stay as disabled stub
  ABANDONED  — feature was started but abandoned, should be removed or archived
  CONDITIONAL — feature depends on optional service (VoiceVox, ChromaDB), OK to be False

STEP 4 — FIX EACH CLASSIFICATION
  PLANNED features:
    Keep code, add clear flag at top of file:
      FEATURE_X_ENABLED = False  # Planned: implement in v2.0
    Add graceful user message when triggered:
      await update.message.reply_text("Feature coming soon! 🔧")

  ABANDONED features:
    Remove from main.py handler registration
    Move file to archive/ directory (don't delete — preserve history)
    Log in CLEANUP_LOG_v2.md

  CONDITIONAL features (VoiceVox, ChromaDB, etc.):
    Wrap with availability check:
      if not VOICEVOX_AVAILABLE:
          await update.message.reply_text("Voice mode offline. Text only for now.")
          return
    Log at startup: "⚠️ Feature X disabled: optional dependency missing"

STEP 5 — ADD FEATURE STATUS TO /status COMMAND
Find the /status or /stats command handler.
Add a section that shows all feature flags and their current state:
  🟢 Nihongo mode: available
  🔴 VoiceVox TTS: unavailable (service not running)
  🟢 Web search: available
  🟡 WhatsApp bridge: disabled (not deployed)
  🟢 Wiki auto-ingest: available

STEP 6 — VERIFY
Run: grep -rn "= False" . --include="*.py" | grep -i "feature\|enabled"
Verify every result has a corresponding user-facing message when triggered.
Verify no feature silently does nothing.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
