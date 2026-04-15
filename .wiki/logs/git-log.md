---
title: Git Log
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
summary: '- Date: Sat Apr 11 06:29:48 PM JST 2026'
wikilinks: []
confidence: medium
source: research
---
# git-log

## Commits

## Commit: e9262e8
- Date: Sat Apr 11 06:29:48 PM JST 2026
- Message: chore: sync all local changes excluding env files
---
## Commit: 5fc27d2
- Date: Sat Apr 11 07:31:27 PM JST 2026
- Message: CHORE: pre-dead-file-purge checkpoint 2026-04-11
---
## Commit: 8c78cdc
- Date: Sat Apr 11 08:46:17 PM JST 2026
- Message: feat(wiki): add complete Legion knowledge base — 13 files across 8 directories
---
## Commit: 0ef8ad7
- Date: Sat Apr 11 08:46:46 PM JST 2026
- Message: feat(wiki): add complete Legion knowledge base — 13 files across 8 directories
---
## Commit: 835e000
- Date: Sun Apr 12 01:31:20 PM JST 2026
- Message: add some
---
## Commit: d36e8ec
- Date: Sun Apr 12 01:31:35 PM JST 2026
- Message: add some
---
## Commit: 1a7294e
- Date: Sun Apr 12 01:32:16 PM JST 2026
- Message: add some
---
## Commit: aa15f5e
- Date: Sun Apr 12 05:23:14 PM JST 2026
- Message: chore: wiring/wiki updates and module integration
---
## Commit: a260dbe
- Date: Sun Apr 12 05:25:52 PM JST 2026
- Message: chore: add audit15 integration notes and test updates
---
## Commit: f0df3b8
- Date: Sun Apr 12 05:52:01 PM JST 2026
- Message: chore: apply repository cleanup and wiring follow-ups
---
## Commit: fca8599
- Date: Sun Apr 12 07:40:35 PM JST 2026
- Message: chore: finalize concerns fixes, audits, and orchestration updates
---
## Commit: 052914b
- Date: Sun Apr 12 07:49:13 PM JST 2026
- Message: chore: finalize review/completion logs and wiki updates
---
## Commit: d602f7f
- Date: Sun Apr 12 07:49:30 PM JST 2026
- Message: chore: update git log ledger
---
## Commit: 317bf73
- Date: Sun Apr 12 07:49:58 PM JST 2026
- Message: chore: refresh git log after push sequence
---
## Commit: f335f99
- Date: Sun Apr 12 07:53:22 PM JST 2026
- Message: chore: refresh git log safely
---
## Commit: cd8eb0d
- Date: Mon Apr 13 12:44:30 PM JST 2026
- Message: chore: sync audit quarantine and wiki restructuring
---
## Commit: 911c695
- Date: Mon Apr 13 12:56:39 PM JST 2026
- Message: fix: surgical repair — frontmatter YAML, duplicate file resolved, broken wikilinks fixed
---
## Commit: de05176
- Date: Mon Apr 13 01:16:37 PM JST 2026
- Message: audit: comprehensive implementation audit 2026-04-13 — full system verification

Findings: 8 critical, 8 warnings
- CF-1: No OpenCode config file (all agents hardcoded model, no temperature)
- CF-2: 303 broken wikilinks (wrong .md extension in links)
- CF-3: Split-brain .wiki/ vs wiki/ with divergent content
- CF-4: OpenCode agents write to .wiki/ not wiki/
- CF-5: compile_state.json timestamp is fake midnight
- CF-6: 8 command files are empty (0 lines)
- CF-7: 29 stub articles below word minimums
- CF-8: 69 YAML parsing failures (inline wikilink arrays)

Karpathy compliance: 3/12 | /swarm compliance: 9/10

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 392d6cc
- Date: Mon Apr 13 01:20:10 PM JST 2026
- Message: feat: wiki enrichment — stub elimination, schema fixes, wikilink normalization
---
## Commit: 5354db7
- Date: Mon Apr 13 01:22:59 PM JST 2026
- Message: fix: batch1 — wikilinks, YAML frontmatter, path wiring, opencode.json
---
## Commit: 7cbc402
- Date: Mon Apr 13 05:34:24 PM JST 2026
- Message: wiki: ingest POPW research meetings 4th-14th — concepts, entities, timelines, decisions

- concepts/: film-modulation, pose-derived-detection, kendall-loss, wise-iou, multi-task-learning
- entities/: ikea-asm, assembly101, ha4m, industreal, ego-exo4d
- timelines/: popw-meetings-nov-dec-2025, popw-meetings-jan-mar-2026, popw-meetings-mar-apr-2026
- decisions/: adr-2026-01-film-over-attention, adr-2026-03-pdd-pivot, adr-2026-04-conference-submission-strategy
- projects/: popw-research (updated)
---
## Commit: 3071c8d
- Date: Mon Apr 13 05:36:04 PM JST 2026
- Message: wiki: ingest POPW research meetings — concepts, entities, timelines, and decisions
---
## Commit: ab54128
- Date: Mon Apr 13 05:36:12 PM JST 2026
- Message: fix: quote summary field in popw-meetings-mar-apr-2026 timeline
---
## Commit: 7625978
- Date: Mon Apr 13 05:37:57 PM JST 2026
- Message: wiki: fix YAML frontmatter in 3 audit files

Fixed WIRING_AUDIT_REPORT.md (bold metadata → proper YAML FM),
legion/audit-2026-04-11-fixes.md, logs/worker-final-2026-04-11.md
(prepend --- to fix malformed frontmatter blocks).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: c9fec77
- Date: Mon Apr 13 05:38:49 PM JST 2026
- Message: wiki: update compile_state — merged vault, 2091 articles, 1688 proper FM (80.5%)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 99a1a65
- Date: Mon Apr 13 05:55:34 PM JST 2026
- Message: wiki: add POPW research articles + architectural diagram

- architecture/worker-net-architecture-diagram.md: Full pipeline diagram with embedded local image
- architecture/worker-net-improved4.md: ResNet50-FPN + 3 heads + PoseFiLMModule
- architecture/popw-training-pipeline.md: FP16 training, Kendall weighting, validation metrics
- research/popw-film-literature-gap.md: Novelty argument — no prior pose→FiLM→action work
- research/popw-model-comparison.md: improved4_film benchmark: mAP@0.5=0.600, PCK@0.1=99.9%
- research/popw-v14-ground-truth.md: Source code audit — P3 shape [B,256,80,60] correction

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: c1e4e37
- Date: Mon Apr 13 06:01:20 PM JST 2026
- Message: wiki: fix 100 YAML failures across research papers, decisions, wisdom

- Fix bold metadata in decisions (ADR files): **Key:** value → proper YAML
- Fix research paper implementation fields with 3-value comma issues
- Fix YAML list blank line in hoi-survey-2023-2024
- Fix wikilinks in research: comma-separated → proper YAML list
- Fix git-log.md wrongly had FM delimiters (working doc, no FM needed)
- Fix ADR-001-api-key-fix.md unquoted backtick-heavy current_vision_chain
- Compile state: 2098 articles, 0 yaml_fails, 0 broken_links

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: e9a805e
- Date: Mon Apr 13 06:09:11 PM JST 2026
- Message: wiki: add PDF paths to FiLM/Kendall/IKEA ASM research articles

- Add pdf_path frontmatter to 003-film-perez-2018.md
- Add pdf_path to 004-kendall-uncertainty-2018.md
- Add pdf_path to 005-ikea-asm-dataset-2021.md
- Fix broken wikilink in 028-amtl-yun-cho-2023.md
- Archive duplicate Kendall/IKEA files to _archived_duplicates/

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 8aa4d1d
- Date: Mon Apr 13 06:41:07 PM JST 2026
- Message: wiki: link 17 downloaded papers to pdf_path frontmatter

Updated pdf_path for papers downloaded in previous session:
- ResNet, FPN, FiLM, Kendall, IKEA ASM (already done)
- Focal Loss, Mask R-CNN, Simple Baselines, GIoU, GradNorm
- PCGrad, MGDA, Assembly101, I3D, TSM, DINOv2, YOLO, DETR, Attention

Also archived 2 duplicate articles (004-multitask-kendall, 005-ikea-asm-benshabat)
that were less POPW-specific than their canonical counterparts.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: aa2f895
- Date: Mon Apr 13 06:55:14 PM JST 2026
- Message: wiki: add 8 research articles for Assembly101 and IndustReal papers

Added articles:
- 075: ATTACH Dataset (two-handed assembly actions)
- 076: Fusing Hand Body Skeleton + Object features
- 077: Foundation Model Augmentation for Hand Pose
- 078: ProMQA-Assembly multimodal procedural QA
- 079: Object-Aware Egocentric Online Action Detection
- 080: Procedure-Aware Pretraining for Instructional Video
- 081: Prompt-Enhanced Hierarchical Transformer (CPR)
- 082: MS-TCN for Action Segmentation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 3738c7c
- Date: Mon Apr 13 06:58:10 PM JST 2026
- Message: refactor: fix 228 broken wikilinks across 54 wiki files

- Add ./concepts/ prefix to bare concept links
- Add ./entities/ prefix to bare entity links
- Remove incorrect wiki/ prefixes
- Remove trailing slashes from directory links
- Add batch_fix_wikilinks.py script for future fixes
---
## Commit: e03e5e4
- Date: Mon Apr 13 06:58:15 PM JST 2026
- Message: refactor: wikilink path corrections in wiki content
---
## Commit: 3e9ca87
- Date: Mon Apr 13 07:07:22 PM JST 2026
- Message: refactor: remove split-brain wiki/ vault — .wiki/ is canonical

Deleted wiki/ (2.1M, 242 files) — Obsidian vault at project root was
duplicate of .wiki/. Both had .obsidian/ dirs and identical harvester
output. .wiki/ is the canonical vault per CLAUDE.md Section 2b.

main.py and all code already reference .wiki/ — no path updates needed.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 9defd78
- Date: Mon Apr 13 07:08:35 PM JST 2026
- Message: chore: add scattered dirs to .gitignore, clean embedded repos

- Add project/, cekwajar/, meeting/, popwadditional/, wiki/ to .gitignore
- These are separate project directories, not part of swarm-bot
- Remove embedded git repo reference for project/rumahlabuh

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: e966d49
- Date: Mon Apr 13 07:09:27 PM JST 2026
- Message: wiki: fix last YAML fail in contracts-batch4-wiki-wiring.md

summary field had unquoted colon-containing value.
Compile state: 2113 articles, 0 yaml_fails, 0 broken_links.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 00d78d6
- Date: Mon Apr 13 08:36:58 PM JST 2026
- Message: wiki: add session_harvester.py — auto-capture Claude Code + OpenClaude + Legion sessions as draft stubs
---
## Commit: 7af1e42
- Date: Mon Apr 13 08:53:51 PM JST 2026
- Message: wiki: add session_harvester.py + session_synthesizer.py — full auto-ingestion pipeline

Pipeline:
- session_harvester.py: captures Claude Code + OpenClaude + Legion bot sessions every 30min
- session_synthesizer.py: synthesizes stubs into wiki articles (concepts/decisions) using Cerebras llama3.1-8b
- stubs → .wiki/conversations/ (draft review)
- synthesized → .wiki/concepts/ + .wiki/decisions/ (proper articles with frontmatter + wikilinks)
- Cron: harvester */30min, synthesizer */35min
- 24 stubs processed → 16 wiki articles in first run
---
## Commit: 263adb9
- Date: Mon Apr 13 11:05:11 PM JST 2026
- Message: research: temporal attention alternatives for POPW BiGRU replacement
---
## Commit: ee745fa
- Date: Mon Apr 13 11:05:37 PM JST 2026
- Message: research: log POPW architecture improvement swarm run (2026-04-13)
---
## Commit: e1ca3e6
- Date: Mon Apr 13 11:19:23 PM JST 2026
- Message: fix: DNS-resilient HTTP client for rumahlabuh.com connectivity
---
## Commit: 5b0386f
- Date: Tue Apr 14 09:58:20 AM JST 2026
- Message: research: add DEEP_AUDIT quarantine analysis (5 contracts, 7797 words)
---
## Commit: 408d68d
- Date: Tue Apr 14 10:07:41 AM JST 2026
- Message: fix: productivity.py timer user_id fallback, rumahlabuh_crew draft_guest_reply call_llm — comprehensive audit fixes
---
## Commit: 5c29b51
- Date: Tue Apr 14 10:18:25 AM JST 2026
- Message: wiki: revive quarantined files with score > 0.05
---
## Commit: aaec6ae
- Date: Tue Apr 14 10:32:53 AM JST 2026
- Message: fix: tighten wiki quarantine threshold 0.15 → 0.05
---
## Commit: 49286e8
- Date: Tue Apr 14 12:00:24 PM JST 2026
- Message: fix: unify wiki path from wiki/ to .wiki/ across core modules
---
## Commit: af30503
- Date: Tue Apr 14 12:58:12 PM JST 2026
- Message: docs: add POPW temporal architecture diagram with BiGRU and Feature Bank
---
## Commit: 8b25a33
- Date: Tue Apr 14 01:12:11 PM JST 2026
- Message: docs: add BiGRU temporal modeling to POPW architecture XML
---
## Commit: 0d353aa
- Date: Tue Apr 14 01:15:46 PM JST 2026
- Message: wiki: add POPW temporal modeling research stack (BiGRU, feature bank, pose conditioning)
---
## Commit: 108ca0b
- Date: Tue Apr 14 01:17:11 PM JST 2026
- Message: fix: remove OpenAI SDK from voice.py, migrate tiers.py to aiosqlite, add wiki batch fix scripts
---
## Commit: 4109560
- Date: Tue Apr 14 01:19:45 PM JST 2026
- Message: wiki: fix 016 frontmatter, add 020 comprehensive survey
---
## Commit: b432562
- Date: Tue Apr 14 01:26:13 PM JST 2026
- Message: research: BiGRU replacement comparison — Mamba recommended for POPW activity head
---
## Commit: c6bf1b9
- Date: Tue Apr 14 02:25:51 PM JST 2026
- Message: wiki: add 20 Mamba + MMN papers for pose-aware activity recognition

Mamba papers (8):
- mamba-selective-ssm (foundation)
- vision-mamba, video-mamba (backbone/temporal)
- spikmamba, ms-temba, vl-mamba, mamba-track, mamba-motion-generation

MMN/Motion papers (10):
- 015-motion-modulation-acmmm-2025 (MMN foundation)
- mans-tarm, psumnet, lsta-net, epam-net (temporal/attention)
- dmm-motion, just-add-pi, pogars, posescript, st-gcn

Comprehensive survey:
- mamba-pose-activity-survey (full 18-paper synthesis)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 566c9f3
- Date: Tue Apr 14 04:10:26 PM JST 2026
- Message: feature: add Mamba SSM as BiGRU alternative in POPW paper skeleton
---
## Commit: 609189f
- Date: Tue Apr 14 11:01:39 PM JST 2026
- Message: fix: add tool configs to gitignore, add direct wiki_bridge call in opencode_bridge, remove session hooks
---
## Commit: 79d2c8f
- Date: Thu Apr 16 12:09:09 AM JST 2026
- Message: docs: add deep integration design for OpenCode ⇄ Claude Code ⇄ LegionBot

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 9679a70
- Date: Thu Apr 16 12:30:22 AM JST 2026
- Message: feat: document multi-session worktree system in SOUL.md, CLAUDE.md, and wiki

SOUL.md: Added multi-session worktree system section explaining
  the git-worktree isolation system Legion now knows about.

CLAUDE.md: Added 2c (Multi-Session Worktree System) to architecture
  map and CLAUDE_REPO_ROOT / CLAUDE_WORKTREES_ROOT env vars.

.wiki/architecture/multi-session-worktrees.md: New article documenting
  architecture, usage, and design rationale (advisory vs enforced locking).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 1707b1c
- Date: Thu Apr 16 12:31:43 AM JST 2026
- Message: feat: add joint_memory facade for OpenCode/Claude Code/LegionBot
---
## Commit: 12bfb3b
- Date: Thu Apr 16 12:33:22 AM JST 2026
- Message: feat: add _claude_code_brain_layer() to unified prompt context

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 05b8f3c
- Date: Thu Apr 16 12:34:16 AM JST 2026
- Message: feat: add claude_code_write_session to wiki bridge
---
## Commit: e5b2e00
- Date: Thu Apr 16 12:36:14 AM JST 2026
- Message: feat: add claude_code_bridge bidirectional Claude Code↔OpenCode bridge

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: 8172aa2
- Date: Thu Apr 16 12:37:35 AM JST 2026
- Message: feat: add legion_callback_bridge with recursive depth tracking
---
## Commit: a593fb4
- Date: Thu Apr 16 12:39:25 AM JST 2026
- Message: feat: add @legion/@claude directive parsing and cross-system callbacks
---
## Commit: c7ca3cf
- Date: Thu Apr 16 01:38:58 AM JST 2026
- Message: feat: add legiona shared agent definitions
---
## Commit: 701d84f
- Date: Thu Apr 16 01:40:45 AM JST 2026
- Message: feat: add legion-callback and claude-callback commands
---
## Commit: 9b17a8d
- Date: Thu Apr 16 01:44:17 AM JST 2026
- Message: feat: add claude_code session hooks to builtin_hooks
---
## Commit: bb4bbdf
- Date: Thu Apr 16 01:45:41 AM JST 2026
- Message: feat: add /codex handler for Claude Code bridge
---
## Commit: 7fb9285
- Date: Thu Apr 16 01:48:05 AM JST 2026
- Message: docs: add three-system integration architecture to CLAUDE.md
---
## Commit: 120222e
- Date: Thu Apr 16 02:05:54 AM JST 2026
- Message: fix: remove invalid kwargs from run_claude_task call
---
## Commit: 7c4a205
- Date: Thu Apr 16 03:10:05 AM JST 2026
- Message: feat(cekwajar): Stage 1 — project scaffold complete

- Full shadcn/ui component library (button, input, label, select, card, dialog, toast, badge, tabs, progress, separator, sheet, skeleton, alert)
- Cookie-based Supabase auth with @supabase/ssr middleware
- Homepage with hero + 5 tool cards + how-it-works section
- Mobile-first layout with GlobalNav (Sheet side panel) and Footer
- .env.local with all API keys (Supabase, Google Vision, Midtrans)
- TypeScript: zero errors (pnpm tsc --noEmit)
- Dev server: HTTP 200 on localhost:3000

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
## Commit: cedc71b
- Date: Thu Apr 16 03:18:50 AM JST 2026
- Message: feat(cekwajar): Stage 2 — database schema, migrations, RLS, seed data, query helpers

- 19 SQL migrations covering all tables (users, subscriptions, transactions,
  payslip_audits, salary/property/col/ppp benchmarks, reference data)
- Full RLS policies on all tables via migrations 004 and 011
- pg_cron jobs for record purging and subscription expiry checks
- TER A/B/C brackets (PMK 168/2023), BPJS rates, PTKP values, 48 city UMK
- COL indices (20 cities), 15-country PPP reference, 10 COL categories
- src/types/database.types.ts — fully typed TypeScript definitions
- src/lib/db/queries.ts — typed helper functions (getUserTier, getUMKForCity,
  getTERRate, getBPJSRates, getPTKPValue, incrementOCRCounter, COL/PPP/salary/
  property helpers)
- Fixed NEXT_PUBLIC_SUPABASE_ANON_KEY → NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
  across server.ts, client.ts, and middleware.ts
---
## Commit: 94b5938
- Date: Thu Apr 16 03:28:15 AM JST 2026
- Message: feat: stage 3 complete — auth, dashboard, subscription system

- Add dashboard middleware protection (/dashboard → /auth/login)
- Add PremiumGate component with blur overlay + upgrade CTA
- Add upgrade/page.tsx with 3-tier pricing cards
- Add pricing/page.tsx with feature comparison table + FAQ
- Fix Tool type to include description field
- Fix getCurrentUser return type to use Awaited<ReturnType<>>
- Fix pricing page union type indexing with explicit type annotation
- PremiumGate, SubscriptionBadge, GlobalNav all in place
- Zero TypeScript errors (pnpm tsc --noEmit)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
---
