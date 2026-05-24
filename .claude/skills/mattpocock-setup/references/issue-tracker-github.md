# Issue Tracker: GitHub

**Type:** GitHub Issues

**CLI:** `gh` (GitHub CLI)

**Location:** Repo → Issues on GitHub

## Setup

Ensure `gh` is authenticated:

```bash
gh auth login
```

## Reading Issues

```bash
# List open issues
gh issue list

# View specific issue
gh issue view <number>

# Filter by label
gh issue list --label "needs-triage"
```

## Writing Issues

```bash
# Create issue with title and body
gh issue create --title "Bug: checkout fails" --body "Steps to reproduce..."

# Create with labels
gh issue create --label "bug,needs-triage"
```

## Triage Integration

The triage skill reads labels via `gh issue list --label <label>` and updates via `gh issue edit <number> --add-label` / `--remove-label`.

## Workflow

1. **Read:** `gh issue list` → shows all issues with status, labels
2. **Triage:** Read issue body, apply labels via `gh issue edit`
3. **Create:** `gh issue create` with description for new issues
4. **Close:** `gh issue close <number>` with comment explaining decision