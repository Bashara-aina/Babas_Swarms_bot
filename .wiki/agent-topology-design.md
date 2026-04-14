---
title: Agent Topology Design
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- agent-topology-design.md
created: '2026-04-14'
updated: '2026-04-14'
summary: Optimal multi-agent structure for Legion's workload — single-agent vs swarm.
wikilinks: []
confidence: medium
source: research
---

# Agent Topology Design

## ONE-LINE SUMMARY
Optimal multi-agent structure for Legion's workload — single-agent vs swarm.

## FACTS
- 76+ agents registered in YAML — most are specialized task agents (coder, analyst, researcher, etc.)
- Agent routing: intent_router.py classifies intent → routes to agent_key → agents.py dispatches
- 5 main task types: code/debug, research/analysis, emotional/support, media, system/utility
- Current topology: intent classifier → single specialist agent per turn → response
- Multi-agent needed for: compound tasks ("A dan B") — currently only executes A
- No parallel execution: agent_loop() runs single agent, no swarm pattern
- Swarm patterns: defined in core/swarm_topologies.py but not wired into main routing
- Agent communication: via shared.py state + SQLite transcript store — no message passing

## LEGION BEHAVIOR RULES
1. Simple queries (quick questions, emotional support): single general agent — no multi-agent overhead
2. Compound tasks (A + B): intent_router detects "dan" / "and" → spawn 2 sub-agents → merge responses
3. Research tasks (>5 min): job queue pattern — spawn research agent, post result when done
4. Coding tasks with sub-steps: agent_loop handles sequentially with progress updates — already working
5. Media processing: single agent with tool access — sequential pipeline (extract → transcribe → analyze)
6. Swarm pattern for consensus: "predict" command uses multi-agent voting (swarm_topologies.py) — already exists
7. Don't use swarm for simple tasks: spawning 3+ agents for a "what time is it" query = massive overhead

## CURRENT TOPOLOGY ISSUES
- 76 agents is excessive — many are duplicate or untested
- No agent timeout: a stuck agent can hang indefinitely
- No agent priority: all agents equal, no way to prefer cheaper/faster agents
- No agent memory isolation: agents share memory store — potential cross-contamination
- FallbackChain provides provider fallback but not agent fallback

## OPTIMAL TOPOLOGY (proposed)
Layer 1: Intent Router (fast, deterministic) — 23 intents + LLM classifier for ambiguity
Layer 2: Specialist Dispatch — routes to 5 main task type agents
Layer 3: Tool Executor — async tools called by specialist agents
Layer 4: Response Formatter — formats output via shared.py send_chunked()

Single-agent for: quick questions, emotional support, simple tool calls
Multi-agent for: compound tasks, research digests, consensus predictions, parallel evaluations

## ANTI-PATTERNS
1. Agent proliferation: adding new agents without retiring old ones → 76+ agents, most untested
2. Swarm without need: running 5 agents to answer "what is 2+2" — single agent 100x faster
3. No agent retirement: dead/duplicate agents remain in registry → confusion about what works

## DEBATE RECORD
Advocate: 7 | Skeptic: 7 | Judge: WRITE 7
Judge note: Agent topology is architecture-critical for scaling — this page provides a design blueprint.
