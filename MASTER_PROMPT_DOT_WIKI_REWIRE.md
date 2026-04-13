# MASTER PROMPT — FORCE `.wiki` AS SINGLE SOURCE OF TRUTH

Use this prompt exactly in Claude Code / OpenCode / LegionBot sessions.

---

You are operating inside `~/swarm-bot`.

## NON-NEGOTIABLE RULE

From now on, **`.wiki/` is the ONLY knowledge-base path**.

- ✅ Allowed: `.wiki/**`
- ❌ Forbidden: `wiki/**`

Never read from, write to, create, update, or reference `wiki/` in code, docs, prompts, scripts, configs, tests, or commands.

If both folders exist, treat `wiki/` as legacy and migrate everything to `.wiki/`.

---

## PRIMARY OBJECTIVE

Re-route and rewire the entire repository so all wiki operations (read/write/edit/delete/index/lint/compile/query) use `.wiki/` only.

This includes:

1. Python code
2. Shell scripts
3. YAML/JSON/TOML configs
4. Prompt files (`CLAUDE*.md`, `OPENCODE*.md`, `AGENTS.md`, etc.)
5. README/docs/tests
6. CI workflows

---

## EXECUTION PLAN (DO ALL)

### Phase 1 — Inventory and impact map

1. Find all references to `wiki/` and `/wiki` across repo.
2. Categorize each hit as:
   - filesystem path usage
   - documentation text
   - command example
   - test fixture/assertion
   - CI/workflow logic

### Phase 2 — Path rewiring

Replace all active path references from `wiki/` to `.wiki/`.

Rules:

- Replace only true path references; do not corrupt normal words.
- Preserve relative/absolute semantics.
- Keep behavior unchanged besides path root.

### Phase 3 — Legacy migration

If `wiki/` contains files not present in `.wiki/`:

1. Move/mirror required content into `.wiki/`.
2. Do not delete user data silently.
3. If uncertain, keep backup under `.wiki/_migration_backup/`.

### Phase 4 — Guardrails to prevent regressions

Add safeguards so new code cannot drift back to `wiki/`:

1. Add/update constants such as `WIKI_ROOT = Path('.wiki')` where appropriate.
2. Add a lint/check script (or test) that fails on forbidden `wiki/` path usage.
3. Update docs to explicitly state `.wiki/` is canonical.

### Phase 5 — Validation

Run verification commands and fix every failure:

1. `grep -R "\bwiki/" -n . --exclude-dir=.git --exclude-dir=.venv`
2. `grep -R "['\"]/wiki" -n . --exclude-dir=.git --exclude-dir=.venv`
3. project tests/lint relevant to changed files

Success criteria:

- No live path usage points to `wiki/`
- All wiki operations succeed using `.wiki/`
- Docs and prompts consistently reference `.wiki/`

---

## EDITING POLICY

- Make minimal, targeted changes.
- Do not introduce unrelated refactors.
- Preserve async behavior and existing architecture.
- Do not change secrets/env values.

---

## OUTPUT FORMAT (MANDATORY)

At end, output:

1. **Changed files summary** (grouped by code/config/docs/tests)
2. **Key rewires performed**
3. **Validation results** with command outputs
4. **Remaining risks** (if any)
5. **Exact commit message suggestion**

---

## COMMIT MESSAGE TEMPLATE

`refactor(wiki): rewire all wiki operations to .wiki and add anti-regression guards`

---

## HARD STOP CONDITIONS

If any step tries to write to `wiki/`, stop and correct to `.wiki/`.
If unsure between `wiki/` and `.wiki/`, always choose `.wiki/`.
