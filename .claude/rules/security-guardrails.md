# Security Guardrails for Claude Code

## Core Rules
1. **Never commit secrets**: API keys, tokens, passwords, private keys
2. **Never execute destructive commands**: rm -rf, mkfs, dd, force push
3. **Never read .env files directly**: Use Read tool if needed
4. **Never write to .env**: Use env vars or settings.local.json
5. **Never disable hooks**: `disableAllHooks: true` requires explicit user request
6. **Never expose permissions**: Keep deny list populated

## Configuration Audit Checklist
- [ ] `permissions.deny` includes dangerous patterns
- [ ] `permissions.allow` has no bare wildcards (`*`)
- [ ] No API keys in settings.json `env` section
- [ ] Hook scripts validate their input
- [ ] MCP server commands use fixed paths, not user-supplied args

## ECC-Derived Patterns
- **Atomic operations**: One instinct = one trigger + one action
- **Confidence decay**: Unused instincts decay 0.05 per week
- **Observation window**: Keep last 1000 observations, prune old
- **Project scope**: Instincts scoped via git remote hash
