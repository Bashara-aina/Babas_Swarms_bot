# ECC Enterprise Controls

## Governance

- `ECC_GOVERNANCE_CAPTURE=1` — enables secrets/policy violation capture
- Governance logs at `.superpowers/governance/alerts.log`
- Review before any public release or audit

## Security Controls

1. All commits scanned for secrets (via security-prehook.sh + governance capture)
2. Config protection blocks linter/formatter weakening
3. MCP health tracking prevents calls to unhealthy servers
4. Session activity tracking provides audit trail

## Audit Trail

- Tool call logs at `.superpowers/metrics/`
- Session activity at `.superpowers/activity/`
- Quality gate reports at `.superpowers/quality-gate/`
- Cost tracking at `.superpowers/metrics/cost-log.jsonl`

## Profiles

| Profile | Security | Governance | Monitoring | Quality |
|---------|----------|------------|------------|---------|
| minimal | ✅ | ❌ | ❌ | ❌ |
| standard | ✅ | ⚠️ (opt-in) | ✅ | ❌ |
| strict | ✅ | ✅ | ✅ | ✅ |

## Policy

- Config files (pyproject.toml, ruff.toml, .eslintrc, etc.) must NOT be weakened
- Secrets must never be committed
- All edits should pass `make check`
- Session activity should be reviewed periodically
