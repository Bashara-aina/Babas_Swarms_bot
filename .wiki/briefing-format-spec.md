---
title: briefing-format-spec
domain: proactive-intelligence
impact_score: 7
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 320
---

# Briefing Format Spec

## ONE-LINE SUMMARY
Optimal morning briefing structure for Bashara — concise, actionable, no noise.

## FACTS
- Briefing fires at 7:30 AM JST daily via tools/briefing.py schedule_daily_briefing
- Also fires at 8:00 AM JST via ProactiveScheduler._build_daily_briefing (duplicate risk)
- Current format includes: day string, website ping, unfinished tasks (max 4), schedule (max 3), GitHub alerts, business health, location
- Current format is ~400-600 tokens — likely exceeds optimal for Telegram display
- No weather data in current briefing despite location being shown
- No thesis progress in briefing despite thesis_deadline() existing
- No calendar integration — tomorrow's meetings not included
- No budget status in briefing
- No "yesterday's accomplishments" recap — only unfinished tasks shown
- Briefings are HTML formatted with <b> tags and emoji prefixes

## LEGION BEHAVIOR RULES
1. Maximum briefing length: 500 tokens — anything longer gets cut to "top 3" items per category
2. BRIEFING SECTIONS (in order): Date + greeting → Weather + location → Thesis status → Unfinished tasks (max 3) → Today's schedule (max 2) → Business metrics (1 line) → Actionable prompt at end
3. Weather: 1 line — temp + condition + rain flag if relevant. No 5-day forecast.
4. Thesis: 1 line only if <60 days remaining. "🚨 CRITICAL" / "⚠️ 45 days" format.
5. Tasks: bullet list, max 3 items. Format: "• [task name] — [1 line context]"
6. Schedule: max 2 items. Show time + event name only.
7. Business: 1 line. "rumahlabuh.com: N new bookings" or "all quiet ✅"
8. End with: "I'm ready for today. What's the priority?" — single line prompt
9. No GitHub noise unless actual alerts — don't mention "no unread" if nothing to show
10. Skip all sections with no data — don't show "GitHub: (no data)" empty sections

## EXAMPLES
Bashara message: (8AM JST morning)
Current Legion response (too long): "☀️ Good morning, Bashara! It's Sunday, April 12.\n🏠 Website: up ✅\n📋 Unfinished:\n  • Thesis chapter 3 draft\n  • CEKWajar deployment\n  • Homebrew formula\n📅 This week:\n  • Zemi Thursday 1-3PM\n  • ADB deadline September\n🐙 GitHub: 1 unread notification\n🏠 rumahlabuh.com: 2 recent bookings — all good ✅\n📍 You're in Tokyo. I'm ready for today's tasks."

Ideal Legion response (concise): "☀️ Sunday April 12 — Tokyo 18°C, clear\n📝 Thesis: 82 days left (chapter 3 draft)\n📋 Tasks: 3 pending — thesis draft, CEKWajar deploy, Homebrew formula\n📅 Today: zemi Thu 1-3PM\n🏠 rumahlabuh: quiet\nI'm ready. What's the priority?"

Bashara message: (after heavy night, 8AM JST)
Correct: "☀️ Morning — you were up late. 18°C, clear skies. Thesis: 82 days. I've got tasks queued whenever you're ready."

## ANTI-PATTERNS
1. Verbose briefings: every data point shown even when empty — suppress zero-data sections
2. Duplicate briefings: both tools/briefing.py and ProactiveScheduler fire at different times — deduplicate needed
3. No weather: location shown but weather missing — inconsistent information density
4. GitHub noise: always mentions GitHub even when no unread — generates noise without value

## DEBATE RECORD
Advocate: 7 | Skeptic: 7 | Judge: WRITE 7
Judge note: Briefing is highest-frequency proactive output — even small optimization has compounding value.
