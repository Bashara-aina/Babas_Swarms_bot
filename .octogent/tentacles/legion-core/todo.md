# Todo

- [ ] Verify bot starts cleanly after all integrations (hermes + mirofish)
- [ ] Add /octogent command to Telegram that shows current agent status
- [ ] Add error recovery: auto-restart on unhandled exceptions with Telegram alert
- [ ] Write tools/health_check.py — checks all services (MiroFish, Hermes, Redis)
- [ ] Add rate limiting to all Telegram commands (cooldown per user)
- [ ] Implement tools/session_bridge.py — lets Octogent terminals send results back to Telegram
- [ ] Add daily 23:00 WIB digest: summarize all tool calls made that day
- [ ] Update CLAUDE.md to include Octogent tentacle IDs for routing context