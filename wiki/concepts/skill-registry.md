---
title: skill-registry
type: concept
status: active
tags: [skills, registry, capabilities, agents]
created: 2026-04-13
updated: 2026-04-13
summary: The skill registry is a centralized catalog of Legion's capabilities, each skill having defined triggers, implementations, and fallback behaviors.
wikilinks: [[concepts/intent-routing.md]], [[concepts/skill-registry.md]], [[architecture/skill-execution-flow.md]]
confidence: high
source: implementation
---

# Skill Registry

## TL;DR
Skills are discrete capabilities (web search, code review, memory recall) registered in a central registry that maps trigger patterns to implementations.

## Skill Categories

| Category | Count | Examples |
|----------|-------|----------|
| A: Web | 4 | web_audit, url_check, web_scrape |
| B: Search | 5 | web_search, arxiv_search, summarize_url |
| C: Code | 3 | github_pr_status, code_review |
| D: System | 4 | system_health, service_restart |
| E: Memory | 3 | remember, recall, obsidian_write |
| F: Utility | 3 | weather, translate, timer |
| G: Status | 5 | rumahlabuh_status, gpu_training_status |
| H: Media | 3 | screenshot, analyze_screen |

## Registry Structure

```python
SKILL_REGISTRY = {
    "web_audit": {
        "triggers": ["cek seo", "pagespeed", "audit website"],
        "impl": web_audit_skill,
        "needs": ["Google PageSpeed API"],
        "fallback": " graceful error message"
    },
    # ...
}
```

## Related Pages

- [[architecture/skill-execution-flow.md]] — How skills execute
- [[concepts/intent-routing.md]] — How skills are triggered
