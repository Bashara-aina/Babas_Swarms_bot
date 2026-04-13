---
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: [target-env] [--rollback] | production | staging | --rollback
description: Deploy the bot to production or staging with health verification and rollback capability
---

# /deploy — Deployment with Health Verification

## STEP 1 — Pre-Deployment Checks

Run these before any deployment:
```
git status
git log --oneline -3
```

Verify no uncommitted changes that should be included:
```
pytest tests/ -x --asyncio-mode=auto -q 2>/dev/null || echo "Tests skipped"
```

Check service status:
```
systemctl status swarm-bot --no-pager
```

## STEP 2 — Deploy to TARGET

If TARGET = staging:
```bash
cd /home/newadmin/swarm-bot
git pull origin main
systemctl restart swarm-bot
sleep 5
systemctl status swarm-bot --no-pager
```

If TARGET = production:
- **ALWAYS get user confirmation before proceeding**
- Create a backup tag first:
```bash
git tag "backup-$(date +%Y%m%d-%H%M%S)"
git push origin --tags
```
- Then restart:
```bash
systemctl restart swarm-bot
sleep 5
systemctl status swarm-bot --no-pager
```

If --rollback:
```bash
git checkout <previous-tag>
git pull origin <previous-tag>
systemctl restart swarm-bot
```

## STEP 3 — Health Verification

Run health checks:
```
# Check bot responds
python -c "from core.soul_engine import build_soul_context; print('soul ok')"
python -c "from core.intent_router import IntentRouter; print('router ok')"

# Check service logs
journalctl -u swarm-bot --since "5 minutes ago" --no-pager | tail -20
```

## STEP 4 — Report

Report deployment status with timestamp and any issues.
