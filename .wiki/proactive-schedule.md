---
title: Proactive Schedule
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- proactive-schedule.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Every scheduled job, trigger, and frequency — Legion initiates without being
  asked.
wikilinks: []
confidence: medium
source: research
---

# Proactive Schedule

## ONE-LINE SUMMARY
Every scheduled job, trigger, and frequency — Legion initiates without being asked.

## FACTS
- ProactiveScheduler (core/proactive/scheduler.py) runs on 30-min interval via asyncio loop
- DAILY MORNING BRIEF fires at 8:00 AM JST — one per day, skips other checks when firing
- LATE NIGHT CHECK fires at 1:00 AM JST — shows unfinished tasks + Soul Engine emotional tone
- RUMAHLABUH.COM MONITOR fires every 30 min during 8AM–11PM JST — pings rumahlabuh.com
- GITHUB TREND WATCHER fires Monday 9:00 AM JST — runs SelfUpgradeEngine.scan_github_trending
- WIKI LINT fires Sunday 10:00 AM JST — lint_wiki() health check
- AGENTS.MD SYNC fires Saturday 10:30 AM JST — sync_agents_md()
- WEEKLY GITHUB INTEL DIGEST fires on configurable weekday (default Sunday) — opt-in via LEGION_WEEKLY_GITHUB_INTEL=1
- CuriosityEngine (core/proactive/curiosity_engine.py) runs on 60-min interval (CURIOSITY_INTERVAL_MIN)
- CuriosityEngine max 3 proactive messages per day (MAX_PROACTIVE_PER_DAY)
- CuriosityEngine quiet period: 30 min silence before interrupting (CURIOSITY_QUIET_MIN)
- CuriosityEngine sleeps if no user message for >8h during 9AM–11PM JST
- ProactiveInitiator (core/proactive/proactive_initiator.py) runs on system snapshot triggers
- ProactiveInitiator has 30-min minimum interval between messages (PROACTIVE_MIN_INTERVAL_SEC)
- ProactiveInitiator triggers: GPU temp, RAM, disk, training complete, email, business spike
- proactive_engine.py (core/) runs independent 60s loop: late_night, site_health, system_health, github_releases, thesis_deadline
- Proactive engine DND: 1–7 AM JST (DO_NOT_DISTURB_START/END)
- All proactive failures are silent — wrapped in try/except, never crashes bot

## LEGION BEHAVIOR RULES
1. Daily briefing fires once per day at 8AM JST — never repeat in same day
2. Proactive messages capped at 3/day across all curiosity engine triggers
3. Sleep check-in requires 4-hour cooldown between sends
4. 30-min silence required before curiosity engine interrupts
5. No proactive messages between 1AM–7AM JST (DND window)
6. All proactive checks fail silently — never crash the bot
7. GitHub notifications checked every 6 hours
8. Rumahlabuh.com pinged every 30 min during active hours
9. Brain check-ins from beliefs.json pending follow-ups checked every curiosity tick
10. ProactiveInitiator alerts fire in priority order — first trigger wins

## EXAMPLES
Bashara message: (no message for 10 hours)
Ideal Legion response: "Lo baik-baik aja? Still there? Let me know if there's anything I should be handling." (from CHECKIN_POOL, random selection)

Bashara message: (8AM JST, first interaction of the day)
Ideal Legion response: "☀️ Good morning, Bashara! It's Sunday, April 12.\n🏠 Website: up ✅\n📋 Unfinished: ...\n📍 You're in Tokyo. I'm ready for today's tasks."

Bashara message: (1AM JST check-in)
Ideal Legion response: "🌙 Late night check-in — take it easy tonight\nAll clear ✅ — get some rest, Bashara."

## ANTI-PATTERNS
1. Check-in spam: without U4 cooldown, same message fires multiple times in 2 hours — FIXED by 4h cooldown + CHECKIN_POOL variety
2. DND violation: proactive engine sends thesis nudge at 9AM on Saturday when Bashara is sleeping in — FIXED by time-of-day guards
3. Silent failure on all proactive checks makes debugging impossible — no monitoring hook exists

## DEBATE RECORD
Advocate: 9 | Skeptic: 6 | Judge: WRITE 9
Judge note: Proactive intelligence is core to Legion's "initiates without being asked" value prop — this page is the definitive reference.
