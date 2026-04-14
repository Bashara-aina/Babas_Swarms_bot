---
title: Readme
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- readme.md
created: '2026-04-14'
updated: '2026-04-14'
summary: '> Powered by OpenCode + MiniMax M2.7 + Obsidian | Karpathy LLM Wiki Method'
wikilinks: []
confidence: medium
source: research
---
# SwarmBot Master Wiki
> Powered by OpenCode + MiniMax M2.7 + Obsidian | Karpathy LLM Wiki Method

## 🗂 Structure
- [[architecture]] — System design, diagrams, data flow
- [[agents]] — Each agent's role, model, prompt, status
- [[prompts]] — Master prompts and templates
- [[logs]] — Agent session logs and decisions
- [[research]] — External research, benchmarks, papers
- [[issues]] — Known bugs, blockers, open questions
- [[decisions]] — Architecture decision records (ADRs)

## 🤖 Active Agents
| Agent | Model | Role | Status |
|-------|-------|------|--------|
| Planner | MiniMax M2.7 | Orchestration | Active |
| Worker-1 | MiniMax M2.7 | Code execution | Active |
| Worker-2 | MiniMax M2.7 | Research | Active |
| Guard | MiniMax M2.7 | Safety & review | Active |

## 📡 Quick Commands
- Search wiki: `rg "keyword" ~/swarm-bot/.wiki`
- Open session: `cd ~/swarm-bot && opencode`
- Check GitHub: `gh repo view`