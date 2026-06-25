---
name: receiving-code-review
description: >-
  How to respond when a reviewer provides feedback on your code.
  Forbidden responses, YAGNI check pattern, and growth mindset protocol.
---

## Forbidden Responses

Do NOT respond with these phrases:

- "You're absolutely right!" — vague agreement without action
- "Great point!" — social padding, not engineering
- "I'll fix that in a follow-up" — deferred action without a ticket
- "That's how the existing code does it" — not a valid defense
- "It works on my machine" — irrelevant

Instead, respond with specific, actionable replies:

- "Fixed in abc123. The issue was X. Here's how I fixed it: Y."
- "I considered X but chose Y because Z. Is there a case I'm missing?"
- "Good catch. Added a test for that edge case."

## YAGNI Check Pattern

When a reviewer suggests adding something, first check:

1. Does the current code have a concrete bug without this?
2. Is this handling a scenario that will realistically occur?
3. Is this adding an abstraction for a single use case?

If all three are "no", push back: "This seems like a YAGNI case. The current code handles the known cases. Let's add this when we see the need."

## Growth Mindset

- Every review comment is an opportunity to learn the codebase better
- If you don't understand a comment, ask for clarification
- If you disagree, explain your reasoning with specifics
- Thank reviewers for catching issues (once, at the end — not after every comment)

## Follow-Up

- After fixing all issues, re-run `make check`
- Run `gitnexus_detect_changes()` to verify final scope
- Update the review artifact if one exists
