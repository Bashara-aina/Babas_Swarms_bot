---
title: orchestrator-comparison
type: architecture
status: active
tags: [orchestration, agents, comparison, swarm, nexus, jarvis]
created: 2026-04-13
updated: 2026-04-13
summary: Legion has 4 competing orchestrators: task_orchestrator (492 lines, task chaining + debate), legion_swarm (322 lines, 11-agent 3-phase), nexus_orchestrator (3-layer routing), and jarvis_orchestrator (context bundling). Consolidation into a single orchestrator is planned per the 2026-04-12 audit.
wikilinks:
  - [[multi-agent-orchestration]]
  - [[intent-routing]]
  - [[legion-module-map]]
confidence: medium
source: implementation
---

# Orchestrator Comparison

## TL;DR
Legion operates four concurrent orchestration systems at different complexity levels: intent routing for simple commands (<100ms), three-agent pipeline for coding tasks (30-120s), full 87-agent swarm for complex research (60-120s), and Nexus semantic routing for intelligent task distribution. Per the 2026-04-12 audit, consolidation into a single unified orchestrator is planned.

## Orchestrator Inventory

| Orchestrator | File | Lines | Purpose | Agents |
|--------------|------|-------|---------|--------|
| Task Orchestrator | task_orchestrator.py | 492 | Task chaining + debate | 6 debate personas |
| Legion Swarm | core/legion_swarm.py | 322 | 3-phase execution | 11 hardcoded |
| Nexus | core/nexus_orchestrator.py | — | 3-layer routing | Registry-based |
| Jarvis | core/jarvis_orchestrator.py | — | Context bundling | Multi-source |

## Pattern 1: Intent Routing (Fastest)

**Latency**: <100ms  
**Agents**: 1 (router)  
**Use Case**: Simple commands, greetings, single-intent queries

```
User Message → [Intent Router] → [Handler] → Response
```

### Flow
1. Message arrives at `core/intent_router.py`
2. Keyword matching + LLM fallback classifies intent
3. Handler selected from 45+ handlers
4. Single LLM call or direct execution
5. Response sent

### When Used
- `/start`, `/help`, `/status`
- "Hello", "Hi"
- Simple factual questions
- Single-skill invocations

## Pattern 2: Three-Agent Pipeline

**Latency**: 30-120s  
**Agents**: 3 (Planner, Worker, Reviewer)  
**Use Case**: Code tasks, analysis, multi-step problems

```
Task → [Planner Agent] → [Worker Agent] → [Reviewer Agent] → Response
```

### Flow
1. **Planner**: Decomposes task into subtasks
2. **Worker**: Executes subtasks (via OpenCode or direct)
3. **Reviewer**: Validates output quality
4. **Synthesis**: Final response assembly

### Implementation
From `wiki/raw/docs/legion-master.md`:
```python
# Three-agent pipeline components
- Planner: Task decomposition, approach strategy
- Worker: Code execution, research execution
- Reviewer: Quality gate, validation
```

## Pattern 3: Full Swarm Debate

**Latency**: 60-120s  
**Agents**: ~87 (72 specialists + 9 leads + 6 debate personas)  
**LLM Calls**: ~96 (4 rounds × 24 parallel)  
**Use Case**: Complex research, strategic decisions, multi-perspective analysis

```
/swarm <topic>
    ├─ Phase 1: Department Sprint (parallel)
    │   ├─ ⚙️ Engineering (8 agents) → Lead Engineer
    │   ├─ 🔬 Research (8 agents) → Research Director
    │   ├─ 📦 Product (8 agents) → Head of Product
    │   ├─ 📣 Marketing (8 agents) → CMO
    │   ├─ 🎨 Design (8 agents) → Design Lead
    │   ├─ 🏭 Operations (8 agents) → COO
    │   ├─ ✨ Creative (8 agents) → Creative Director
    │   ├─ ⚖️ Legal (8 agents) → General Counsel
    │   └─ 🧭 Strategy (8 agents) → CSO
    │
    ├─ Phase 2: 4-Round Debate
    │   ├─ Round 1: 6 personas in parallel
    │   ├─ Round 2: Cross-examination
    │   ├─ Round 3: Judge synthesis
    │   └─ Round 4: Rating
    │
    └─ Phase 3: Format → Telegram
```

### Quick Variant: `/swarm_quick`
- Skips departments
- 6 debate personas only
- 15-30s latency
- 24 LLM calls total

## Pattern 4: Nexus Semantic Routing

**Latency**: Variable  
**Layers**: 3 (keyword → semantic embeddings → LLM fallback)  
**Use Case**: Intelligent task distribution to appropriate agents

### Routing Layers
1. **Keyword Matching**: Fast path for known commands
2. **Semantic Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
3. **LLM Fallback**: General classification for unknown inputs

## The 4 Competing Orchestrators

Per the 2026-04-12 deep audit, these 4 orchestrators create confusion:

### 1. task_orchestrator.py (492 lines)
- Primary: Task decomposition
- SwarmDebateOrchestrator with 6 personas, 4-round debate
- Command: `/swarm`, `/orchestrate`

### 2. core/legion_swarm.py (322 lines)
- Hardcodes 11-agent LEGION_TEAM
- 3-phase: propose → debate → synthesize
- **Problem**: Ignores 76-agent registry entirely

### 3. core/nexus_orchestrator.py
- 3-layer routing: keyword → semantic → LLM
- sentence-transformers for embedding similarity
- Selects agents from registry

### 4. core/jarvis_orchestrator.py
- Context bundling
- Integrates: Memory + Screenpipe + WhatsApp + Calendar
- For: Personal assistant tasks

## Consolidation Plan

Per audit Priority 7, these will be unified:

```python
class LegionOrchestrator:
    def __init__(self):
        self.agent_registry = AgentRegistry()
        self.nexus_router = NexusRouter()
    
    async def run(self, task: str, user_id: int) -> str:
        # Phase 1: Route and select team from REAL registry
        team = await self.agent_registry.select_team(task, max_agents=5)
        
        if len(team) == 1:
            return await self._run_single(team[0], task, user_id)
        else:
            return await self._run_debate(team, task, user_id)
```

## When to Use Each

| Task Type | Example | Orchestrator | Latency |
|-----------|---------|--------------|---------|
| Simple command | "/help" | Intent Router | <100ms |
| Quick question | "What's the weather?" | Intent Router | <500ms |
| Code task | "/opencode fix the bug" | Three-Agent | 30-120s |
| Deep research | "/research AI in healthcare" | Full Swarm | 60-120s |
| Quick debate | "/swarm_quick Python vs JS" | Debate only | 15-30s |
| Personal query | "Remind me to call mom" | Jarvis | Variable |

## Related Pages

- [[multi-agent-orchestration]] — Agent coordination
- [[intent-routing]] — Simple routing
- [[legion-module-map]] — Module overview
