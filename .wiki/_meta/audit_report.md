---
title: Wiki Audit Report
type: reference
status: deprecated
tags:
- wiki
- audit
- meta
- karpathy-kb
created: '2026-04-13'
updated: '2026-04-13'
summary: Audit of .wiki/ directory identifying 1964 markdown files not following Karpathy LLM KB pattern. Provides directory structure mapping and migration guidance.
wikilinks: []
confidence: high
source: research
---
# Wiki Audit Report
> Generated: 2026-04-13
> Phase: PHASE 0 — Karpathy LLM KB Wiki Master Restructure

## Executive Summary

The existing `.wiki/` directory is a sprawling, unstructured knowledge base containing **1964 markdown files** accumulated across many sessions. It does NOT follow the Karpathy LLM KB pattern (raw/wiki/output structure). This audit identifies the current state and maps source files for migration.

## Directory Structure (Top-Level)

| Directory | Purpose | Files |
|-----------|---------|-------|
| `.wiki/` | Root wiki directory (NOT Karpathy pattern) | 1964 MD files total |
| `wiki/` | Separate root-level wiki directory | Contains knowledge/ structure |
| `.wiki/00-meta/` | Meta information | Contains README |
| `.wiki/01-cekwajar-product/` | Cekwajar product docs | Product-related |
| `.wiki/02-cekwajar-tech/` | Cekwajar technical docs | Tech architecture |
| `.wiki/03-regulatory/` | Regulatory docs | Indonesia tax/labor law |
| `.wiki/04-medvi-playbook/` | Medvi playbook | Gallagher model |
| `.wiki/05-growth-strategy/` | Growth strategy | CEKWAJAR roadmap |
| `.wiki/06-legion-instructions/` | Legion agent instructions | Coding references |
| `.wiki/07-gallagher-empire-model/` | Gallagher empire model | Business model |
| `.wiki/agents/` | Agent documentation | planner.md |
| `.wiki/architecture/` | System architecture | block_02, block_07, PRODUCTION-AGENT-PATTERNS |
| `.wiki/decisions/` | Architecture Decision Records | 50+ ADR files |
| `.wiki/research/` | ML/AI research papers | 100+ paper summaries |
| `.wiki/indexes/` | Index files | AI agents, dev patterns, opencode |
| `.wiki/founder-mindset/` | Founder mindset content | |
| `.wiki/candidate/` | Candidate docs | browser-agent, video-url, web-scraping |
| `.wiki/_archive/` | Archived content | |
| `.wiki/_quarantine/` | Quarantined files | 200+ files (orphaned/temp) |
| `.wiki/knowledge/` | Structured knowledge | tax, bpjs, labor-law, market, business, product, engineering |
| `.wiki/tools/` | Tool documentation | karpathy-wiki skill (THE PATTERN) |
| `.wiki/legion/` | Legion agent logs | |
| `.wiki/logs/` | Session logs | |
| `.wiki/issues/` | Issue tracking | |

## Source Files to Migrate to raw/

The following key project files should be copied to `raw/` for ingestion:

### Core Project Files
- `AGENTS.md` (2948 bytes) — Agent system documentation
- `README.md` (8639 bytes) — Project overview
- `CHANGELOG.md` (5552 bytes) — Version history
- `SWARM_WIRING.md` (5900 bytes) — Swarm wiring spec
- `DEPLOYMENT.md` (8902 bytes) — Deployment guide
- `TESTING.md` (10290 bytes) — Testing documentation
- `CONTRIBUTING.md` (1454 bytes) — Contribution guidelines
- `CLEANUP_LOG.md` (2155 bytes) — Cleanup operations
- `IMPLEMENTATION_STATUS.md` (8274 bytes) — Implementation status
- `DEEP_AUDIT_2026-04-12.md` (28790 bytes) — Deep audit results
- `CONCERNS_FIXED_REPORT.md` (1061 bytes) — Concerns fix report
- `WIRING_VERIFIED_2026-04-12.md` (3588 bytes) — Wiring verification

### Configuration Files
- `pyproject.toml` (1900 bytes)
- `requirements.txt` (2872 bytes)
- `requirements_no_tiktoken.txt` (1033 bytes)
- `Makefile` (2069 bytes)
- `docker-compose.yml` (3820 bytes)
- `config/` directory — YAML configs for models, departments, routing

### Python Source Files (for reference, NOT modification)
- `agents.py` (4021 bytes)
- `llm_client.py` (671 bytes)
- `router.py` (3087 bytes)
- `task_orchestrator.py` (19608 bytes)
- `daily_harvester.py` (2244 bytes)
- `test_apis.py` (1481 bytes)

### Legion/LLM System Files
- `LEGION_MASTER.md` (28305 bytes)
- `LEGION_PRODUCTION_HARDENING.md` (23474 bytes)
- `LEGION_CONCERNS_MASTER_PROMPT.md` (21502 bytes)
- `OPENCODE_DEPTH_UPGRADE_PROMPT.md` (35214 bytes)
- `OPENCODE_EXTERNAL_TOOLS_INTEGRATION.md` (35404 bytes)
- `CLAUDE_DEEP_AUDIT_PROMPT.md` (10570 bytes)
- `legion.log` (12669 bytes)
- `legion.db` (5074944 bytes) — binary, skip

### Prompts and Instructions
- `prompts/` directory — Master prompts and templates
- `agents/` directory — 76+ specialized agent files
- `llm_client/` directory — LLM client code
- `core/` directory — Agent orchestration (DO NOT TOUCH per constraints)

### Scripts
- `deploy.sh` (2247 bytes)
- `restart.sh` (1133 bytes)

## Issues Identified

### 1. Chaotic Directory Structure
- No `raw/`, `wiki/`, `output/` separation (Karpathy pattern)
- Files scattered across 30+ directories
- `_quarantine/` contains 200+ orphaned/temp files

### 2. Index Out of Sync
- `wiki/index.md` exists but doesn't reflect actual content
- No `wiki/log.md` for operation history

### 3. Missing Karpathy Pattern Infrastructure
- No `raw/` directory for immutable sources
- No `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/synthesis/`
- No `output/` directory for reports

### 4. Obsidian Config Missing
- `.obsidian/` exists but may be incomplete
- No `plugins.json` or proper `graph.json`

## Recommended Karpathy Structure

```
.wiki/
├── raw/                    # IMMUTABLE sources (will be created)
│   └── assets/
├── wiki/                   # LLM workspace (will be created)
│   ├── sources/            # Source summaries
│   ├── entities/            # People, orgs, products, tools
│   ├── concepts/            # Ideas, frameworks, patterns
│   ├── synthesis/           # Comparisons, analyses
│   ├── index.md            # Master catalog
│   └── log.md              # Operation log
├── output/                  # Reports (will be created)
├── SCHEMA.md               # Schema reference (will be created)
└── .obsidian/              # Obsidian config (will be wired)
```

## Migration Plan

1. **Phase 1**: Run onboarding script to create Karpathy directory structure
2. **Phase 2**: Copy key source files to `raw/`
3. **Phase 3**: Ingest sources to create wiki pages
4. **Phase 4**: Wire Obsidian config
5. **Phase 5**: Verify and commit

## Files NOT to Touch (Per Constraints)
- `main.py`
- `core/` directory
- `handlers/` directory
- `SOUL.md`
- `CLAUDE.md`
- `.env*` files
- `secrets.json`
