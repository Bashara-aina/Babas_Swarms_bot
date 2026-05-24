# Triage Label Mapping

Canonical triage roles and their configured label strings.

## Canonical Roles

| Role | Purpose | GitHub Label | GitLab Label |
|------|---------|--------------|--------------|
| `needs-triage` | Maintainer needs to evaluate | `needs-triage` | `needs-triage` |
| `needs-info` | Waiting on reporter for info | `needs-info` | `needs-info` |
| `ready-for-agent` | Fully specified, AFK-ready | `ready-for-agent` | `ready-for-agent` |
| `ready-for-human` | Needs human implementation | `ready-for-human` | `ready-for-human` |
| `wontfix` | Will not be actioned | `wontfix` | `wontfix` |
| `bug` | Category: something is broken | `bug` | `bug` |
| `enhancement` | Category: new feature/improvement | `enhancement` | `enhancement` |

## Default Mapping

By default, each role maps to its own name. Override below only if your tracker uses different strings.

## Override Format

```yaml
# Example: GitHub uses different format
needs-triage: "bug:triage"
needs-info: "waiting-on-reporter"
ready-for-agent: "ready-for-agent"
ready-for-human: "ready-for-human"
wontfix: "wontfix"
bug: "bug"
enhancement: "enhancement"
```

## Custom Labels

If your tracker uses a different vocabulary, list the overrides:

| Canonical | Your Tracker |
|----------|--------------|
| `needs-triage` | `<your-label>` |
| `needs-info` | `<your-label>` |
| `ready-for-agent` | `<your-label>` |
| `ready-for-human` | `<your-label>` |
| `wontfix` | `<your-label>` |

## State Machine

```
Unlabeled → needs-triage
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
needs-info  ready-for-agent  ready-for-human
    ↓           ↓           (human-only)
    ↓           ↓
    → needs-triage ← (reporter replied)
              ↓
           wontfix
```

Each issue should have exactly ONE category role (bug/enhancement) and ONE state role.