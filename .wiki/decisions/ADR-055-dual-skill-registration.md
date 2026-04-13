---
## Context

---
During LEGION AUDIT 09 (Skills Layer & Skill Registry), a **dual skill registration architecture** was discovered. Two separate, disconnected systems handle skill registration in the codebase:

### System 1: `core/skills/registry.py` — Python Class-Based Registry

```python
# core/skills/registry.py
@dataclass
class Skill:
    name: str
    description: str
    trigger_keywords: list[str]
    handler: Callable
    required_env_keys: list[str] = field(default_factory=list)
    category: str = "general"

class SkillRegistry:
    def register(self, skill: Skill) -> None: ...
    def find_by_example(self, text: str) -> Skill | None: ...  # keyword scoring
    def list_all(self) -> list[Skill]: ...
    def describe_for_prompt(self) -> str: ...

SKILL_REGISTRY = SkillRegistry()
```

- **Purpose:** Programmatic skill lookup with keyword-based matching
- **How it works:** Skills are registered manually via `registry.register(Skill(...))` calls; `find_by_example()` scores keywords for matching
- **Scope:** `core/skills/` directory only (3 builtin skills)

### System 2: `core/skill_registry.py` — JSON Manifest Loader

```python
# core/skill_registry.py
_MANIFEST = Path(__file__).resolve().parent.parent / "skills" / "manifest.json"
_CONFIG = Path(__file__).resolve().parent.parent / "config" / "legion_skills.json"

def load_skills() -> list[dict[str, Any]]:
    # Loads skills/manifest.json first (primary)
    # Then additive merge from config/legion_skills.json (legacy)
    ...

def skills_prompt_block_for_query(user_message: str = "") -> str:
    # Builds LLM prompt with [AUTONOMOUS ROUTES] + [REGISTERED SKILLS]
    ...

def get_skill(name: str) -> dict[str, Any] | None:
    # Lookup by name or id
    ...
```

- **Purpose:** Dynamic skill discovery from JSON manifests for LLM context
- **How it works:** Loads `skills/manifest.json` (6 skills) and `config/legion_skills.json` (3 legacy additions)
- **Scope:** Global skill registry including external tools (`screenpipe_recall`, `mirofish_simulation`, `open_interpreter`)
---


## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         SKILL LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  core/skills/registry.py              core/skill_registry.py   │
│  ┌─────────────────────────┐          ┌───────────────────────┐│
│  │   SkillRegistry          │          │   JSON Manifest       ││
│  │   (Python class)         │          │   Loader              ││
│  │                          │          │                       ││
│  │ - Skill dataclass        │          │ - load_skills()       ││
│  │ - register()             │          │ - manifest.json       ││
│  │ - find_by_example()      │          │ - legion_skills.json  ││
│  │ - list_all()             │          │ - skills_prompt_block ││
│  └─────────────────────────┘          └───────────────────────┘│
│              │                                   │             │
│              ▼                                   ▼             │
│  Used for programmatic              Used for building LLM       │
│  skill lookup + handler             prompt context blocks      │
│  invocation                          + autonomous routing      │
│                                                                 │
│  ❌ NOT CONNECTED — Different purposes, no shared data          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Problem

These two systems are **completely disconnected**:

1. **`core/skills/registry.py`** is a standalone Python registry that is never populated from the JSON manifests
2. **`core/skill_registry.py`** loads JSON files but has no connection to the `SkillRegistry` class
3. **`find_by_example()`** in `core/skills/registry.py` is defined but not used by the JSON manifest path
4. The manifest and `SKILL_PATTERNS` use **different naming conventions**:
   - Manifest: Python class names (`WebSearch`, `GeoIntelligence`, `DatabaseAgent`)
   - SKILL_PATTERNS: Lowercase action names (`location`, `business`, `simulation`)

### Observed Symptoms

| Issue | Manifest Handler | SKILL_PATTERNS Handler | Match? |
|-------|------------------|-------------------------|--------|
| `web_search` | `WebSearch` | `deep_research` → `/research` | ❌ |
| `geo_intelligence` | `GeoIntelligence` | `location_advice` → `location` | ❌ |
| `database_agent` | `DatabaseAgent` | `business_query` → `business` | ❌ |
| `mirofish_simulation` | `mirofish` | `strategic_simulation` → `simulation` | ❌ |
| `screenpipe_recall` | `screenpipe_tool` | *(none)* | ❌ |
| `open_interpreter` | `interpreter_tool` | *(none)* | ❌ |

---

## Options

### Option A: Deprecate `core/skills/registry.py` Class System

**Action:** Remove or deprecate `core/skills/registry.py` entirely; standardize on JSON manifest approach.

**Pros:**
- Single source of truth for skill definitions
- Easier to add/remove skills without code changes
- Consistent with `core/skill_registry.py` philosophy

**Cons:**
- `find_by_example()` keyword scoring is lost
- Class-based registration may have been used elsewhere

### Option B: Wire `core/skills/registry.py` to JSON Manifests

**Action:** Populate `SkillRegistry` at startup from `load_skills()` output.

**Pros:**
- Preserves programmatic lookup capability
- Keeps `find_by_example()` for cases where JSON isn't available

**Cons:**
- Adds complexity; two systems still exist
- Potential sync issues between class registry and JSON

### Option C: Keep Both, Document Separation

**Action:** Accept the duality; document that `core/skills/registry.py` is for internal programmatic use while `core/skill_registry.py` is for LLM prompts.

**Pros:**
- No refactoring required
- Each system serves a clear purpose

**Cons:**
- Confusing architecture
- Maintenance burden doubles
- Risk of divergence over time

---

## Decision

**Option C — Keep Both, Document Separation**

The two systems serve distinct purposes:
- `core/skills/registry.py` is for **programmatic skill lookup and handler invocation** (internal use)
- `core/skill_registry.py` is for **building LLM prompt context** (external-facing)

They should remain separate but clearly documented.

### Required Actions

1. **Document** the distinction in `core/skills/registry.py` docstring
2. **Add integration note** in `core/skill_registry.py` that it does NOT use `SkillRegistry` class
3. **Wire manifest skills to SKILL_PATTERNS** by adding entries for `web_search`, `screenpipe_recall`, `open_interpreter`
4. **Standardize handler naming** in `SKILL_PATTERNS` or add alias mapping so manifest handlers can resolve to SKILL_PATTERNS keys

---

## Consequences

- **Documentation improvement** — clearer role separation
- **No immediate code change** — systems already work independently
- **Future wiring work** — SKILL_PATTERNS manifest integration needed (P1)

---

## References

- Audit file: `.wiki/logs/audit-09/skill_registry_duality.md`
- Manifest: `skills/manifest.json`
- Legacy config: `config/legion_skills.json`
- SKILL_PATTERNS: `core/autonomous_router.py`
- Class registry: `core/skills/registry.py`
- Manifest loader: `core/skill_registry.py`

---

*ADR created by Reviewer Agent — LEGION AUDIT 09*
