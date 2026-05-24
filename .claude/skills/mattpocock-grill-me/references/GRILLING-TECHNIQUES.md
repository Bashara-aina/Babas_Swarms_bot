# Grilling Techniques

How to conduct an effective grilling session.

## Principles

1. **One question at a time** — don't overwhelm with a list
2. **Wait for answer before continuing** — let them think
3. **Provide your recommendation** — help them decide
4. **Explore codebase when possible** — verify claims against code

## Question Types

### Clarifying Questions
"What do you mean by X?" — clarify fuzzy terms
"How does Y work currently?" — establish baseline

### Challenge Questions
"What if Z fails?" — test edge cases
"How does this scale to N users?" — probe assumptions
"What are the failure modes?" — identify risks

### Dependency Questions
"Does X depend on Y being ready first?"
"What's the order of operations?"
"What can be done in parallel?"

### Trade-off Questions
"What are you trading off by choosing X over Y?"
"Cost of being wrong on this?"
"Time vs quality tradeoff?"

## Decision Tree Walking

```
Start: User presents plan
  ↓
Clarify: What problem does this solve?
  ↓
Scope: What's in/out?
  ↓
Dependencies: What must happen first?
  ↓
Approach: How does this work?
  ↓
Edge cases: What could go wrong?
  ↓
Trade-offs: What are you accepting/rejecting?
  ↓
Verification: How do we know it worked?
  ↓
Shared understanding reached? → Done
                                       ↓ (if not)
Return to most unclear branch
```

## Good Follow-up Questions

- "Can you walk me through the flow?"
- "What does success look like?"
- "What's the simplest version that proves the concept?"
- "What would have to be true for this to fail?"
- "How does this interact with [related system]?"

## Probing Edge Cases

```
"What if the user does X?"
"What if the network fails during Y?"
"What if the data is malformed?"
"What if load increases 100x?"
"What if someone tries to use this for Z (misuse case)?"
```

## When You Disagree

1. State the disagreement clearly
2. Explain your reasoning
3. Ask if they see it differently
4. Offer ADR if it's a hard-to-reverse decision