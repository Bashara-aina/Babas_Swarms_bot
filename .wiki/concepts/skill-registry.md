---
title: skill-registry
type: concept
status: active
tags: [skills, registry, capabilities, agents, trigger]
created: 2026-04-13
updated: 2026-04-13
summary: The skill registry is a centralized capability catalog mapping trigger phrases to handler implementations, enabling Legion to扩展 capabilities without modifying core routing logic.
wikilinks:
  - [[intent-routing]]
  - [[./concepts/reasoning-loop]]
  - [[skill-execution-flow]]
  - [[./concepts/self-improvement-loop]]
confidence: high
source: implementation
---

# Skill Registry

## TL;DR
The skill registry is a central catalog of discrete Legion capabilities — web search, code review, memory recall, system health checks — where each skill defines its trigger phrases, handler function, required environment variables, and fallback behavior. Skills are discovered at runtime and can be added without touching core routing code.

## Overview

As Legion gains capabilities, hard-coding every new feature into the intent router becomes unsustainable. The skill registry solves this by making capabilities first-class, self-describing units. A new skill can be registered with a name, description, trigger keywords, and a handler — and is immediately available to the intent router and skill execution flow without any changes to routing logic.

## Context

Legion needs to handle an expanding set of user requests: "cek seo rumahlabuh", "gpu lagi training ga", "restart legion". Each of these maps to a different skill with different requirements (API keys, system access, external services). The registry provides a uniform interface so adding a new capability is a matter of writing the handler and registering it — not refactoring the intent classifier.

## Key Properties

- **Trigger-based discovery**: Skills are matched against user messages by keyword overlap, not intent classification
- **Runtime registration**: Skills can be added between sessions without restarting the bot
- **Fallback safety**: Each skill defines a graceful error message if it fails or missing dependencies
- **Category organization**: Skills are grouped A–H (Web, Search, Code, System, Memory, Utility, Status, Media)
- **Environment variable awareness**: Skills declare required env keys; missing keys trigger graceful degradation
- **Intent router integration**: Low-confidence intent cases fall through to skill registry as a secondary matching layer
- **Described for prompts**: `describe_for_prompt()` generates a readable capability list for system prompt injection

## How It Works

### Skill Data Structure
```python
@dataclass
class Skill:
    name: str                           # unique identifier
    description: str                    # human-readable description
    trigger_keywords: list[str]          # phrases that may trigger this skill
    handler: Callable                   # async function executing the skill
    required_env_keys: list[str]         # env vars needed; empty = no deps
    category: str = "general"            # grouping for describe_for_prompt
```

### Registration
`SKILL_REGISTRY.register(skill)` adds the skill to the registry dictionary keyed by name. Registration happens at module import time via `core/skills/__init__.py` which imports all builtin skill modules.

### Discovery (`find_by_example`)
Given a user message, `find_by_example()` lowercases the message and scores each registered skill by how many of its trigger keywords appear in the message. Returns the highest-scoring skill above a minimum threshold, or None if nothing beats the floor.

### Execution Flow
When a skill is matched, the handler is called with the original message and any extracted parameters. The handler is responsible for all tool invocations, LLM calls, and external API usage. Errors are caught and converted to the skill's defined fallback message.

### Skill Categories (30 skills defined in LEGION_MASTER.md)

| Category | Count | Examples |
|----------|-------|----------|
| A: Web | 4 | web_audit, url_check, web_scrape |
| B: Search | 5 | web_search, arxiv_search, summarize_url, hacker_news, video_url |
| C: Code | 3 | github_pr_status, github_commit_log, code_review |
| D: System | 4 | system_health, service_status, service_restart, run_shell |
| E: Memory | 3 | remember, recall, obsidian_write |
| F: Utility | 3 | weather, translate, timer |
| G: Status | 5 | rumahlabuh_status, thesis_status, cekwajar_status, gpu_training_status, adb_scholarship |
| H: Media | 3 | screenshot, analyze_screen, screen_text |

## Relationships

The skill registry is the capability layer that sits above intent routing. [[intent-routing]] uses the registry as a fallback when pattern matching and LLM classification both fail to reach 0.50 confidence — so skills effectively extend the routing vocabulary without modifying the intent classifier. Skills use [[./concepts/reasoning-loop]] internally: complex skills like `web_search` and `arxiv_search` run through plan → execute → observe phases. The execution flow is detailed in [[skill-execution-flow]]. When skills succeed or fail, [[./concepts/self-improvement-loop]] records the outcome so future skill selections are better calibrated.

## Current Status

**Partially implemented.** The `SkillRegistry` class and `Skill` dataclass exist in `core/skills/registry.py`. Runtime registration via `__init__.py` is defined. `find_by_example()` is implemented. Builtin skill handlers exist in `core/skills/builtin/`. Skill registration in intent router is wired. The full 30-skill roster from LEGION_MASTER.md Phase 2 is not yet fully populated — this is ongoing work.

## See Also

- [[intent-routing]] — Intent router fallback to skill registry
- [[skill-execution-flow]] — How skills execute in detail
- [[./concepts/self-improvement-loop]] — Learning from skill outcomes
