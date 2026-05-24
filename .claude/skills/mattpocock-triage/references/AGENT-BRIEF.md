# Agent Brief Template

Use this structure when posting a `ready-for-agent` issue:

```markdown
## Agent Brief

**Issue:** #[number] [title]

**Goal:** [What the agent should accomplish]

**Context:**
- [Relevant background from triage]
- [Links to related docs, ADRs, or code]

**What to do:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Constraints:**
- [What NOT to do or change]
- [Boundaries of the task]

**Verification:**
- [How to verify the solution works]
- [Any tests that should pass]

**Success criteria:**
- [Observable outcome that proves the task is complete]
```

## Tips for Writing Good Agent Briefs

1. **One goal per brief** — if it's complex, split into multiple issues
2. **Be specific about scope** — what shouldn't the agent touch?
3. **Provide context** — links to relevant code, docs, prior discussions
4. **Define success clearly** — how does the agent know they're done?

## Example

```markdown
## Agent Brief

**Issue:** #42 Add rate limiting to API endpoints

**Goal:** Implement rate limiting for all public API endpoints

**Context:**
- Related to security concern in #38
- See `docs/rate-limiting.md` for design
- Backend uses Express, see `src/api/` for routes

**What to do:**
1. Add rate limiting middleware to `src/api/routes.ts`
2. Use in-memory store for demo (can be swapped for Redis later)
3. Limit: 100 requests/minute per IP

**Constraints:**
- Don't modify database schema
- Don't add new dependencies
- Keep it simple — this is a v1

**Verification:**
- `curl` to endpoint should return 429 after 100 requests
- `pnpm test` should pass

**Success criteria:**
- Rate limiting applied to all `/api/*` routes
- Returns 429 with `Retry-After` header when exceeded
```