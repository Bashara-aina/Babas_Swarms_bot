## Review: MCP Cross-Editor Configuration Audit
Date: 2026-04-22
Reviewer: @reviewer
Loop: #1 (first review)

### Independent Verification

**Files found:**
```
.wiki/logs/mcp-audit/git-audit-findings.md
.wiki/logs/mcp-audit/exa-audit-findings.md
.wiki/logs/mcp-audit/obsidian-audit-findings.md
.wiki/logs/mcp-audit/firecrawl-audit-findings.md
.wiki/logs/mcp-audit/filesystem-gitnexus-audit-findings.md
```

**git status:** 1342 files changed (massive diff — large purge of archived/stale wiki content + many .py/.ts/.tsx changes). Multiple untracked files. No blockers flagged in git status itself.

**Key configs read:**
- `config/mcp_config.json` — 26 lines, JSON valid, `enabled: false` for filesystem/obsidian, `enabled: true` for gitnexus only
- `.opencode/opencode.json` — 42 lines, defines 6 servers (gitnexus, obsidian, git, filesystem, firecrawl, exa)
- `.vscode/mcp.json` — 59 lines, defines same 6 servers, same vault paths

---

### ✅ Passed

- **Firecrawl** — API key `fc-09da51dd5e5c46b5b73d7b1ca5cb4c74` consistent across both opencode.json and mcp.json ✅
- **Filesystem** — Both configs use `/home/newadmin` (note: opencode watcher ignores `.wiki/templates/**` etc.) ✅
- **GitNexus** — Both use `pnpm dlx --allow-build=kuzu gitnexus@1.4.0 mcp` ✅
- **All 5 finding files written** to `.wiki/logs/mcp-audit/` with evidence-backed conclusions ✅
- **JSON configs syntactically valid** (verified with `python -c "import json"`) ✅

---

### ⚠️ Warnings (non-blocking)

1. **Obsidian `config/mcp_config.json` stale** — still points to `@modelcontextprotocol/server-obsidian` (wrong package) with `enabled: false`. This is benign since it's disabled, but it is stale and could confuse future debugging.

2. **Filesystem root discrepancy noted** — opencode.json passes `/home/newadmin` while opencode's filesystem watcher (line 17) also uses `/home/newadmin`. VS Code config uses same. Minor point but the audit finding file correctly notes this.

3. **Exa API key mismatch in findings vs. actual config** — The exa findings file shows OpenCode remote URL with embedded API key `2f2f6644-9907-4444-bb6b-c507b32c4820` and VS Code local with env var. The audit findings correctly describe the remote vs. local architecture difference (legitimate design choice, not a bug).

4. **Git MCP server duplicate** — Two different packages (`@mseep/git-mcp-server` vs `@modelcontextprotocol/server-git`) across editors. This is a known design choice (different editors, different toolchains). Findings accurately describe this.

5. **Massive uncommitted diff** — 1342 files changed, many untracked. This includes legitimate new work (Python code changes, test files) alongside a large deletion of archived wiki content. The MCP audit task itself is scoped correctly to the 5 finding files.

---

### ❌ Blockers (must fix before APPROVED)

None found. All 5 audit findings files exist, contain evidence-backed conclusions, and correctly describe the actual state of the 3 config files.

---

### Decision

**APPROVED ✅** — Audit task complete. No blockers.

### Loop Status

This is loop #1 of 3 maximum. No fixes required.

---

### Notes for @worker

When committing, be aware this diff is very large (1342 files). The MCP audit-specific changes are the 5 files under `.wiki/logs/mcp-audit/`. You may want to stage only those for a clean commit:

```bash
git add .wiki/logs/mcp-audit/*.md
git commit -m "audit: MCP cross-editor configuration audit findings"
```

The remaining changes (Python code, wiki deletions, etc.) appear to be from other concurrent work. Ensure they are reviewed separately before committing.
