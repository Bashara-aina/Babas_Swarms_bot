---
title: dify
type: entity
status: active
tags: [agent, workflow, no-code, llm-apps]
created: 2026-04-13
updated: 2026-04-13
summary: Dify is an open-source LLM app development platform enabling workflow orchestration, agent creation, and RAG pipelines.
wikilinks:
  - [[./entities/opencode]]
  - [[./concepts/skill-registry]]
confidence: medium
source: research
---

# Dify

## TL;DR
Dify is an open-source platform for building LLM applications with visual workflows, agent orchestration, and RAG capabilities.

## Features

| Feature | Description |
|---------|-------------|
| Workflows | Visual node-based orchestration |
| Agents | Tool-augmented LLM agents |
| RAG | Document ingestion and retrieval |
| Datasets | Knowledge base management |

## Comparison with Alternatives

| Platform | Dify | langchain | Semantic Kernel |
|----------|------|-----------|-----------------|
| UI | Visual | Code-only | Code-only |
| Open source | ✅ | ✅ | ✅ (Microsoft) |
| Self-hosted | ✅ | ✅ | ❌ |

## Potential Use Cases for Legion

- **Rapid prototyping**: Visual workflow builder for new skill pipelines
- **Business automation**: cekwajar salary survey processing workflows
- **RAG pipelines**: Dify datasets for rumahlabuh property Q&A

## Integration with Legion

Dify is not currently integrated — it was evaluated as a potential skill execution platform. Current skill execution uses `core/skills/` (Python functions) and the intent router. Dify could replace the skill registry for visual workflow-based skills.

Status: **Not integrated** — evaluated but not selected. Could be revisited if workflow complexity grows.

## Related Pages

- [[./entities/opencode]] — Code agent alternative
- [[./concepts/skill-registry]] — Current skill management system
- [[cekwajar-id]] — Potential workflow automation target
