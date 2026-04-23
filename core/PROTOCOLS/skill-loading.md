# Skill Loading Protocol

**MANDATORY AT TASK START** — Always declare skill tiers.

## Tier Discipline

```python
from core.skills.harness import load_skills_for_task, format_skill_declaration

skills = load_skills_for_task("feature", "cekwajar")
declaration = format_skill_declaration("feature", "cekwajar")
# Output: "Loading skills: typescript-strict, next-js-app-router, indonesian-market, ... for feature/cekwajar"
```

## Tier Definitions

| Tier | Always/By | Types |
|------|-----------|-------|
| **TIER 1** | Always | `next-js-app-router`, `typescript-strict` |
| **TIER 2** | By type | `supabase-realtime`, `stripe-integration`, `recharts-dataviz` |
| **TIER 3** | By domain | `indonesian-market`, `property-valuation`, `salary-benchmark` |
| **TIER 4** | By quality | `security-audit`, `a11y-compliance`, `conventional-commits` |

## Usage

Load skills appropriate to the task type and domain:

```python
# Feature task in Indonesian domain
skills = load_skills_for_task("feature", "cekwajar")
# → loads: typescript-strict, next-js-app-router, indonesian-market, property-valuation, salary-benchmark

# Bug fix in security-sensitive area
skills = load_skills_for_task("fix", "auth")
# → loads: typescript-strict, security-audit

# Research task
skills = load_skills_for_task("research", "market")
# → loads: indonesian-market, conventional-commits
```