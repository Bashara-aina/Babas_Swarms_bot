---
description: >-
  Safety guard for destructive or irreversible operations. Always runs before
  executing: rm, DROP TABLE, git push --force, DELETE operations, schema migrations,
  or any operation that cannot be undone. Use when: running destructive commands,
  migrating databases, force-pushing, or any operation where rollback is difficult.
  This is a mandatory safety check.
allowed-tools: Bash, Read, Grep, Glob
argument-hint: [the command you want to run]
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---

# /careful — Destructive Operation Safety Guard

## PURPOSE

This skill runs BEFORE any potentially destructive operation. It:
1. Explains exactly what will happen
2. Identifies what cannot be undone
3. Suggests rollback procedures
4. Requires explicit confirmation

## SAFETY CHECKLIST

Before any destructive operation, run through this checklist:

### Tier 1 — Filesystem Operations

```bash
# What files will be affected?
echo "Operation: [command]"
echo "Files at risk:"

# Check what rm would delete
rm -nv [path] 2>&1 | head -20  # dry-run with verbose

# Check git status
git status
```

### Tier 2 — Database Operations

```bash
# Check if there's a backup
ls -la [backup_dir] 2>/dev/null | tail -5

# Check migration status
python -m alembic history 2>/dev/null | head -10 || echo "Alembic not available"
```

### Tier 3 — Remote Operations

```bash
# Force push risk assessment
echo "Current branch: $(git branch --show-current)"
echo "Remote tracking: $(git rev-parse --abbrev-ref HEAD@{upstream} 2>/dev/null || echo 'no upstream')"

# Check if others have pushed since last fetch
git fetch origin
git status
```

## OPERATION CLASSIFICATION

Classify the operation:

| Class | Risk | Examples |
|-------|------|----------|
| 🔴 CRITICAL | Irreversible, affects others | DROP TABLE, rm -rf, force push to shared branch |
| ⚠️ HIGH | Difficult to undo, scoped | DELETE rows, git push --force (own branch) |
| ⚠️ MEDIUM | Undoable with effort | DELETE, schema change without migration |
| ✅ LOW | Easily reversible | CREATE, INSERT, git push (normal) |

## REQUIRED FOR CRITICAL OPERATIONS

For 🔴 CRITICAL operations, you MUST:

1. **Document the current state:**
```bash
# For filesystem: list what exists
ls -la [affected_path]

# For database: capture current schema
pg_dump --schema-only [table] 2>/dev/null || echo "No pg_dump available"

# For git: capture current commit
git rev-parse HEAD
```

2. **Write rollback procedure:**
```
ROLLBACK:
  step 1: [exact command to undo]
  step 2: [exact command to verify rollback]
```

3. **Get explicit confirmation:**
```
⚠️ DESTRUCTIVE OPERATION: [command]
This is IRREVERSIBLE. Before proceeding:

1. [State exactly what will happen]
2. [State what cannot be undone]
3. [State the rollback procedure above]

Confirm: A) Proceed  B) Abort
```

## ANTI-HALLUHALLUCINATION RULES

1. Never run the destructive command in dry-run analysis — only analyze
2. Classify honestly — don't downgrade risk to avoid friction
3. If rollback is unclear, STOP and figure it out before proceeding
4. For shared branches: ALWAYS classify force-push as CRITICAL

## OUTPUT FORMAT

```
CAREFUL ANALYSIS: [operation]
═══════════════════════════════════

COMMAND: [exact command]
CLASSIFICATION: 🔴 CRITICAL | ⚠️ HIGH | ⚠️ MEDIUM | ✅ LOW

AFFECTED:
- [list of files/resources]

CAN BE UNDONE: [YES/NO]
IF NO: [why not]

ROLLBACK PROCEDURE:
1. [step]
2. [step]

SAFETY CHECKS:
[ ] Backup exists or captured
[ ] Rollback tested or documented
[ ] Users notified (if shared resource)

CONFIRMATION REQUIRED: YES/NO
```
