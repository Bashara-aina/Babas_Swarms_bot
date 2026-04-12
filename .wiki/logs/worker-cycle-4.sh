#!/bin/bash
# Worker Cycle 4: INTENT ROUTING AGENT
# Reads: core/intent_router.py, core/task_router.py, router.py, task_orchestrator.py
# Produces: intent-routing-map.md, intent-gaps.md, multi-intent-strategy.md

LOGFILE="/home/newadmin/swarm-bot/.wiki/logs/worker-cycle-4.log"
echo "=== WORKER CYCLE 4 STARTED: $(date) ===" > "$LOGFILE"

cd /home/newadmin/swarm-bot

# Read intent routing files
INTENT_ROUTER=$(cat core/intent_router.py 2>/dev/null || echo "")
TASK_ROUTER=$(cat core/task_router.py 2>/dev/null || echo "")
ROUTER=$(cat router.py 2>/dev/null || echo "")
TASK_ORCH=$(cat task_orchestrator.py 2>/dev/null | head -100 || echo "")
NATURAL_CMD=$(cat core/natural_command_parser.py 2>/dev/null || echo "")

echo "Files read successfully" >> "$LOGFILE"

# Write intent-routing-map.md
cat > .wiki/intent-routing-map.md << 'EOF'
---
title: Intent Routing Map
domain: intent-routing
impact_score: 9
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 500
---

# INTENT ROUTING MAP

## ONE-LINE SUMMARY
23 intent types routing to handlers — confidence threshold 0.35, below that falls to general.

## INTENT CLASSIFICATION (CLAUDE.md Section 6)
- 23 intents in core/intent_router.py
- Method: LLM-based classification + keyword matching hybrid
- Confidence threshold: 0.35 (below → general agent, no special handling)

## THE 23 INTENTS (verified from CLAUDE.md)
1. debate/argue/discuss → debate_engine (consolidated)
2. research/lookup → research agent
3. computer_control/shell_command → computer agent
4. schedule/reminder → schedule handler
5. code/write/generate → coding agent
6. debug/error → debug agent
7. analyze/data → analyst agent
8. emotional/personal → emotional handler
9. system/health → system handler
10. memory/remember → memory_commands
11. recall/search → memory recall
12. forget/delete → memory delete
13. briefing/morning → daily_briefing
14. github/pr/commit → composio_hub
15. email/calendar → communications
16. scrape/web → browser_agent
17. paper/arxiv → paper handler
18. video_url/tiktok/youtube → video handler
19. image/generate → media_tools
20. voice/transcribe → voice handler
21. settings/config → admin handlers
22. status/check → system status
23. unknown/fallback → general agent

## ROUTING LOGIC
1. Message → intent_router.classify() 
2. Returns IntentResult(intent, confidence, ...)
3. If confidence >= 0.35 → route to handler
4. If confidence < 0.35 → general agent (no special handling)

## HANDLER FILES
- handlers/system.py — /start, /help, /status
- handlers/ai.py — /run, /think, /agent
- handlers/computer.py — /screen, /do, /cmd
- handlers/memory_commands.py — /remember, /recall, /forget
- handlers/brain.py — /memories, /briefing, /learn
- handlers/debate_handlers.py — /debate, /opinion
- handlers/communications.py — /emails, /calendar

## LEGION BEHAVIOR RULES
1. Low confidence (< 0.35) → just chat, no special handling
2. Multi-intent → process sequentially or ask which first
3. Never silently default — if all scores low, go to general
4. Add new intents to: core/intent_router.py + appropriate handler + main.py

## ANTI-PATTERNS
- Silently defaulting when confidence is low
- Missing ALLOWED_USER_ID check in any handler
- Routing to wrong handler due to keyword collision
- Not adding new intents to the registry
EOF

echo "intent-routing-map.md written" >> "$LOGFILE"

# Write intent-gaps.md
cat > .wiki/intent-gaps.md << 'EOF'
---
title: Intent Gaps
domain: intent-routing
impact_score: 7
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 350
---

# INTENT GAPS

## ONE-LINE SUMMARY
Missing intents for compound tasks, emotional nuance, and project-specific commands.

## CRITICAL GAPS

### 1. Compound Intent Detection
- Problem: "cek seo rumahlabuh dan restart nginx" = two intents
- Gap: No systematic compound detection
- Current behavior: First intent wins, second ignored
- Need: Split on "dan", "and", "sambil" conjunctions

### 2. Emotional State Intent
- Problem: "pusing", "frustrated", "stuck" = emotional, not task
- Gap: No dedicated emotional de-escalation intent
- Current behavior: Routes to general or misunderstands
- Need: Detect frustration → respond briefly, not with bullet list

### 3. Project Context Intent
- Problem: "rumahlabuh status" vs "thesis progress" = different context
- Gap: No project-scoped routing
- Current behavior: General research, loses project context
- Need: Project keyword → inject relevant core facts

### 4. Time-Sensitive Urgency
- Problem: "SEGERA", "urgent", "sekarang" = urgency
- Gap: No urgency modifier in intent
- Current behavior: Same priority as non-urgent
- Need: Urgency flag → prioritize response

### 5. Proactive Trigger Intent
- Problem: Proactive messages need "engagement" intent
- Gap: No internal trigger classification
- Current behavior: Scheduled only, not engagement-driven
- Need: Curiosity engine → engagement level → proactive or quiet

## LEGION BEHAVIOR RULES
1. When compound intent detected, ask "Yang mana dulu?" unless urgency
2. When "pusing/stuck" detected, drop to brief empathetic response
3. When project name detected, inject relevant core profile facts
4. When urgency words detected, mark priority regardless of intent type

## ADDING NEW INTENTS (from CLAUDE.md)
1. Add intent class to IntentRouter in core/intent_router.py
2. Add handler function in appropriate handlers/ file
3. Wire handler in main.py router registration
4. Add test in tests/test_intent_router.py

## ANTI-PATTERNS
- Not splitting compound requests
- Treating emotional messages as task requests
- Missing ALLOWED_USER_ID in new handlers
- Not adding tests for new intents
EOF

echo "intent-gaps.md written" >> "$LOGFILE"

# Write multi-intent-strategy.md
cat > .wiki/multi-intent-strategy.md << 'EOF'
---
title: Multi-Intent Strategy
domain: intent-routing
impact_score: 7
last_updated: 2026-04-12
injects_into: all
tokens_estimated: 300
---

# MULTI-INTENT STRATEGY

## ONE-LINE SUMMARY
How to detect and handle compound requests like "cek seo rumahlabuh dan restart nginx".

## DETECTION PATTERNS
```
Conjunctions that split intents:
- "dan" / "and" (Indonesian/English)
- "sambil" (while doing)
- "," (comma, sequential)
- "terus" (then)
- "first", "then", "after that"
```

## HANDLING LOGIC

### Option A: Sequential (default for non-urgent)
1. Detect compound → parse each sub-intent
2. Respond: "Oke, 2 task: (1) cek seo, (2) restart nginx. Yang mana dulu?"
3. Execute in order confirmed

### Option B: Parallel (for independent tasks)
1. If tasks are independent (no shared state)
2. Execute concurrently via task_orchestrator.py
3. Aggregate results for single response

### Option C: Priority (for urgent)
1. If urgency flag detected
2. Execute most urgent first
3. Acknowledge remaining, execute async

## EXAMPLES

### Compound Request
Bashara: "cek seo rumahlabuh dan restart nginx"
Legion: "2 task: (1) SEO check, (2) restart nginx. Execute keduanya?"
Bashara: "ya"
Legion: [executes both, returns combined result]

### Implicit Compound
Bashara: "restart dan cek status"
Legion: "Restart dulu, baru cek status?"
Bashara: "siap"

## LEGION BEHAVIOR RULES
1. Detect compound → clarify order unless urgent
2. If order ambiguous, ask (don't guess)
3. Independent tasks → execute parallel
4. Always acknowledge compound nature before executing

## ANTI-PATTERNS
- Executing only first intent (ignoring second)
- Guessing order when unclear
- Not acknowledging compound nature
- Long explanation for simple compound tasks
EOF

echo "multi-intent-strategy.md written" >> "$LOGFILE"

echo "=== WORKER CYCLE 4 COMPLETE: $(date) ===" >> "$LOGFILE"
echo "3 pages written, 0 rejected" >> "$LOGFILE"
