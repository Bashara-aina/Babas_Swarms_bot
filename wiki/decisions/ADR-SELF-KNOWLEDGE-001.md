---
title: "ADR-SELF-KNOWLEDGE-001: Master Architecture Overview"
type: decision
status: active
tags: [adr, architecture, self-knowledge, cross-repo]
created: 2026-04-11
updated: 2026-04-11
summary: Architecture overview of all repositories and projects in Bashara's AI agent system, providing self-knowledge mapping for the SwarmBot/Legion system to understand its own ecosystem.
wikilinks: []
confidence: high
source: implementation
---

# ADR-SELF-KNOWLEDGE-001: Master Architecture Overview

**Date**: 2026-04-11  
**Status**: Accepted  
**Type**: Architecture Decision Record

---

## Context

This ADR documents the architecture of all known repositories and projects managed by or related to Bashara's AI agent system. The goal is to provide a comprehensive self-knowledge map for the SwarmBot/Legion agent system to understand its own ecosystem.

---

## Decision

### Repository Map

#### 1. SwarmBot (Primary)
- **Location**: `/home/newadmin/swarm-bot/`
- **Type**: Python Telegram bot with multi-agent orchestration
- **Tech Stack**:
  - aiogram 3.4+ (async Telegram bot)
  - litellm 1.57+ (LLM routing)
  - Python 3.11+, asyncio-first
  - Supabase (database)
  - SQLite/legion.db (ephemeral state)
- **Purpose**: Primary AI assistant interface via Telegram
- **Key Files**:
  - `main.py` — Bot startup
  - `agents.py` — Agent registry (76+ agents)
  - `llm_client.py` — LLM calls
  - `core/` — Agent orchestration, intent routing, memory, soul engine
  - `handlers/` — 45+ aiogram router files
  - `tools/` — 72 tool modules
  - `config/` — YAML configs for models, departments

#### 2. cekwajar
- **Type**: Indonesian payroll tax calculator (PPh 21, BPJS, lembur, THR, pesangon)
- **Location**: Not found in swarm-bot repo
- **Expected**: Separate Next.js/TypeScript project
- **Status**: Source code NOT present in this extraction
- **Domain**: cekwajar.id

#### 3. popw-protocol
- **Type**: Computer vision / point-of-work protocol research
- **Location**: `/home/newadmin/Documents/popw-protocol/`
- **Content Found**: COCO dataset only (no model code)
- **Expected Architecture**: FiLM, ResNet, FPN
- **Status**: Research code NOT present

#### 4. rumahlabuh
- **Type**: Villa/booking management system
- **Location**: `/home/newadmin/swarm-bot/wiki/rumahlabuh/` (wiki only)
- **Tech Evidence**: Supabase backend, CrewAI integration
- **Domain**: rumahlabuh.com
- **Status**: Design system NOT present

---

## Technical Architecture Summary

### SwarmBot Model Strategy
```
Paid (only): MiniMax M2.7
Free Cloud: Groq, Cerebras, Gemini, OpenRouter, ZAI
Local (vision only): Ollama gemma4:e4b (RTX 3060)
```

### SwarmBot Agent Departments
1. Engineering (12+ agents)
2. Design
3. Research
4. Marketing
5. Operations
6. Product
7. Legal Compliance
8. Creative
9. Vision/Multimodal
10. Nexus/Strategy

### Key Integrations
- **Supabase**: Primary database for SwarmBot and rumahlabuh
- **Telegram**: Primary interface
- **Screenpipe**: Activity monitoring
- **RAGFlow/ChromaDB**: Knowledge retrieval
- **CrewAI**: Multi-agent orchestration for rumahlabuh tasks

---

## Consequences

### Positive
- Unified agent system across multiple domains
- Free-tier cost optimization
- Local privacy for vision tasks

### Negative / Unknowns
- cekwajar source code location unknown
- popw research code not accessible
- rumahlabuh design system not documented

---

## References

- SwarmBot: `/home/newadmin/swarm-bot/`
- cekwajar knowledge: `/home/newadmin/swarm-bot/.wiki/knowledge/cekwajar/` (empty)
- popw: `/home/newadmin/Documents/popw-protocol/` (COCO only)
- rumahlabuh wiki: `/home/newadmin/swarm-bot/wiki/rumahlabuh/` (empty)

---
*Created: 2026-04-11 by @worker*
