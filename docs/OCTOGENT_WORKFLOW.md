# Octogent Workflow Guide

> How to use Octogent as the multi-agent orchestration UI for the Legion Elite Stack.

## Quick Start

```bash
# Start Octogent dashboard
./scripts/start_octogent.sh start

# Open browser manually
open http://localhost:8788

# Check status
./scripts/start_octogent.sh status

# Stop
./scripts/start_octogent.sh stop
```

## Architecture

Octogent runs as a web dashboard at `http://localhost:8788` with a CLI backend.

```
Browser (8788) ←→ Octogent Server ←→ Tentacle Files (.octogent/tentacles/)
                              ←→ Legion stack (agents, handlers, tools)
```

## Your 6 Tentacles

| Tentacle | Project | Focus |
|---|---|---|
| `legion-core` | swarm-bot | Telegram bot, agent registry, orchestration core |
| `mirofish` | mirofish | Financial market analysis pipeline |
| `cekwajar` | cekwajar | Indonesian B2C SaaS (gaji, slip, tanah, kabur) |
| `rumahlabuh` | rumahlabuh | Real estate marketplace for kos & rental |
| `research` | research | Academic research (Shibaura Institute) |
| `popw` | popw | POPW project tracking |

## Daily Workflow

### Morning: Start Session

```bash
# Option A: Single terminal (blocks)
./scripts/start_octogent.sh start

# Option B: Tmux multi-window (recommended for parallel work)
./scripts/octogent_worksession.sh
```

### During Work

1. **Pick a tentacle** from the Octogent dashboard
2. **Read CONTEXT.md** to understand current state
3. **Update todo.md** as you complete tasks
4. **Use child agents** for parallel sub-tasks — see CLAUDE.md for routing rules

### Evening: Commit

```bash
# Save work, then commit tentacles with structured message
cd /home/newadmin/swarm-bot
git add .octogent/tentacles/
git commit -m "feat(octogent): update tentacles — $(date +%Y-%m-%d)

- legion-core: <what changed>
- cekwajar: <what changed>
- rumahlabuh: <what changed>
- mirofish: <what changed>
- research: <what changed>
- popw: <what changed>"
```

## File Locations

```
.octogent/
├── tentacles/
│   ├── legion-core/   # CONTEXT.md + todo.md
│   ├── mirofish/      # CONTEXT.md + todo.md
│   ├── cekwajar/      # CONTEXT.md + todo.md
│   ├── rumahlabuh/    # CONTEXT.md + todo.md
│   ├── research/      # CONTEXT.md + todo.md
│   └── popw/          # CONTEXT.md + todo.md
├── worktrees/         # Git worktrees for parallel project work (gitignored)
└── state/             # Runtime state (gitignored)
```

## Octogent CLI Reference

```bash
octogent --help              # All commands
octogent tentacle list       # List all tentacles
octogent tentacle <name>     # Open specific tentacle
octogent agent spawn <type>  # Spawn a child agent
octogent status              # System health
```

## Troubleshooting

**Octogent won't start:**
```bash
tail -f /tmp/octogent_legion.log
```

**Port 8788 occupied:**
```bash
# Check what's using it
ss -tlnp | grep 8788

# Change port
OCTOGENT_PORT=8789 ./scripts/start_octogent.sh start
```

**node-pty fails to load:**
```bash
# Rebuild from source
cd /home/newadmin/octogent/node_modules/.pnpm/node-pty@1.1.0/node_modules/node-pty
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && nvm use 22
CFLAGS="-I/home/newadmin/.nvm/versions/node/v22.22.2/include/node" \
CXXFLAGS="-I/home/newadmin/.nvm/versions/node/v22.22.2/include/node" \
node-gyp build
```