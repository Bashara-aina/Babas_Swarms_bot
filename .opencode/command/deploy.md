---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [files-or-subdirectory]
description: "Deploy to production. Restart swarm-bot systemd service, verify logs, confirm bot responds."
---

# /deploy — Deploy to production

Deploy code changes to the running swarm-bot service.

## Usage
```
/deploy
/deploy handlers/
/deploy core/
```

## Pre-deployment Checklist
```
- [ ] Tests pass: pytest tests/ -x --asyncio-mode=auto -q
- [ ] No .env or secrets in diff
- [ ] Code looks correct in diff
- [ ] Announce maintenance window if needed
```

## Deployment Steps
1. Stage and commit changes (or confirm already committed)
2. Pull latest on server
3. Restart systemd service
4. Verify clean startup in logs
5. Confirm bot responds

## Commands Run
```bash
# Pull latest
git pull

# Restart service
sudo systemctl restart swarm-bot

# Check logs
journalctl -u swarm-bot -n 50 --no-pager

# Verify status
sudo systemctl status swarm-bot
```

## Rollback
```bash
sudo systemctl stop swarm-bot
git revert HEAD  # or git checkout <prev>
sudo systemctl start swarm-bot
```

## Constraints
- Only deploy from main branch
- Always verify tests before deploying
- Check logs after restart
- Never deploy with uncommitted changes
