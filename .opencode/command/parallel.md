---
description: >-
  Run multiple OpenCode swarm sessions in parallel using git worktrees.
  Each worktree is an independent session with its own branch and working directory.
  Use when tasks can be split into independent parallel streams.
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---
# /parallel — Multi-Session Parallel Execution

## WHEN TO USE

Use `/parallel` when:
- Task splits into independent streams (e.g., audit A + audit B simultaneously)
- Multiple agents need concurrent execution
- You want faster throughput on parallelizable work
- Research + implementation can happen in parallel

## ARCHITECTURE

Each parallel session runs in a **git worktree** — a separate working directory with its own branch, all sharing the same git repository:

```
~/.claude/worktrees/
├── registry.json          # Shared coordination state
├── main/                  # Main trunk worktree (this session)
├── parallel-1/            # Session 1 worktree
├── parallel-2/            # Session 2 worktree
└── parallel-3/           # Session 3 worktree
```

**Benefits:**
- Zero VRAM/RAM conflict (each session is separate process)
- Independent model loading (ollama stop/start per session)
- Shared git history (commits from any worktree visible everywhere)
- Shared registry for coordination

## COORDINATION LIBRARY

Located at `~/.claude/lib/`:

```bash
cd ~/.claude/lib
python cli.py --help

# Commands:
#   init        Initialize worktree system for a repo
#   create      Create new worktree session
#   list        List all active sessions
#   locks       Show advisory locks
#   analyze     Analyze divergence between branches
#   merge       Coordinate merge of completed worktrees
#   awareness   Generate awareness prompt block
#   heartbeat   Start session heartbeat daemon
```

## USAGE

### Initialize (one-time setup)
```
/parallel init --repo /home/newadmin/swarm-bot --root ~/.claude/worktrees
```

### Create parallel sessions
```
/parallel create session-A --task "Audit opencode agents"
/parallel create session-B --task "Write browser automation tests"
/parallel create session-C --task "Review memory system"
```

### List active sessions
```
/parallel list
```

### Generate awareness block (for each new session)
```
# Run in each worktree after creation
python awareness_prompt.py --session session-A
```

### Coordinate merge after completion
```
/parallel analyze --session session-A
# Review what changed in each worktree
/parallel merge --session session-A --target main
```

### Heartbeat (keep session alive)
```
python heartbeat.py session-A --registry ~/.claude/worktrees/registry.json &
```

## WORKFLOW EXAMPLE

### Scenario: Audit ALL opencode agents + write tests simultaneously

**Terminal 1 (main session):**
```
/parallel create audit-workers --task "Audit .opencode/agents/ for quality"
/parallel create audit-reviewers --task "Audit .opencode/agents/review/ for coverage"
/parallel create audit-commands --task "Audit .opencode/command/ for completeness"
```

**In each new session:**
```
# Session: audit-workers
/swarm audit .opencode/agents/ --depth comprehensive

# Session: audit-reviewers  
/swarm audit .opencode/agents/review/ --depth comprehensive

# Session: audit-commands
/swarm audit .opencode/command/ --depth comprehensive
```

**After completion:**
```
/parallel merge --session audit-workers --target main
/parallel merge --session audit-reviewers --target main
/parallel merge --session audit-commands --target main
```

## LOCK MECHANISM

Advisory locks prevent conflicting writes:

```bash
# Session A wants to edit handlers/ai.py
/advisory_lock acquire handlers/ai.py
# → Returns lock_id if acquired, blocks if held by another

# Session A finishes editing
/advisory_lock release handlers/ai.py --lock_id [lock_id]
```

**Lock types:**
- `WRITE` — exclusive access for modification
- `READ` — shared access for reading
- `MERGE` — acquired automatically on merge

## AWARENESS BLOCK

Each session needs awareness of others to avoid duplicate work:

```
python awareness_prompt.py --session session-A
# → Outputs block to add to system prompt:
#    "Other sessions running: [session-B: editing handlers/ai.py]"
```

## ANTI-HALLUCINATION RULES

1. **Acquire locks before writing** — prevent branch conflicts
2. **Report completion to registry** — other sessions should know
3. **Merge before starting related work** — don't pile up unmerged branches
4. **Check registry before creating** — don't exceed hardware capacity
5. **Heartbeat to stay alive** — sessions without heartbeat may be cleaned up

## HARDWARE CAPACITY

| VRAM | Max Parallel Sessions |
|------|------------------------|
| 12GB (RTX 3060) | 2-3 sessions (depends on model sizes) |
| 24GB+ | 4-6 sessions |

Monitor with `nvidia-smi` or `ollama list`.

## STATUS
```
PARALLEL STATUS: ✅ [operation] | ❌ FAILED
Active sessions: [N]
Registry: ~/.claude/worktrees/registry.json
Locks held: [N]
```

## EXAMPLE SESSION
```
# Initialize
/parallel init --repo /home/newadmin/swarm-bot --root ~/.claude/worktrees

# Create 3 parallel audit sessions
/parallel create audit-agents --task "Audit .opencode/agents/"
/parallel create audit-review --task "Audit review agents"
/parallel create audit-mcp --task "Audit MCP agents"

# In each session (parallel):
/swarm audit .opencode/agents/ --depth comprehensive
/swarm audit .opencode/agents/review/ --depth comprehensive
/swarm audit .opencode/agents/mcp/ --depth comprehensive

# Merge results
/parallel merge --session audit-agents --target main
/parallel merge --session audit-review --target main
/parallel merge --session audit-mcp --target main
```
