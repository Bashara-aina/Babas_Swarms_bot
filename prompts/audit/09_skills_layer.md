# AUDIT 09 — Skills Layer & Skill Registry
> Paste this entire prompt into a new OpenCode session.
> Goal: every skill in skills/ is registered, has the right interface, and is triggerable.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 09 — Skills Layer & Skill Registry                ║
║  Fix: every skill registered, callable, and triggered by intent ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — LIST ALL SKILLS
List every file/directory in skills/.

STEP 2 — SKILL INTERFACE AUDIT
For each skill file, verify it has the expected interface.
Expected pattern (class-based):
  class XxxSkill:
      name = "xxx"
      description = "..."
      async def execute(self, args: dict, context: dict) -> str:
          ...

OR function-based:
  async def execute(args: dict, context: dict) -> str:
      ...

If a skill does not match: refactor it to match the interface.
This is required for skill_registry to load it.

STEP 3 — SKILL REGISTRY AUDIT
Read core/skill_registry.py.
Verify it has auto-discovery (scans skills/ directory) OR manual registration.
Build a list: which skills does the registry currently know about?
Compare with Step 1 list.
For any skill NOT in registry: add it:
  registry.register(XxxSkill())

STEP 4 — INTENT MAPPING AUDIT
For each registered skill: what user message or intent triggers it?
Check intent_router.py and autonomous_router.py for mappings.
For any skill with NO intent mapping:
  Either add the intent case:
    elif "search" in intent: return skill_registry.get("search").execute(args)
  Or mark it as an internal/utility skill (not user-facing) with a comment.

STEP 5 — SEARCH SKILL SPECIAL CHECK
Find the web search skill (likely skills/search.py or skills/web_search.py).
Verify execute() actually returns results as a string or list of dicts.
Verify it's not silently catching and swallowing errors.
Verify it has a timeout (8 seconds max).

STEP 6 — NIHONGO SKILL SPECIAL CHECK
Find any nihongo-related skill or module in skills/nihongo/.
Verify SenseiSoul or equivalent is importable.
Verify it connects to the nihongo handler in handlers/.

STEP 7 — VERIFY
Run: python -c "from core.skill_registry import SkillRegistry; r = SkillRegistry(); r.load_all(); print(r.list_skills())"
Fix any error.
Confirm all expected skills appear in the output list.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
