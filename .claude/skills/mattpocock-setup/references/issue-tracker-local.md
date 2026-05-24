# Issue Tracker: Local Markdown

**Type:** Markdown files in repo

**Location:** `.scratch/<feature>/` subdirectories

**Good for:** Solo projects, repos without GitHub/GitLab, offline work

## Directory Structure

```
.scratch/
├── README.md              # Index of all issues
├── 2024-01-bugfix/
│   ├── 001-checkout-fails.md
│   └── 002-login-timeout.md
└── 2024-02-features/
    └── 001-new-dashboard.md
```

## File Format

```markdown
---
id: 001
title: Checkout fails with empty cart
status: open
labels: [bug, needs-triage]
created: 2024-01-15
updated: 2024-01-16
---

## Description

Checkout crashes when cart is empty.

## Steps to reproduce

1. Go to /checkout
2. Click "Pay" with no items

## Notes

- Bug introduced in commit abc123
- Affects ~5% of users
```

## Index Format (README.md)

```markdown
# Scratchpad Issues

## Open Issues

| ID | Title | Status | Updated |
|----|-------|--------|---------|
| 001 | Checkout fails | open | 2024-01-15 |
| 002 | Login timeout | in-progress | 2024-01-14 |

## Closed Issues

...
```

## Workflow

1. **Read:** `grep` the `.scratch/` directory for open issues
2. **Create:** New file with `id: XXX` format
3. **Update:** Edit frontmatter `status` and `labels`
4. **Close:** Move to `.scratch/closed/` subdirectory or mark `status: closed`