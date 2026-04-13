---
title: self-improvement-loop
type: concept
status: active
tags: [improvement, learning, feedback, iteration, calibration]
created: 2026-04-13
updated: 2026-04-13
summary: The self-improvement loop enables Legion to learn from every interaction — recording what worked, what failed, and what the user corrected — and applying those learnings to future reasoning and responses.
wikilinks:
  - [[memory-architecture]]
  - [[./concepts/reasoning-loop]]
  - [[./concepts/multi-agent-orchestration]]
  - [[./concepts/skill-registry]]
confidence: medium
source: design
---

# Self-Improvement Loop

## TL;DR
Legion continuously learns from each interaction by observing outcomes (did the approach work? did the user correct the response?), recording salient facts to memory with appropriate importance weights, and retrieving relevant past learnings when reasoning through new requests. The loop closes when a learned pattern influences a future response — without explicit user prompting.

## Overview

A system that only learns when explicitly told to "remember this" is limited. Legion's self-improvement loop is implicit and continuous: it observes every interaction, extracts signals about what worked and what didn't, and stores those signals in a way that influences future behavior without requiring recall. The user doesn't say "remember that worked" — the loop handles it automatically.

## Context

Legion operates on a 64GB RAM machine with an RTX 3060. The memory architecture provides the storage substrate. But storage alone doesn't create learning — there must be a mechanism that observes events, writes appropriate records, and retrieves those records at relevant decision points. That's the self-improvement loop.

## Key Properties

- **Implicit learning**: No explicit "learn from this" command required — every interaction is evaluated
- **Importance-weighted storage**: Corrections and failures get 0.9 importance; casual observations get 0.5–0.7
- **Outcome observation**: Success/failure signals come from task completion, user correction, tool return codes
- **Feedback integration**: `/opinion` and `/debate` command outcomes feed into belief calibration
- **Memory tiering**: High-importance learnings are promoted to CoreMemory; others remain in ArchivalMemory
- **Curiosity engine integration**: `curiosity_engine.py` checks for learning opportunities on each tick
- **4h sleep check-in cooldown**: Prevents over-triggering during active sessions
- **Pattern recognition**: Repeated failure patterns are flagged for review

## How It Works

### Observe Phase
Every LLM response and tool execution result is observed. Key signals:
- Did the user correct the response? (indicator: "no, that's wrong", "actually...")
- Did the task complete successfully? (indicator: tool return code, explicit acknowledgment)
- Did the user express frustration or confusion? (indicator: "pusing", "gak jelas")
- Was a repeated approach already attempted? (indicator: memory recall of past failed attempts)

### Record Phase
Observations are written to memory via `MemoryManager.save()`:
- User corrections → importance 0.9, tagged "user-correction"
- Failed tool calls → importance 0.85, tagged "failed-approach"
- Successful resolutions → importance 0.75, tagged "successful-approach"
- Preference signals → importance 0.8, tagged "user-preference"
- Auto-extract triggers → handled by `auto_extract_and_save()` in `memory_manager.py`

The `_CuriosityState` in `curiosity_engine.py` tracks daily send count and last fire time to prevent the loop from interrupting active sessions.

### Recall Phase
Before reasoning through a new request, `MemoryManager.search()` is called with the request topic. Relevant past learnings are retrieved and injected into the context. The reasoning loop checks for previously failed approaches and avoids repeating them.

### Apply Phase
Learned patterns influence behavior:
- If a skill handler failed previously and the same skill is triggered again, the fallback path is taken immediately rather than retrying the failed approach
- If a particular reasoning approach succeeded for a similar problem, that approach is prioritized
- User preferences extracted via auto-extraction are included in the system prompt via UserProfile

## Relationships

The self-improvement loop depends entirely on [[memory-architecture]] for its storage substrate — without ArchivalMemory, CoreMemory, and RecallMemory, there would be nowhere to record observations. The loop feeds into [[./concepts/reasoning-loop]] by providing learned context: when the reasoning loop retrieves past learnings, it can avoid previously failed approaches and build on previously successful ones. [[./concepts/multi-agent-orchestration]] benefits from the loop: if the swarm produces a poor synthesis or a debate persona takes a consistently suboptimal stance, those outcomes are recorded and inform future swarm calls. [[./concepts/skill-registry]] skill selection is calibrated by past performance: if `web_search` consistently returns poor results for a certain query type, that pattern is recorded and the fallback is preferred next time.

## Current Status

**Partially implemented.** Auto-extraction pipeline is fully functional. Curiosity engine is running with CHECKIN_POOL. Memory importance-weighted storage is implemented. Skill performance tracking is not yet wired. Outcome observation for task success/failure is tracked in handlers but not yet systematically fed back into memory. Explicit feedback from `/opinion` and `/debate` is wired. This is ongoing Phase 2 work.

## See Also

- [[memory-architecture]] — Storage substrate for learnings
- [[./concepts/reasoning-loop]] — Reasoning that retrieves past learnings
- [[./concepts/multi-agent-orchestration]] — Swarm learning from debates
- [[./concepts/skill-registry]] — Skill performance calibration
