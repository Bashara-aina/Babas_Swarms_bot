---
title: Contract 02 Verification
type: concept
status: legacy
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Verifier:** Worker Agent'
wikilinks: []
confidence: medium
source: research
---
# CLAUDE.md Verification Report
**Date:** 2026-04-14  
**Verifier:** Worker Agent  
**Scope:** Claims in `/home/newadmin/.claude/CLAUDE.md` vs actual implementation

---

## Summary Score

| Claim Area | CLAUDE.md Says | Actual Is | Status |
|---|---|---|---|
| Department count | "9 departments" | **10 departments** | ❌ MISMATCH |
| Agent count | "76+" | **107 agents** (non-legacy: 85) | ❌ MISMATCH |
| Intent count | (not claimed in CLAUDE.md) | **24 intents** in intent_router.py | ℹ️ N/A |
| Model roster | "gemma3:12b, qwen3.5:35b, exaone-deep:32b, phi4, llama3.3:70b" | **Model names don't match** — departments.yaml uses different naming scheme | ❌ MISMATCH |
| Env vars | `LEGION_DEFAULT_MODEL` only | CLAUDE.md accurate but **incomplete** — `LEGION_MASTER` mentioned in contract but not in doc | ⚠️ INCOMPLETE |

**Overall Accuracy: ~40%** (2/5 areas accurate, 3/5 have issues)

---

## 1. Department Count Verification

**CLAUDE.md claim:** "76+ specialized agents across 9 departments" (AGENTS.md header)  
**Actual departments in `config/departments.yaml`:**

```
engineering
design
research
marketing
operations
legal_compliance
product
creative
vision_multimodal
legacy
```

**Count:** 10 departments (NOT 9)

The comment in `departments.yaml` itself says `# config/departments.yaml — 76 agents across 9 departments` — this comment is also stale. The legacy department was added (making it 10 departments), and the agent count has grown far beyond 76.

---

## 2. Agent Count Verification

**CLAUDE.md claim:** "76+ specialized agents"  
**Actual agent count in `config/departments.yaml`:**

Per-department agent counts (from `grep -E "^\s{4}[a-z_]+:"`):

| Department | Agents | Agent IDs |
|---|---|---|
| engineering | 15 | senior_python_dev, frontend_react_dev, backend_fastapi_dev, rust_systems_dev, smart_contract_auditor, security_pentester, cuda_optimizer, debugging_specialist, test_automation_engineer, cicd_architect, database_optimizer, mlops_engineer, api_designer, code_reviewer, performance_tuner |
| design | 10 | ux_designer, graphic_designer, branding_strategist, motion_artist, spatial_designer, wireframe_specialist, color_expert, accessibility_auditor, prototype_builder, user_flow_mapper |
| research | 12 | deep_researcher, trend_forecaster, competitor_analyst, data_scientist, web_scraper_coordinator, sentiment_analyst, market_intel, survey_designer, interview_simulator, patent_searcher, paper_summarizer, stats_modeler |
| marketing | 13 | copywriter, seo_specialist, social_media_strategist, growth_hacker, content_strategist, ad_copywriter, viral_campaign_designer, email_marketer, influencer_outreach, analytics_interpreter, brand_voice_developer, pr_crisis_manager |
| operations | 7 | project_manager, task_coordinator, scheduler, cost_tracker, resource_allocator, workflow_optimizer, reporting_builder |
| legal_compliance | 6 | contract_reviewer, gdpr_expert, risk_assessor, ip_lawyer, ethics_auditor, compliance_checker |
| product | 8 | product_manager, roadmap_planner, user_research_lead, feedback_analyzer, feature_prioritizer, mvp_builder, beta_coordinator, launch_strategist |
| creative | 8 | storyteller, script_writer, video_concept_artist, music_composer, meme_creator, idea_generator, poetry_specialist, concept_artist |
| vision_multimodal | 6 | screenshot_analyzer, diagram_interpreter, ui_reviewer, image_descriptor, ocr_specialist, video_frame_analyzer |
| legacy | 22 | vision, coding, debug, math, architect, analyst, computer, general, researcher, marketer, devops, pm, humanizer, reviewer, think, owl, ag2_researcher, ag2_critic, ag2_synthesizer, code_exec, predictor, claude_orchestrator, debate |
| **TOTAL** | **107** | |

**Non-legacy total (what "76+" likely intended to describe):** 85 agents

**CLAUDE.md claim:** "76+" → **Actual: 107 total (85 non-legacy)** → MISMATCH in both directions

---

## 3. Intent Count Verification

**CLAUDE.md claim:** No specific intent count claimed  
**Actual intents defined in `core/intent_router.py`:** 24 intents

```
COMPUTER_CONTROL, CODE_GENERATION, CODE_REVIEW, WEB_RESEARCH, WEB_SCRAPE,
MEMORY_SEARCH, MEMORY_STORE, SCHEDULE_TASK, EMAIL_READ, EMAIL_WRITE,
SITE_ANALYSIS, DATABASE_AUDIT, WEATHER_QUERY, LOCATION_QUERY,
FILE_OPERATION, TRANSLATION, MATH_REASONING, CREATIVE_WRITE,
DATA_ANALYSIS, API_CALL, SELF_UPGRADE, CASUAL_CHAT, DEEP_REASONING
```

AGENTS.md Section 6 claims "45+ aiogram router files" — the actual `handlers/` directory has **41 files** (not counting `__init__.py` and `__pycache__`). So the "45+" claim in AGENTS.md is also stale.

---

## 4. Model Roster Verification

**CLAUDE.md claim:** "Active model roster: gemma3:12b, qwen3.5:35b, exaone-deep:32b, phi4, llama3.3:70b"

**Actual models referenced in `config/departments.yaml`:**

Primary models used:
- minimax-m2-7
- qwen3-235b
- glm-4
- kimi-k2
- devstral
- gemini-3.1-pro
- gemma4:e4b (legacy only)
- llama3-70b
- qwen-3-32b (legacy only)
- qwen3-coder:free
- claude-opus-4 (requires ANTHROPIC_API_KEY)
- gemma3-12b (vision_multimodal)

**Issues:**
1. **CLAUDE.md model names don't match departments.yaml**: CLAUDE.md says `qwen3.5:35b` but departments.yaml uses `qwen3-235b`. Similarly `llama3.3:70b` vs `llama3-70b`.
2. **CLAUDE.md lists 5 models**: departments.yaml references at least 12 distinct models.
3. **CLAUDE.md is missing `LEGION_MASTER`** mentioned in the contract — this env var is NOT documented in CLAUDE.md.

---

## 5. Handler/Agent File Count Verification

**CLAUDE.md (AGENTS.md) claim:** "45+ aiogram router files"  
**Actual `handlers/` files:**

```
41 handler files: admin_handlers.py, ai.py, artifact.py, brain.py,
business_handler.py, communications.py, computer.py, debate_handlers.py,
dev.py, draft.py, e2e.py, ecc_compat.py, enterprise.py, github_intel_handler.py,
harvest_review.py, inline.py, legion_extras.py, media_tools.py,
memory_commands.py, message_handler.py, nihongo_handler.py, orchestrate.py,
overnight_handler.py, persona_handler.py, pm.py, research.py,
runbook_handler.py, session_handler.py, sessions.py, shared.py, skills.py,
streaming.py, swarm_handler.py, system.py, tasks.py, upgrade.py, voice.py,
whatsapp_handler.py, wiki_handler.py, wiki.py
```

Count: 41 files (excluding `__init__.py`)

**CLAUDE.md (AGENTS.md) claim:** "76+ specialized agents"  
**Actual `agents/` files:** 8 files (ag2_pipeline.py, code_agent.py, mirofish_agent.py, owl_agent.py, research_agent.py, simulation_agent.py, voice_agent.py, plus `__init__.py` and research/strategy_nexus directories)

The "76+ agents" are defined in `departments.yaml`, not as individual Python files in `agents/`.

---

## 6. Environment Variables

**CLAUDE.md claims:** `LEGION_DEFAULT_MODEL` — override Ollama model default

**Verification:** `LEGION_DEFAULT_MODEL` IS documented in CLAUDE.md ✓

**Missing from CLAUDE.md:**
- `LEGION_MASTER` — mentioned in contract, not in CLAUDE.md Section 10
- No documentation of other Legion-specific env vars (if they exist)

---

## Key Mismatches Summary

| # | Claim in CLAUDE.md/AGENTS.md | Actual Implementation | Severity |
|---|---|---|---|
| 1 | "76+ specialized agents across **9** departments" | **107 agents** across **10** departments | HIGH |
| 2 | "**45+** aiogram router files" | **41** handler files | MEDIUM |
| 3 | Model roster: `qwen3.5:35b`, `llama3.3:70b` | departments.yaml uses `qwen3-235b`, `llama3-70b` (different naming) | MEDIUM |
| 4 | Model roster: only 5 models listed | 12+ models actually referenced | HIGH |
| 5 | `LEGION_MASTER` env var | NOT documented in CLAUDE.md | MEDIUM |

---

## Files Referenced

- `/home/newadmin/.claude/CLAUDE.md` — 40 lines, verified
- `/home/newadmin/swarm-bot/config/departments.yaml` — 900 lines, 10 departments, 107 agents
- `/home/newadmin/swarm-bot/core/intent_router.py` — 508 lines, 24 intent types
- `/home/newadmin/swarm-bot/handlers/` — 41 .py files
- `/home/newadmin/swarm-bot/agents/` — 8 .py files (agents are defined in YAML, not Python)

---

## Recommendations

1. **Update `departments.yaml` comment:** Change `# 76 agents across 9 departments` to `# 107 agents across 10 departments`
2. **Update CLAUDE.md model roster:** Use consistent model naming that matches actual Ollama model IDs
3. **Add `LEGION_MASTER`** to CLAUDE.md Section 10 Environment Variables
4. **Sync AGENTS.md claims** with actual handler/agent counts
