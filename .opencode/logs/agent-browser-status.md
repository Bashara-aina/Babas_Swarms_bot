# agent-browser status

## Result
- Install: PASS
- Native workflow: PASS
- MiniMax-only policy: PASS
- Chat mode: DISABLED (hardened to block non-MiniMax models)

## Binary
- Path: /home/newadmin/.local/node18/bin/agent-browser
- Version: 0.26.0
- Chrome: Google Chrome for Testing 148.0.7778.97 (newly downloaded)

## Validation
- doctor: PASS (8/8 checks passed)
- open + snapshot: PASS
- batch: PASS
- chat hardening: PASS (blocked claude-sonnet-4.6)

## Files created
- scripts/agent-browser-safe.sh (wrapper with MiniMax lock)
- scripts/agent-browser-project.sh (config-pinned wrapper)
- agent-browser.json (project config)
- .opencode/skills/agent-browser.md (skill stub)
- .opencode/command/browser.md (slash command)
- .opencode/logs/agent-browser-version.txt
- .opencode/logs/agent-browser-doctor.json
- .opencode/logs/agent-browser-example-snapshot.json
- .opencode/logs/agent-browser-batch.json
- .opencode/logs/agent-browser-bin-path.txt

## Files modified
- AGENTS.md (added Browser Automation section)
- CLAUDE.md (added agent-browser policy)

## Chat status
Chat is disabled by default. The safe wrapper hard-blocks any AI_GATEWAY_MODEL
matching claude|anthropic|gpt|openai|gemini|groq|together.
If chat is needed with MiniMax, the AI_GATEWAY_MODEL must be explicitly set to
`minimax/MiniMax-M2.7` and the proxy at localhost:4000 must be compatible.

## Notes
- System deps install required sudo but Chrome was downloaded successfully
- daemon requires first open before other commands
- --ignore-https-errors warning is non-critical (daemon already running)