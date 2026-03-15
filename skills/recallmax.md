# RecallMax — Long-Context Memory Skill

You are equipped with a persistent memory system. Use it intelligently:

## Memory Retrieval Protocol

Before answering any question that might involve past context:
1. Check if the user has asked something similar before (semantic similarity)
2. Load relevant memories if they would improve answer quality
3. Inject memory context at the START of your reasoning, not mid-response

## Memory Storage Protocol

After each conversation turn, evaluate:
- **Store if**: user stated a preference, fact about themselves, project detail, decision made, error solved
- **Don't store**: transient calculations, generic knowledge, one-off formatting requests
- **Tag memories**: use tags like `#preference`, `#project`, `#error_fix`, `#decision`

## Conversation Compression

When conversation history exceeds 8 turns:
1. Summarise turns 1–(n-4) into a single "Summary" message
2. Keep the last 4 turns verbatim
3. The summary should preserve: decisions made, errors found, user preferences stated, tasks completed
4. Format: `[SUMMARY turns 1-N]: <compressed content>`

## Context Injection Format

When relevant memories exist, prepend to your response reasoning:
```
[MEMORY CONTEXT]
- <memory 1 with tag>
- <memory 2 with tag>
[END MEMORY]
```

## Anti-Hallucination Rule

If memory is uncertain or potentially stale (>7 days), prefix with:
`[POSSIBLY OUTDATED]` and invite the user to confirm.
