---
title: Proactive Gaps
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- proactive-gaps.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Missing proactive behaviors that should exist but don't.
wikilinks: []
confidence: medium
source: research
---

# Proactive Gaps

## ONE-LINE SUMMARY
Missing proactive behaviors that should exist but don't.

## FACTS
- No Supabase row-level-security anomaly detection — ProactiveScheduler._check_business_health() only counts recent bookings, no error detection
- No thesis progress nudge between 9–10AM Mon-Fri — proactive_engine.check_thesis_deadline() runs once per day at 9AM but has 24h cooldown
- No GitHub PR review requests checked proactively — only unread notifications tracked
- No cekwajar.id health monitor — only rumahlabuh.com is monitored
- No weather-based proactive check — no trigger for "rain tomorrow bring umbrella" or temperature extremes
- No calendar-based proactive — no integration with Google Calendar or n8n for meeting reminders
- No POPW training log parser — ProactiveInitiator._check_training_complete() only checks for completion signals in raw log
- No email attachment alert — ProactiveInitiator._check_new_important_email() only checks inbox count, not attachment-specific triggers
- CuriosityEngine follow-up check relies on beliefs.json manual population — no automatic surfacing of unresolved user requests
- No SCREENPIPE integration for proactive screen context — ScreenpipeBridge exists but only runs on demand
- No "you've been coding for 4 hours straight" physical break reminder — no context for session duration
- ProactiveEngine._check_github_releases() uses REST API polling — no webhook-based instant notification
- No "you're about to run out of budget" warning — proactive budget alerts missing
- No external trigger for currency exchange rate spikes (IDR/USD) affecting Indonesian business
- No "new paper on arXiv matches your thesis topic" alert

## LEGION BEHAVIOR RULES
1. Add cekwajar.id to site health monitor when deployed — same pattern as rumahlabuh.com
2. Add weather trigger: if tomorrow's forecast shows rain and Bashara has outdoor task, send heads-up by 9PM JST tonight
3. Add thesis progress nudge: if no commit in 48h and deadline <60 days, increase frequency to daily
4. Add training log tail parser for POPW — extract loss/accuracy trends from train.log and alert if degradation detected
5. Add calendar integration: morning briefing should include tomorrow's meetings if any exist
6. Add budget warning: if daily budget >80% used by noon, flag in briefing
7. All new proactive triggers must be gated by do-not-disturb (1–7AM JST)

## EXAMPLES
Bashara message: (no message, 9PM JST, tomorrow forecast shows rain)
Ideal Legion response: "Tomorrow's forecast: rain all day in Tokyo. If you're heading to campus, bring an umbrella. Outdoor tasks for rumahlabuh might need rescheduling."

Bashara message: (48h no commit, thesis 45 days left)
Ideal Legion response: "⚠️ Thesis deadline: 45 days left (July 2026). No commits in 48h. What's the blocker today?"

Bashara message: (training running, loss just spiked 3x)
Ideal Legion response: "Training anomaly detected — loss spiked to 2.4 (was 0.8). Want me to check the learning rate or stop the run?"

## ANTI-PATTERNS
1. Checkin fatigue: too many low-value check-ins → Bashara mutes Legion — keep proactive sparse and high-value
2. DND violations: weather/calendar alerts firing at 3AM JST — must check JST hour before sending
3. Noisy business alerts: 1 new booking triggers alert every 30 min → threshold too low

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Judge note: Practical gap list grounded in actual Bashara workflows — high practical value.
