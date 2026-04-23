# Babas Agency Swarm — OpenCode Memory Index

## Machine
- Host: takamatsu-System-Product-Name, user: newadmin
- GPU: NVIDIA RTX 3060 (12GB VRAM), RAM: 64GB
- Ollama at http://localhost:11434, CUDA_VISIBLE_DEVICES=0
- Venv: /home/newadmin/swarm-bot/.venv
- Framework: aiogram 3.x async Telegram bot, litellm multi-provider

## Project
- Path: /home/newadmin/swarm-bot/
- GitHub: https://github.com/Bashara-aina/Babas_Swarms_bot
- Service: swarm-bot.service (systemd)
- Architecture: multi-agent Telegram bot with 84 agents across 9 departments

## OpenCode System
- Root: .opencode/
- Core agents: .opencode/agent/ (planner, worker, reviewer, diff-analyzer, memory, collaborator)
- Domain agents: .opencode/agents/ (38 specialized domains)
- Commands: .opencode/command/ (swarm, commit, deploy, fix, audit, etc.)
- Pipeline: planner → worker → diff-analyzer → reviewer (4-agent loop)

## Hard Rules
- Never run `rm -rf` or destructive commands
- Never modify `.env`, `.env.*` or files with real credentials
- Always verify file writes with `cat` before reporting complete
- Never report ✅ without PROOF_FORMAT output pasted

## Known Issues & Fixes
- TelegramBadRequest: use parse_mode="HTML" + html.escape()
- Ollama VRAM overflow: stop model before loading next
- sentence-transformers: working on cuda:0 (all-MiniLM-L6-v2)

## Memory Files
- [project/swarm-bot-architecture.md](project/swarm-bot-architecture.md) — full architecture map
- [project/popw-benchmark-system.md](project/popw-benchmark-system.md) — POPW benchmark comparison system (IKEA ASM + IndustReal)
- [user/bashara-identity.md](user/bashara-identity.md) — user identity and preferences
- [feedback/opencode-tool-permissions.md](feedback/opencode-tool-permissions.md) — tool permission fixes applied

- [feedback/agents-init-lint-fix.md](feedback/agents-init-lint-fix.md) — import sorting + Coroutine type fix
- [feedback/ruff-f821-fix-session-status.md](feedback/ruff-f821-fix-session-status.md) — _update_state undefined name fix in session-status.py
- [feedback/ruff-remaining-errors.md](feedback/ruff-remaining-errors.md) — remaining ruff F841/E741/invalid-syntax errors

## Last Updated
2026-04-23
