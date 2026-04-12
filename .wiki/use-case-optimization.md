---
title: use-case-optimization
domain: future-architecture
impact_score: 8
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 340
---

# Use Case Optimization

## ONE-LINE SUMMARY
100x performance definition for each of Bashara's 5 main use cases.

## FACTS
- Bashara's 5 main use cases: coding (Legion self-development), thesis (POPW research), Indonesian businesses (rumahlabuh + cekwajar), personal productivity (scheduling, reminders), emotional support (late night pusing)
- Current baseline: generic LLM + basic memory + reactive-only = ~1x for all use cases
- Potential 100x defined per use case with targeted optimization

## LEGION BEHAVIOR RULES

### USE CASE 1: Coding / Legion Self-Development
100x looks like:
- "build me a webhook listener for GitHub" → working code in <2 minutes, deployed, tested
- "add MCP server X to Legion" → skill auto-generated from server spec, wired in <5 minutes
- "fix the compound intent bug" → identifies root cause in code, proposes fix, offers to implement
- Current gap: no job queue for multi-file changes, no automated code review on PR
- Priority action: job queue + autonomous code execution skill

### USE CASE 2: Thesis / POPW Research
100x looks like:
- "find papers on FPN for assembly action recognition" → 10 relevant papers with 1-line summary each, ranked by citation count, in <30 seconds
- "extract loss values from last 3 training runs and plot the curve" → actual chart in Telegram
- "summarize what you know about my thesis topic from our conversations" → coherent 500-word summary
- Current gap: no arXiv integration, no training log parser, no chapter progress tracker
- Priority action: arXiv search skill + POPW training dashboard + thesis chapter tracker

### USE CASE 3: Indonesian Businesses (rumahlabuh + cekwajar)
100x looks like:
- "any new inquiries on rumahlabuh since yesterday?" → Supabase query + summary in <10 seconds
- "should I raise prices on cekwajar given FX headwinds?" → IDR/USD analysis + competitive data + recommendation
- "CEKWAJAR-123: customer hasn't paid in 48h" → escalation workflow: email draft + Supabase update + Telegram notification to Bashara
- Current gap: no booking escalation, no FX tracking, no pricing intelligence
- Priority action: Supabase client upgrade + FX alert + booking escalation tool

### USE CASE 4: Personal Productivity
100x looks like:
- "remind me in 30 min to check email" → actual Telegram ping at 30 min mark
- "what's on my calendar tomorrow?" → Google Calendar query (if MCP wired) or memory recall
- "summarize what I worked on this week" → from session transcripts: projects touched, files modified, decisions made
- Current gap: no timer tool, no calendar integration, no weekly summary
- Priority action: timer skill + Google Calendar MCP + weekly digest

### USE CASE 5: Emotional Support
100x looks like:
- "pusing" at 1AM → one warm sentence, no bullets, no advice, just acknowledgment
- "skripsi gatau mau ngapain" → Socratic questions to help clarify: "chapter 3 kan mau bikin apa?"
- "mantap" → brief celebration, context-aware response matching the兴奋
- Current gap: emotion_modulator works but no Indonesian-specific empathy patterns
- Priority action: Indonesian emotional vocabulary expansion in soul_engine + emotion_engine

## EXAMPLES
Bashara message: "pusing skripsi"
Current: "I understand this is frustrating. Let's break it down..." (generic AI response)
100x: "Chapter 3 ya? Lo udah sampai Fig 3.1没? Atau masih stuck di methodology?" (context-aware, Socratic, Indonesian)

Bashara message: "cek rumahlabuh ada inquiry baru ga"
Current: Runs query, returns raw Supabase rows
100x: "1 new inquiry from Bandung — Rp 2.5M budget, moving in June. Reply draft ready. Want me to send?" (query + summary + action)

## ANTI-PATTERNS
1. Same model for all use cases: using general-purpose model for emotional support = slow + expensive + generic
2. No context injection for business queries: thesis context injected but rumahlabuh context not = missed personalization
3. No task-type routing: "pusing" routed to general agent when it should route to emotional support agent

## DEBATE RECORD
Advocate: 8 | Skeptic: 6 | Judge: WRITE 8
Judge note: Use-case-specific optimization is how Legion becomes 10x engineer, not just smart assistant.
