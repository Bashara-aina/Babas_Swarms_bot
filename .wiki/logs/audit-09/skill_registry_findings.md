---
title: Skill Registry Findings
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '> Generated: 2026-04-12'
wikilinks: []
confidence: medium
source: research
---
# SkillRegistry Audit — LEGION AUDIT 09
> Generated: 2026-04-12

## File: `core/skills/registry.py`

### Skill Dataclass Fields

```python
@dataclass
class Skill:
    name: str
    description: str
    trigger_keywords: list[str]
    handler: Callable
    required_env_keys: list[str] = field(default_factory=list)
    category: str = "general"
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `name` | `str` | required | Skill identifier |
| `description` | `str` | required | Human-readable description |
| `trigger_keywords` | `list[str]` | required | Keywords for matching |
| `handler` | `Callable` | required | Callable handler |
| `required_env_keys` | `list[str]` | `field(default_factory=list)` | Env vars needed |
| `category` | `str` | `"general"` | Skill category |

### SkillRegistry Methods

| Method | Signature | Notes |
|--------|-----------|-------|
| `register` | `(skill: Skill) -> None` | Registers skill by name |
| `find_by_example` | `(text: str) -> Skill \| None` | **Keyword scoring** — counts keyword matches |
| `list_all` | `() -> list[Skill]` | Returns all registered skills |
| `describe_for_prompt` | `() -> str` | Formats skills for LLM prompt |

### `find_by_example()` Keyword Scoring Logic

```python
def find_by_example(self, text: str) -> Skill | None:
    text_lower = text.lower()
    best: tuple[float, Skill | None] = (0.0, None)
    for skill in self._skills.values():
        score = sum(1 for kw in skill.trigger_keywords if kw.lower() in text_lower)
        if score > best[0]:
            best = (score, skill)
    return best[1]
```

- **Scoring**: Simple keyword presence count (each keyword match = 1 point)
- **Selection**: Returns skill with highest score, ties broken by insertion order
- **Issue**: No normalization, no weighting, pure unweighted count

### Module-Level Singleton

```python
SKILL_REGISTRY = SkillRegistry()
get_skill_registry = lambda: SKILL_REGISTRY
```

## Verdict

- ✅ Skill dataclass has all required fields
- ✅ `find_by_example()` implements keyword scoring (simple unweighted count)
- ⚠️ No `_register_*_skills()` functions found in this file (only `register()` method)
