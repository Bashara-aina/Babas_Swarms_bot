# Design: OpenCode ⇄ Claude Code ⇄ LegionBot — Deep Integration
Date: 2026-04-16
Type: Architecture Design
Status: Draft

---

## 1. Concept & Vision

Three autonomous coding agents — **OpenCode** (CLI-coded pipeline), **Claude Code** (senior engineering review), and **LegionBot** (Telegram-connected AI coworker) — operate as a single coherent intelligence. They share memory, recursively spawn each other as sub-agents, and delegate based on capability match + availability. No system is a dead-end: any of the three can escalate to either of the others.

The integration is **principle-based**: shared wiki as the joint brain, unified memory facade as the write layer, cross-agent bridges as the transport, and shared skills/agents as the execution units.

---

## 2. Architecture — Four Integration Layers

### Layer 1 — Shared Memory (Joint Brain)

```
                    ┌─────────────────────────┐
                    │   .wiki/ (joint brain)   │
                    │  sessions/  decisions/   │
                    │  entities/  concepts/    │
                    └────────┬────────────────┘
                             │ read/write
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
 ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
 │  OpenCode   │      │ Claude Code │      │ LegionBot   │
 │ builtin_hooks│      │   CLAUDE.md │      │memory_manager│
 │session_hooks│      │   skills/   │      │ soul_engine │
 └─────────────┘      └─────────────┘      └─────────────┘
```

**All three systems** read from and write to the same `.wiki/` vault:
- OpenCode → `builtin_hooks.py` → writes session summaries + ADRs to `.wiki/opencode/sessions/` + `.wiki/decisions/`
- Claude Code → skills read/write via `.claude/skills/` + wiki hooks
- LegionBot → `wiki_bridge.py` → reads OpenCode sessions for context (`_opencode_brain_layer`)

**Key change**: LegionBot's `_opencode_brain_layer()` (in `unified_prompt_context.py`) already queries the wiki. We extend it to also query Claude Code session logs stored in `.wiki/claude-code/sessions/`.

**Shared memory facade** (new: `core/joint_memory.py`):
- Single async API: `joint_save(content, source, tags)`, `joint_search(query)`
- Writes to the correct subdirectory based on `source` field
- All three systems call this facade — no direct store access

### Layer 2 — Bidirectional Bridges (Recursive Spawning)

**A. OpenCode → LegionBot** (`core/opencode_bridge.py` upgrade)
```
OpenCode task complete
  → extract_report() detects LEGION TASK COMPLETE
  → checks for callback directives: @legion, /telegram, /notify
  → If directives found: call back to LegionBot via Telegram
    or via internal async event (no Telegram round-trip)
```

**B. OpenCode → Claude Code** (`core/claude_code_bridge.py`, new)
```
OpenCode task complete
  → extract_report() checks for @claude directives
  → If found: spawn Claude Code subprocess with task context
  → Claude Code writes its own session log to .wiki/claude-code/sessions/
  → OpenCode reads that log for next-step context
```

**C. Claude Code → OpenCode** (`core/claude_code_bridge.py`, new)
```
Claude Code task complete
  → skill writes session to .wiki/claude-code/sessions/
  → If task is coding+file-write: spawn OpenCode for implementation
    via subprocess: opencode run <task-prompt>
  → OpenCode writes session to .wiki/opencode/sessions/
  → Claude Code reads that log for verification
```

**D. LegionBot ↔ OpenCode** (already exists, but upgraded)
- `opencode_query_wiki()` already reads OpenCode sessions
- Upgrade to include `@legion` directive parsing → LegionBot can spawn OpenCode sub-tasks that call back
- Recursive depth tracking: max 3 nested spawns to prevent infinite loops

### Layer 3 — Shared Skills & Agents

```
.skills/  (shared by gstack/OpenCode/Claude Code via symlinks)
├── gstack/                    # gstack skills (OpenCode host-aware)
│   └── hosts/opencode.ts       # Host config (path rewriting)
├── swarm/                      # Swarm orchestration
│   └── swarm.md                # /swarm command (planner→worker→diff→reviewer)
├── legiona/                    # Shared agent definitions
│   ├── coding.md              # @coding agent (shared prompt)
│   ├── reviewer.md            # @reviewer agent
│   └── researcher.md           # @researcher agent
└── skills/                     # Cross-system skill stubs
    ├── opencode-to-legion.md  # OpenCode→Legion callback protocol
    ├── claude-to-opencode.md  # Claude Code→OpenCode delegation
    └── joint-brain.md         # Shared memory protocol
```

**Shared agents**: Both OpenCode and Claude Code reference the same agent definition files. When an agent definition updates, both systems pick it up automatically.

**gstack host config** (`ext/skills/gstack/hosts/opencode.ts`): Already maps `.claude/skills/gstack` → `.opencode/skills/gstack`. We add `legiona/` to the path rewrite list so shared agent definitions are found by both systems.

**LegionBot integration**: `agents.py` in LegionBot is updated to reference the same agent definition files (`legiona/coding.md`, etc.) via the `legion_agents/` lookup.

### Layer 4 — Unified Task Pipeline

The 4-agent pipeline (`planner → worker → diff-analyzer → reviewer`) from OpenCode's `.opencode/command/swarm.md` becomes the **universal task execution model** used by all three systems:

```
Task received
  ↓
@planner  (decomposes into CONTRACTS)  ← OpenCode planner agent
  ↓
@worker   (executes + proves completion) ← OpenCode worker agent
  ↓
@diff-analyzer  (verifies before review)  ← OpenCode diff-analyzer
  ↓
@reviewer  (quality gate)  ← OpenCode reviewer agent
  ↓
[Result] → written to .wiki/{opencode,claude-code}/sessions/
  ↓
LegionBot reads session → builds Telegram response
```

**LegionBot as orchestrator**: When `/run <complex-task>` is received, LegionBot:
1. Routes to OpenCode via `opencode_bridge.py`
2. OpenCode runs the full 4-agent pipeline
3. Session is written to `.wiki/opencode/sessions/`
4. `_opencode_brain_layer()` in LegionBot reads the session
5. Telegram response is crafted from the session log

**Claude Code as reviewer**: When OpenCode's `@reviewer` issues a `FIX` directive, the task can be escalated to Claude Code for a second opinion via the `claude_code_bridge.py`.

---

## 3. Cross-System Data Flows

### Flow 1: OpenCode Completes → LegionBot Notifies User
```
User sends "/opencode implement authentication"
  → handlers/dev.py → opencode_bridge.run_opencode_task()
  → OpenCode 4-agent pipeline executes
  → Session written to .wiki/opencode/sessions/2026-04-16-abc123.md
  → builtin_hooks: opencode_session_end_hook() fires
  → hooks writes Telegram-formatted summary to .wiki/opencode/sessions/summary-pending.md
  → LegionBot reads summary on next interaction
  → User receives Telegram message with result
```

### Flow 2: Claude Code Completes → OpenCode Implements
```
User sends "/codex implement auth middleware"
  → Claude Code skill runs → produces implementation plan
  → Skill writes plan to .wiki/claude-code/sessions/session.md
  → claude_code_bridge detects @opencode directive in result
  → spawns: opencode run "implement the auth middleware per .wiki/claude-code/sessions/session.md"
  → OpenCode writes implementation session to .wiki/opencode/sessions/
  → Claude Code reviews the implementation
```

### Flow 3: LegionBot Deep Research → OpenCode Implements
```
User sends "/research compare database options for auth"
  → LegionBot routes to research agent
  → research agent writes analysis to .wiki/research/db-comparison.md
  → opencode_query_wiki() surfaces findings to OpenCode
  → OpenCode @worker executes based on research
  → diff-analyzer verifies against research criteria
  → reviewer approves or requests research update
```

---

## 4. Key Components to Build

### New Files

| File | Purpose |
|------|---------|
| `core/joint_memory.py` | Unified facade: all 3 systems write through this |
| `core/claude_code_bridge.py` | Bidirectional Claude Code ↔ OpenCode/LegionBot bridge |
| `core/legion_callback_bridge.py` | LegionBot → OpenCode callback + recursive spawn tracking |
| `.wiki/joint-brain/joint-memory-protocol.md` | Protocol for joint memory writes |
| `.opencode/agents/legiona/` | Shared agent definitions (symlinked from `.claude/skills/legiona/`) |
| `.claude/skills/legiona/` | Source of truth for shared agent definitions |
| `ext/skills/gstack/hosts/legionbot.ts` | gstack host config for LegionBot |
| `.opencode/command/legion-callback.md` | OpenCode command for calling back to LegionBot |

### Modified Files

| File | Change |
|------|--------|
| `core/opencode_bridge.py` | Add directive parsing (`@legion`, `@claude`), callback hooks |
| `core/unified_prompt_context.py` | Add `_claude_code_brain_layer()` alongside `_opencode_brain_layer()` |
| `core/builtin_hooks.py` | Add `claude_code_session_hook` alongside `opencode_session_hook` |
| `core/wiki_bridge.py` | Add `claude_code_write_session()` alongside `opencode_write_session_summary()` |
| `ext/skills/gstack/hosts/opencode.ts` | Add `legiona/` to path rewrite rules |
| `agents.py` | Reference shared agent definitions from `legiona/` |
| `main.py` | Register LegionBot ↔ OpenCode ↔ Claude Code health probes |

### gstack Host Config Additions (`ext/skills/gstack/hosts/legionbot.ts`, new)
```typescript
const legionbot: HostConfig = {
  name: 'legionbot',
  displayName: 'LegionBot',
  cliCommand: 'python3 main.py',  // or service-based
  globalRoot: '.config/legion/skills',
  localSkillRoot: '.claude/skills/legion',
  hostSubdir: '.claude',
  pathRewrites: [
    { from: '.opencode/skills/gstack', to: '.claude/skills/gstack' },
    { from: '.opencode/agents', to: '.claude/skills/legiona' },
  ],
  // ...
};
```

---

## 5. Anti-Hallucination Enforcement

All three systems share the same anti-hallucination rules from OpenCode's `command/swarm.md`:
1. After every file write: READ it back immediately
2. After every bash command: show actual stdout/stderr
3. Never report complete without PROOF_FORMAT output visible
4. Never modify `.env` or credential files
5. Never run `rm -rf`

LegionBot's `soul_engine.py` injects these rules into the system prompt for all `/run` tasks.

---

## 6. Session & Memory Architecture

### Joint Brain Directory Structure
```
.wiki/
├── opencode/
│   └── sessions/          # OpenCode pipeline sessions
├── claude-code/
│   └── sessions/          # Claude Code session logs
├── joint-brain/
│   ├── memory-protocol.md # Unified write/read protocol
│   └── cross-refs/       # Cross-references between sessions
└── [existing structure]
```

### Shared Memory API (`core/joint_memory.py`)
```python
async def joint_save(content: str, source: str, tags: list[str]) -> int:
    """Write to joint brain. source: 'opencode' | 'claude-code' | 'legionbot'"""

async def joint_search(query: str, sources: list[str] | None = None) -> list[dict]:
    """Search across all sources or filter to specific ones."""

async def joint_get_recent(days: int = 7, sources: list[str] | None = None) -> list[dict]:
    """Get recent session summaries across all systems."""
```

---

## 7. Error Handling & Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|---------|
| OpenCode server down | Health probe in `main.py` | Auto-restart via subprocess management |
| Claude Code process timeout | `subprocess.run(timeout=180)` | Fall back to OpenCode-only pipeline |
| Infinite recursive spawn | Depth counter in `legion_callback_bridge.py` (max 3) | Stop at max depth, report to user |
| Wiki write failure | `try/except` in `joint_memory.py` | Log error, do not crash parent pipeline |
| Session read failure | Empty result + logged warning | Downstream system proceeds without session |

---

## 8. Testing

### Smoke Tests
```bash
# Joint memory
python3 -c "from core.joint_memory import joint_save, joint_search; print('joint_memory ok')"

# OpenCode bridge with directive parsing
python3 -c "from core.opencode_bridge import extract_report; print(extract_report('hello @legion'))"

# Claude Code bridge
python3 -c "from core.claude_code_bridge import run_claude_task; print('claude_code_bridge ok')"

# Wiki session ingestion
python3 -c "from core.wiki_bridge import opencode_write_session_summary; print('wiki_bridge ok')"
```

### Integration Tests
```bash
# OpenCode → wiki session write
cd /home/newadmin/swarm-bot && python3 -c "
import asyncio, subprocess
result = subprocess.run(['opencode', 'run', 'write a test file'], capture_output=True, timeout=30)
print(result.stdout[:200])
"

# Joint memory across sources
python3 -c "
import asyncio
from core.joint_memory import joint_save, joint_search
async def test():
    id1 = await joint_save('opencode test', 'opencode', ['test'])
    id2 = await joint_save('claude code test', 'claude-code', ['test'])
    results = await joint_search('test', sources=None)
    print(f'Search returned {len(results)} results')
asyncio.run(test())
"
```

---

## 9. Rollout Plan

**Phase 1 — Joint Memory (Layer 1)**
- Build `core/joint_memory.py` facade
- Migrate `opencode_write_session_summary()` and `claude_code_write_session()` to use facade
- Add `_claude_code_brain_layer()` to `unified_prompt_context.py`
- Test: all 3 systems can read/write the same vault

**Phase 2 — Claude Code Bridge (Layer 2 partial)**
- Build `core/claude_code_bridge.py`
- Wire `run_claude_task()` into `opencode_bridge.py` for @claude directive spawning
- Add `.wiki/claude-code/sessions/` directory + wiki writer
- Test: OpenCode can spawn Claude Code and vice versa

**Phase 3 — LegionBot Callback Bridge (Layer 2 partial)**
- Build `core/legion_callback_bridge.py`
- Add `@legion` directive parsing to `opencode_bridge.py`
- Add recursive depth tracking
- Test: OpenCode can call back to LegionBot without Telegram round-trip

**Phase 4 — Shared Skills & Agents (Layer 3)**
- Create `.claude/skills/legiona/` with shared agent definition stubs
- Add symlinks from `.opencode/agents/legiona/` and `swarm-bot/agents/`
- Update gstack host config for `legiona/` path rewriting
- Test: OpenCode and Claude Code use same agent definitions

**Phase 5 — Unified Pipeline (Layer 4)**
- Wire OpenCode 4-agent pipeline as universal executor for all 3 systems
- Add `/codex` command handler in `handlers/dev.py`
- Add `/legion` command handler in OpenCode command suite
- Test: full round-trip between all 3 systems

---

## 10. Spec Self-Review

- [ ] Placeholder scan: No "TBD", "TODO", or vague requirements ✓
- [ ] Internal consistency: All 4 layers are mutually consistent ✓
- [ ] Scope: Focused on integration, not re-building any single system ✓
- [ ] Ambiguity: Directive names (`@legion`, `@claude`) are explicit; depth limits specified ✓

---

## 11. Success Criteria

After full implementation:
- [ ] `joint_memory.py` is the single write path for all 3 systems
- [ ] OpenCode can spawn Claude Code tasks and receive results back via wiki session logs
- [ ] Claude Code can spawn OpenCode tasks for implementation
- [ ] LegionBot can spawn OpenCode with recursive depth tracking (max 3)
- [ ] OpenCode can call back to LegionBot via `@legion` directive (no Telegram round-trip needed)
- [ ] All 3 systems share the same anti-hallucination rules
- [ ] Smoke tests pass for all new modules
- [ ] Session logs from all 3 systems appear in `.wiki/joint-brain/cross-refs/`
