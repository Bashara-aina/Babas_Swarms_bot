---
title: "Wiki Audit Report"
date: 2026-04-13
tags:
  - audit
  - wiki
  - migration
  - wiki-audit
type: audit_report
status: complete
summary: "Comprehensive audit of wiki structure covering root .md files, wiki/, .wiki/, docs/, skills/ directories"
sources:
  - wiki/_meta/
---

# Wiki Audit Report — 2026-04-13

## Audit Scope
- Root-level `.md` files
- `wiki/` directory (full recursive)
- `.wiki/` directory (full recursive)
- `docs/`, `skills/`, `prompts/` directories

---

## PHASE 0 — Structured Audit Report

### Root-Level .md Files

| Type | Status | Content Summary | Target Location | Wikilink Potential | Action Required |
|------|--------|-----------------|-----------------|-------------------|-----------------|
| LEGION_MASTER.md | ACTIVE | 617-line master prompt, current session tasks, implementation status | wiki/raw/docs/legion-master.md | HIGH — core reference | COPY |
| LEGION_PRODUCTION_HARDENING.md | ACTIVE | 515-line production hardening master prompt, 8 phases | wiki/raw/docs/legion-production-hardening.md | HIGH — architecture reference | COPY |
| SWARM_WIRING.md | ACTIVE | Swarm bot wiring guide, 87-agent pipeline documentation | wiki/raw/docs/swarm-wiring.md | MEDIUM — swarm reference | COPY |
| IMPLEMENTATION_STATUS.md | ACTIVE | 197-line Phase 1 completion tracking, 16/19 tasks | wiki/raw/docs/implementation-status.md | HIGH — project tracking | COPY |
| ARCHITECTURE_V5.md | LEGACY | Old v5 architecture diagram (superseded) | wiki/raw/docs/architecture-v5.md | MEDIUM — historical | COPY |
| OPENCODE_DEPTH_UPGRADE_PROMPT.md | ACTIVE | OpenCode session enhancement prompt | wiki/raw/prompts/opencode-depth-upgrade.md | MEDIUM | COPY |
| OPENCODE_EXTERNAL_TOOLS_INTEGRATION.md | ACTIVE | External tools integration guide | wiki/raw/docs/opencode-external-tools.md | MEDIUM | COPY |
| WIRING_VERIFIED_2026-04-12.md | COMPLETE | Verification checklist output | wiki/raw/audits/wiring-verified-2026-04-12.md | LOW | COPY |
| CONCERNS_FIXED_REPORT.md | COMPLETE | Concerns resolution report | wiki/raw/audits/concerns-fixed-report.md | LOW | COPY |
| TESTING.md | ACTIVE | Testing guide and patterns | wiki/raw/docs/testing.md | MEDIUM | COPY |
| CLEANUP_LOG.md | COMPLETE | Cleanup operations log | wiki/raw/audits/cleanup-log.md | LOW | COPY |
| AGENTS.md | ACTIVE | SwarmBot agent instructions (supersedes wiki/SCHEMA) | **KEEP IN ROOT** | HIGH | DO NOT MOVE |
| SOUL.md | ACTIVE | Legion identity/character (sacred — DO NOT TOUCH) | **KEEP IN ROOT** | HIGH | DO NOT MOVE |
| CLAUDE.md | ACTIVE | Developer context (sacred — DO NOT TOUCH) | **KEEP IN ROOT** | HIGH | DO NOT MOVE |
| MIGRATION.md | LEGACY | Old migration doc | wiki/raw/docs/migration.md | LOW | COPY |
| UI_UX_AUDIT_2026.md | COMPLETE | UI/UX audit results | wiki/raw/audits/ui-ux-audit-2026.md | MEDIUM | COPY |
| RATE_LIMIT_RESILIENCE.md | COMPLETE | Rate limit patterns | wiki/raw/docs/rate-limit-resilience.md | MEDIUM | COPY |
| SELF_UPGRADE.md | LEGACY | Self-upgrade guide (old) | wiki/raw/docs/self-upgrade.md | LOW | COPY |
| IMPLEMENTATION_GUIDE_UI_UX.md | LEGACY | UI/UX implementation | wiki/raw/docs/implementation-guide-ui-ux.md | MEDIUM | COPY |
| UI_UX_COMPLETE_OVERHAUL.md | LEGACY | Old UI overhaul | wiki/raw/docs/ui-ux-overhaul.md | LOW | COPY |
| HOTFIX_*.md | COMPLETE | Emergency fixes | wiki/raw/changelogs/ | LOW | COPY |
| UPGRADE_LOG_v7.md | COMPLETE | v7 upgrade log | wiki/raw/changelogs/upgrade-log-v7.md | MEDIUM | COPY |
| API_RELIABILITY_GUIDE.md | ACTIVE | API reliability patterns | wiki/raw/docs/api-reliability-guide.md | MEDIUM | COPY |

---

### wiki/ Directory Files

| Type | Status | Content Summary | Target Location | Wikilink Potential | Action Required |
|------|--------|-----------------|-----------------|-------------------|-----------------|
| wiki/SCHEMA.md | ACTIVE | Legion wiki schema v1.0 (40 lines) | **REPLACE** with new Karpathy schema | HIGH | REPLACE |
| wiki/INDEX.md | ACTIVE | Section index (22 lines) | **REPLACE** with Dataview INDEX | HIGH | REPLACE |
| wiki/legion/code_reviews.md | ACTIVE | Code review patterns log | wiki/architecture/code-reviews.md | HIGH | MOVE |
| wiki/legion/conversations_log.md | ACTIVE | Conversation tracking | wiki/timelines/legion-conversations.md | HIGH | MOVE |
| wiki/legion/opencode-integration-2026-04-11.md | ACTIVE | OpenCode integration notes | wiki/decisions/adr-2026-04-11-opencode-integration.md | HIGH | MOVE |
| wiki/conversations/2026-04-*.md | ACTIVE | Session summaries | wiki/timelines/conversations-2026-04-*.md | HIGH | MOVE |
| wiki/conversations/_template.md | ACTIVE | Conversation template | wiki/timelines/_template.md | MEDIUM | MOVE |
| wiki/decisions/ | EMPTY | Placeholder directory | — | — | DELETE EMPTY DIR |
| wiki/rumahlabuh/ | EMPTY | Placeholder directory | — | — | DELETE EMPTY DIR |
| wiki/opencode/sessions/ | ACTIVE | OpenCode session logs | wiki/architecture/opencode-sessions.md | MEDIUM | MOVE |
| wiki/research/papers/_template.md | ACTIVE | Paper analysis template | wiki/research/paper-template.md | MEDIUM | MOVE |
| wiki/bashara/ | ACTIVE | User profile directory | wiki/people/bashara.md | HIGH | MERGE → people/ |
| wiki/tokyo/ | ACTIVE | Tokyo life notes | wiki/concepts/tokyo-life.md | MEDIUM | MOVE |
| wiki/tools/ | ACTIVE | Tools documentation | wiki/concepts/tooling-ecosystem.md | MEDIUM | MOVE |

---

### .wiki/ Directory (Knowledge Base)

| Type | Status | Content Summary | Target Location | Wikilink Potential | Action Required |
|------|--------|-----------------|-----------------|-------------------|-----------------|
| .wiki/decisions/ADR-*.md | ACTIVE | 60+ Architecture Decision Records | wiki/decisions/ | HIGH | COPY ALL |
| .wiki/knowledge/tax/* | ACTIVE | Indonesian tax reference (28 files) | wiki/concepts/tax-indonesia/*.md | HIGH | COPY |
| .wiki/knowledge/labor-law/* | ACTIVE | Indonesian labor law (18 files) | wiki/concepts/labor-law-indonesia/*.md | HIGH | COPY |
| .wiki/knowledge/market/* | ACTIVE | Salary/market data (20 files) | wiki/concepts/market-data-indonesia/*.md | HIGH | COPY |
| .wiki/knowledge/business/* | ACTIVE | Business/saas research (10 files) | wiki/concepts/business-research/*.md | HIGH | COPY |
| .wiki/knowledge/bpjs/* | ACTIVE | BPJS reference (10 files) | wiki/concepts/bpjs-reference/*.md | HIGH | COPY |
| .wiki/knowledge/cekwajar/* | ACTIVE | cekwajar project knowledge | wiki/projects/cekwajar/*.md | HIGH | COPY |
| .wiki/knowledge/personal/* | ACTIVE | Personal notes | wiki/people/personal/*.md | MEDIUM | COPY |
| .wiki/05-growth-strategy/CEKWAJAR-ROADMAP.md | ACTIVE | Cekwajar roadmap | wiki/projects/cekwajar-roadmap.md | HIGH | COPY |
| .wiki/legion/* | ACTIVE | Legion audits and refactoring | wiki/architecture/legion-*.md | HIGH | COPY |

---

### docs/ Directory Files

| Type | Status | Content Summary | Target Location | Wikilink Potential | Action Required |
|------|--------|-----------------|-----------------|-------------------|-----------------|
| docs/ARCHITECTURE_V5.md | LEGACY | v5 architecture diagram | wiki/raw/docs/architecture-v5.md | MEDIUM | COPY |
| docs/MIGRATION.md | LEGACY | Migration guide | wiki/raw/docs/migration.md | LOW | COPY |
| docs/agents.md | ACTIVE | SwarmBot agents reference | wiki/raw/docs/swarmbot-agents.md | HIGH | COPY |
| docs/UI_UX_AUDIT_2026.md | COMPLETE | UI/UX audit | wiki/raw/audits/ui-ux-audit-2026.md | MEDIUM | COPY |
| docs/RATE_LIMIT_RESILIENCE.md | ACTIVE | Rate limit patterns | wiki/raw/docs/rate-limit-resilience.md | MEDIUM | COPY |
| docs/UPGRADE_LOG_v7.md | COMPLETE | v7 upgrade log | wiki/raw/changelogs/upgrade-log-v7.md | MEDIUM | COPY |
| docs/SELF_UPGRADE.md | LEGACY | Self-upgrade guide | wiki/raw/docs/self-upgrade.md | LOW | COPY |
| docs/IMPLEMENTATION_GUIDE_UI_UX.md | LEGACY | UI/UX guide | wiki/raw/docs/implementation-guide-ui-ux.md | MEDIUM | COPY |
| docs/API_RELIABILITY_GUIDE.md | ACTIVE | API reliability | wiki/raw/docs/api-reliability-guide.md | MEDIUM | COPY |
| docs/hotfixes/*.md | COMPLETE | Emergency fixes | wiki/raw/changelogs/hotfixes/*.md | LOW | COPY |

---

### skills/ Directory Files

| Type | Status | Content Summary | Target Location | Wikilink Potential | Action Required |
|------|--------|-----------------|-----------------|-------------------|-----------------|
| skills/recallmax.md | ACTIVE | Memory recall patterns | wiki/raw/skills_ref/recallmax.md | HIGH | COPY |
| skills/testing_patterns.md | ACTIVE | Testing best practices | wiki/raw/skills_ref/testing-patterns.md | HIGH | COPY |
| skills/prompt-engineer.md | ACTIVE | Prompt engineering | wiki/raw/skills_ref/prompt-engineer.md | HIGH | COPY |
| skills/security_checklist.md | ACTIVE | Security patterns | wiki/raw/skills_ref/security-checklist.md | HIGH | COPY |
| skills/supabase-engineer.md | ACTIVE | Supabase skills | wiki/raw/skills_ref/supabase-engineer.md | HIGH | COPY |
| skills/security-auditor.md | ACTIVE | Security auditing | wiki/raw/skills_ref/security-auditor.md | HIGH | COPY |
| skills/rag-engineer.md | ACTIVE | RAG patterns | wiki/raw/skills_ref/rag-engineer.md | HIGH | COPY |
| skills/tool-use-guardian.md | ACTIVE | Tool safety | wiki/raw/skills_ref/tool-use-guardian.md | HIGH | COPY |
| skills/python_patterns.md | ACTIVE | Python patterns | wiki/raw/skills_ref/python-patterns.md | HIGH | COPY |
| skills/aiogram-patterns.md | ACTIVE | Aiogram bot patterns | wiki/raw/skills_ref/aiogram-patterns.md | HIGH | COPY |
| skills/payroll-indonesia.md | ACTIVE | Indonesian payroll | wiki/raw/skills_ref/payroll-indonesia.md | HIGH | COPY |
| skills/location-advisor.md | ACTIVE | Location advice | wiki/raw/skills_ref/location-advisor.md | MEDIUM | COPY |
| skills/debugging-strategies.md | ACTIVE | Debug tactics | wiki/raw/skills_ref/debugging-strategies.md | MEDIUM | COPY |
| skills/nextjs-engineer.md | ACTIVE | Next.js patterns | wiki/raw/skills_ref/nextjs-engineer.md | HIGH | COPY |
| skills/e2e-tester.md | ACTIVE | E2E testing | wiki/raw/skills_ref/e2e-tester.md | MEDIUM | COPY |
| skills/brainstorming.md | ACTIVE | Brainstorming skill | wiki/raw/skills_ref/brainstorming.md | MEDIUM | COPY |
| skills/debugging.md | ACTIVE | Debug skill | wiki/raw/skills_ref/debugging.md | MEDIUM | COPY |
| skills/api-cost-optimizer.md | ACTIVE | API cost optimization | wiki/raw/skills_ref/api-cost-optimizer.md | MEDIUM | COPY |

---

### Duplicate Detection Map

| Original Path | Duplicate Path | Action |
|--------------|----------------|--------|
| wiki/legion/conversations_log.md | .wiki/logs/legion/conversations_log.md | MERGE → keep newer |
| wiki/legion/opencode-integration-2026-04-11.md | .wiki/decisions/ADR-001-opencode-integration.md | MERGE → consolidate |
| wiki/SCHEMA.md | .wiki/knowledge/wiki-schema.md | REPLACE with Karpathy schema |

---

### Empty/Orphaned Directories

| Directory | Action |
|-----------|--------|
| wiki/decisions/ | DELETE (empty) |
| wiki/rumahlabuh/ | DELETE (empty, replaced by projects/cekwajar-id.md) |
| wiki/opencode/sessions/ | MOVE contents → wiki/architecture/ |

---

## Migration Summary

- **Files to COPY**: ~150+ files
- **Files to MOVE**: ~15 files
- **Files to DELETE (empty dirs)**: 2 directories
- **Files to REPLACE**: 2 files (SCHEMA.md, INDEX.md)
- **DO NOT TOUCH**: SOUL.md, CLAUDE.md, AGENTS.md, main.py, core/, handlers/

---

## Audit Completed: 2026-04-13