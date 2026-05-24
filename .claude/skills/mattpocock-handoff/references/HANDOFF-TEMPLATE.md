# Handoff Document Template

Template for creating effective handoff documents.

## When to Use

- End of session before closing
- Handing off to another agent
- Saving work-in-progress
- Breaking long conversations

## Template

```markdown
# Handoff: [Brief Description]

**Date:** YYYY-MM-DD
**Session:** [session-id or context]

## What Was Done

- [Accomplishment 1]
- [Accomplishment 2]
- [Key decision made]

## Current State

- What's working:
- What's not working:
- Known issues:

## Next Steps

### Immediate (Do First)
1. [Step 1]
2. [Step 2]

### Later (Can Wait)
- [Future work]

## Key Context

### Files Modified
- `path/to/file1`
- `path/to/file2`

### Decisions Made
- [Decision 1] — because [reason]
- [Decision 2] — because [reason]

### Skills to Use
- `skill-name` — for [reason]

## Questions for Next Session

- [Question 1]
- [Question 2]

## Notes for Future Claude

[Any tribal knowledge, gotchas, things to remember]
```

## Anti-Patterns

### Bad Handoff
```markdown
Did some work on the auth module. Made progress. More to do later.
```

### Good Handoff
```markdown
# Handoff: Auth Module - OAuth Integration

## Done
- Added OAuth2 callback handler in `src/auth/oauth.ts`
- Integrated with Google and GitHub providers
- Added `User.oauthProviders` field to schema

## Next
1. Add token refresh logic
2. Implement logout endpoint
3. Write integration tests

## Context
- OAuth tokens expire in 1 hour — refresh logic needed
- Uses `lucia` library (see `src/auth/lucia-setup.ts`)
- Existing session handling in `src/auth/session.ts`

## Skills
Use `mattpocock-tdd` when implementing token refresh
```

## Tips

1. **Be specific** — "Fixed bug in checkout" vs "Fixed null pointer in `Order.calculateTax()` when cart is empty"
2. **Include paths** — files, modules, functions
3. **Name the next action** — what should the next session do first?
4. **Suggest skills** — what skill fits this work?