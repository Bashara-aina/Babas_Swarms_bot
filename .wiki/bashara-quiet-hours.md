---
title: bashara-quiet-hours
domain: proactive-intelligence
impact_score: 8
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 280
---

# Bashara Quiet Hours

## ONE-LINE SUMMARY
When Legion must NOT send proactive messages — quiet hours, sleep patterns, focus time.

## FACTS
- DND window: 1:00 AM – 7:00 AM JST (hard block in proactive_engine.py DO_NOT_DISTURB_START/END)
- Bashara sleep pattern: often past 1AM JST, wake 7AM JST — frequently up at 1–3AM working
- Zemi (seminar): Thursday 1:00–3:00 PM JST — high-priority blocking time, no distractions
- Deep work hours: Unknown pattern — no tracking of when Bashara enters focus mode
- Weekend pattern: likely sleep in on Saturday/Sunday — morning check-ins may be unwelcome before 9AM
- Late night working: 1–3AM JST is often active coding time — do not treat as DND
- ADB scholarship deadline: September 2026 — if selected, significant life change affecting schedule
- Indonesian business hours: 9AM–6PM WIB (UTC+7) — different from JST by 2 hours
- No formal focus-time protection exists in Legion today — all proactive engines fire regardless of calendar

## LEGION BEHAVIOR RULES
1. HARD DND: No proactive messages 1:00 AM – 7:00 AM JST — block at sender level, not per-engine
2. LATE NIGHT ACTIVE: 1–3AM JST is normal working time — don't send "go to sleep" messages during this window
3. ZEMI BLOCK: Thursday 1:00–3:00 PM JST — no proactive check-ins, no briefings, no alerts during this window
4. WEEKEND LATE: Saturday/Sunday — no proactive messages before 9:00 AM JST
5. FOCUS MODE: If Bashara has been coding for >2 hours straight (session duration), defer non-critical check-ins
6. QUIET_THRESHOLD: If user message received after proactive check-in, wait 4 hours before next check-in
7. Morning briefing: 7:30AM via tools/briefing.py (aligns with 7AM wake time). NOTE: ProactiveScheduler also fires a separate 8AM briefing — duplicate fire risk exists (see proactive-schedule.md). Weekend briefing shifts to 9:00 AM JST.
8. Late night check-in at 1AM only if no messages received since 9PM — check last_user_message_ts

## EXAMPLES
Bashara message: (proactive check-in fires at 2AM JST)
Anti-pattern: "Still there? Let me know if there's anything I should be handling." — Bashara is actively working
Correct: Defer until 7AM briefing OR 30 min after last message if silence >4h during active window

Bashara message: "pusing nih" at 11PM JST
Ideal Legion response: Single sentence reply, no bullet list, no follow-up proactive for 2h minimum

Bashara message: Thursday 1:30PM JST, no message
Correct: No proactive fire — zemi block active

Bashara message: Saturday 7AM JST
Anti-pattern: Morning briefing at 7:30AM — too early for weekend
Correct: Weekend briefing shifts to 9:00 AM JST

## ANTI-PATTERNS
1. Thesis nudge at 9AM Saturday: fires even on weekends when Bashara sleeps in — needs weekday-only guard
2. 2AM curiosity check-in: fires even when Bashara is clearly awake and coding — silence_sec check fires incorrectly
3. No zemi awareness: proactive_engine runs freely during Thursday 1–3PM — needs calendar integration

## DEBATE RECORD
Advocate: 8 | Skeptic: 5 | Judge: WRITE 8
Judge note: Sleep pattern data exists in bashara-schedule.md — this page formalizes the operational rules from it.
