# PRD Template Guide

Full template reference for writing Product Requirements Documents.

## Complete PRD Template

```markdown
## Problem Statement

[What problem does this solve? From the user's perspective.
What pain exists today?]

## Solution

[How does this solve the problem? From the user's perspective.
What does the user see/feel that's different?]

## User Stories

1. As a [actor], I want [feature], so that [benefit]
2. As a [actor], I want [feature], so that [benefit]
...

## Implementation Decisions

### Module: [Name]
**Purpose:** [What this module does]
**Interface changes:** [What changes about how callers use it]
**Key decisions:** [Architectural choices made here]

### Schema Changes
**Before:** [current schema if applicable]
**After:** [new schema]

### API Contracts
**Endpoint:** [if applicable]
**Request:** [shape]
**Response:** [shape]

## Testing Decisions

### What Makes a Good Test
- Tests behavior through public interfaces only
- Does not test implementation details
- Would survive internal refactor

### Modules to Test
- [List modules and why each needs tests]

### Prior Art
- [Reference similar tests in codebase]
- [Patterns to follow]

## Out of Scope

- [Explicitly not included]
- [Boundary of what this PRD does NOT cover]

## Further Notes

[Any additional context, risks, open questions]
```

## Writing Good User Stories

### Format
```
As an <actor>, I want <goal>, so that <benefit>
```

### Good Examples
```
As a mobile bank customer, I want to see my balance, so I can make informed spending decisions
As an admin, I want to delete user accounts, so I can comply with GDPR requests
As a developer, I want typed API responses, so I can catch bugs at compile time
```

### Bad Examples
```
As a user, I want the app to work (too vague)
As a user, I want to click the button (implementation detail)
As a user, I want a beautiful UI (not user-centric)
```

## Implementation Decisions Section

Should include:
- Modules built or modified (use domain language)
- Interface changes (not file paths)
- Technical clarifications
- Architectural decisions
- Schema changes (before/after if relevant)
- API contracts

Should NOT include:
- Specific file paths (go stale)
- Code snippets (except decision-critical prototypes)
- Implementation steps (that's the agent's job)

## Testing Decisions Section

Describe:
- What makes a good test for this feature
- Which modules will be tested and why
- Prior art in the codebase to follow