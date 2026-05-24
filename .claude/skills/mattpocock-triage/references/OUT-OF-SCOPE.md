# Out of Scope

## Purpose

The `.out-of-scope/` directory tracks enhancement requests that have been considered and deliberately not actioned. This prevents:
- Repeated discussions about the same rejected ideas
- "Why was this closed?" confusion
- Wheel-spinning on already-considered proposals

## When to Add to Out-of-Scope

Add to `.out-of-scope/` when:
- Enhancement was deliberately rejected after discussion
- Feature doesn't align with project direction
- Request is too vague to implement but couldn't be clarified
- Similar request was previously rejected

## Structure

```
.out-of-scope/
├── README.md           # Index of all out-of-scope items
└── YYYY-MM-DD-slug.md  # Individual rejection docs
```

## Individual File Template

```markdown
# Out of Scope: [Brief Title]

**Date:** YYYY-MM-DD
**Issue:** #[number]

**Summary:**
[Brief description of what was requested]

**Reason for rejection:**
[Why this won't be implemented]

**Alternative suggestions:**
[Any workarounds or related features that ARE supported]
```

## Example

```markdown
# Out of Scope: Dark mode for CLI output

**Date:** 2024-01-15
**Issue:** #89

**Summary:**
User requested ANSI dark theme for CLI output.

**Reason for rejection:**
CLI tools should output plain text by default for maximum compatibility with pipes and scripts. Color support is available via `--color` flag when needed.

**Alternative suggestions:**
- Use `--color` flag to enable colors when needed
- Configure terminal emulator colors separately
```

## Managing the Directory

1. When closing as `wontfix` (enhancement), create the doc
2. Link to it from the issue comment before closing
3. Update `.out-of-scope/README.md` index

## README.md Template

```markdown
# Out of Scope

Enhancements deliberately rejected after consideration.

| Date | Issue | Summary |
|------|-------|---------|
| YYYY-MM-DD | #XX | Brief description |
```