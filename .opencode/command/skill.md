---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: [command-name]
description: "Create or update a skill. Generates skill markdown from code inspection. Without args: list skills."
---

# /skill — Skill creation and management

Create or update OpenCode skills based on code inspection.

## Usage
```
/skill
/skill browser_agent
/skill create "My Custom Skill" --based-on explorer
```

## What /skill does
1. Scans codebase for skill-related code
2. Generates skill markdown (SKILL.md)
3. Saves to `.opencode/skills/` or `.claude/skills/`
4. Updates index

## Skill Locations
| Type | Location | Use |
|------|----------|-----|
| OpenCode skills | .opencode/skills/ | OpenCode-specific |
| Claude skills | .claude/skills/ | Shared Claude/OpenCode |
| Legacy skills | .claude/skills/generated/ | Auto-generated |

## Skill Template
```markdown
---
name: <skill-name>
description: "When to use this skill..."
---

# <Skill Name>

## Overview
## Tools Used
## Workflow
## Swarm-Bot Context
## Examples
```

## Swarm-Bot Existing Skills
- Browser automation: tools/browser_agent.py
- LLM integration: llm_client.py
- Memory: core/memory/memory_manager.py
- Intent routing: core/intent_router.py

## Constraints
- Skills go in `.claude/skills/` (shared) not `.opencode/skills/`
- Must include description and examples
- Should be project-specific
