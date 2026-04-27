---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <topic-or-function>
description: "Investigate how something works. Runs code exploration, explains architecture, traces execution flows."
---

# /investigate — Deep code investigation

Thoroughly investigate how a system, module, or function works.

## Usage
```
/investigate intent routing
/investigate how agents are dispatched
/investigate LLM fallback chain
/investigate memory recall flow
```

## Workflow
```
1. Glob/grep to find relevant files
2. Read files to understand structure
3. Trace execution flows
4. Map dependencies and side effects
5. Summarize findings
```

## Investigation Output
```
## WHAT_IT_DOES
<concise description>

## KEY_FILES
- file1.py: 50 lines, does X
- file2.py: 100 lines, does Y

## EXECUTION_FLOW
1. entry → file.function
2. process → file.function
3. exit → result

## DEPENDENCIES
- external: litellm, mem0ai, aiogram
- internal: llm_client, intent_router

## SIDE_EFFECTS
- writes to memory
- calls external API
```

## Swarm-Bot Key Areas to Investigate
- Intent routing: `core/intent_router.py`, `agents.py`
- LLM integration: `llm_client.py`
- Memory: `core/memory/memory_manager.py`
- Handler registration: `handlers/loader.py`
- Agent dispatch: `agents.py`, `core/system_prompt_builder.py`
