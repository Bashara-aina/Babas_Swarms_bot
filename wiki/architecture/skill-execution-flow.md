---
title: skill-execution-flow
type: architecture
status: active
tags: [skills, execution, flow, registry]
created: 2026-04-13
updated: 2026-04-13
summary: Skills are triggered by intent router, executed via skill registry with optional tool calls, and results injected into LLM context.
wikilinks: [[concepts/skill-registry.md], [architecture/legion-module-map.md]]
confidence: high
source: implementation
---

# Skill Execution Flow

## TL;DR
Skills flow from intent detection → registry lookup → execution → result injection into LLM context.

## Execution Flow

```
[User Message]
    → [intent_router.classify()]
    → [Intent: skill_name] (confidence ≥ 0.7)
    → [skill_registry.get(skill_name)]
    → [execute_skill(skill, context)]
    → [Result injected into LLM]
    → [LLM generates response]
```

## Skill Registry Structure

```python
SKILL_REGISTRY = {
    "skill_name": {
        "triggers": ["trigger phrase", "another"],
        "handler": async_skill_function,
        "needs": ["API_KEY_NAME"],
        "timeout": 30,
        "fallback": "Error message"
    }
}
```

## Execution Example

For "cek seo rumahlabuh":

1. Intent router detects: `web_audit` intent
2. Skill registry locates: `web_audit` skill
3. Checks: `Google PageSpeed API` available?
4. Executes: `web_audit_skill(legion, context)`
5. Result: PageSpeed score injected into context
6. LLM generates response with score

## Error Handling

- **Missing API key**: Return fallback message
- **Timeout**: Cancel and return partial results
- **Exception**: Log and return error message

## Related Pages

- [[concepts/skill-registry.md]] — Registry concept
- [[architecture/legion-module-map.md]] — Module overview
