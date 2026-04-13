---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/audit-09/skill_registry_duality.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.679556"
}
---

# Skill Registry Duality Audit — LEGION AUDIT 09
> Generated: 2026-04-12

## Finding: Dual Skill Registration Architecture

There are **TWO separate skill registration systems** in the codebase:

### System 1: `core/skills/registry.py` — `SkillRegistry` Class

| Aspect | Details |
|--------|---------|
| Type | Python class-based registry |
| Dataclass | `Skill` with fields: name, description, trigger_keywords, handler, required_env_keys, category |
| Registration | Manual via `registry.register(Skill(...))` calls |
| Lookup | `find_by_example(text)` — keyword scoring |
| Scope | Used for programmatic skill lookup and LLM prompt building |
| Singleton | `SKILL_REGISTRY = SkillRegistry()` |

### System 2: `core/skill_registry.py` — JSON Manifest Loader

| Aspect | Details |
|--------|---------|
| Type | JSON file loader + prompt builder |
| Files loaded | `skills/manifest.json` + `config/legion_skills.json` |
| Merge strategy | **Additive** — manifest first, then legacy config (deduped by id/name) |
| Output | List of dicts, used for building LLM prompt blocks |
| Functions | `load_skills()`, `_score_routes_for_query()`, `_autonomous_routes_block_for_query()`, `skills_prompt_block_for_query()` |

## JSON Manifest Loading (`load_skills()`)

```python
def load_skills() -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    # Primary: skills/manifest.json
    if _MANIFEST.exists():
        data = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        skills.extend(data.get("skills", []))
    # Additive: config/legion_skills.json (legacy)
    if _CONFIG.exists():
        existing_ids = {sk.get("id") or sk.get("name") for sk in skills}
        for item in s:
            if (item.get("id") or item.get("name")) not in existing_ids:
                skills.append(item)
```

## Additive Merge Logic

1. Load `skills/manifest.json` first (primary)
2. Load `config/legion_skills.json` second (legacy additive)
3. Deduplicate by `id` or `name` — items from legacy config only added if not already present

## `skills_prompt_block_for_query()` Usage

```python
def skills_prompt_block_for_query(user_message: str = "") -> str:
    skills = load_skills()
    auto = _autonomous_routes_block_for_query(user_message)  # From autonomous_router
    # Builds prompt with [AUTONOMOUS ROUTES] + [REGISTERED SKILLS]
```

## Dual System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    SKILL LAYER                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  core/skills/registry.py          core/skill_registry.py
│  ┌─────────────────────┐          ┌─────────────────────┐│
│  │   SkillRegistry     │          │   JSON Manifest    ││
│  │   (Python class)    │          │   Loader           ││
│  │                     │          │                    ││
│  │ - Skill dataclass   │          │ - load_skills()    ││
│  │ - register()        │          │ - manifest.json    ││
│  │ - find_by_example() │          │ - legion_skills.json│
│  │ - list_all()        │          │ - skills_prompt_block│
│  └─────────────────────┘          └─────────────────────┘│
│           │                                │            │
│           ▼                                ▼            │
│  Used for programmatic          Used for building       │
│  skill lookup + handler        LLM prompt context       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Issues Found

1. **No connection** between the two systems — `SkillRegistry` class is NOT populated from `load_skills()` manifest
2. **`core/skills/registry.py`** appears to be a separate, older system not connected to the JSON manifest flow
3. **`find_by_example()`** is defined but not clearly used in the JSON manifest path

## Verdict

⚠️ **Architecture inconsistency** — Two systems exist that appear to serve similar purposes but are not integrated. The `SkillRegistry` class with `find_by_example()` is a standalone Python registry, while `core/skill_registry.py` loads JSON manifests for LLM prompts. These are NOT the same system.
