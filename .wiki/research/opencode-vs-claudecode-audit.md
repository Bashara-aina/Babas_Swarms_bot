# OpenCode vs Claude Code — Feature Gap Audit

**Date:** 2026-04-15
**Author:** Bashara / Legion
**Purpose:** Make .opencode/ as intelligent and capable as Claude Code

---

## Executive Summary

.opencode/ has a solid multi-agent contract architecture but lacks the infrastructure substrate that makes Claude Code genuinely powerful. This audit maps every capability gap and prioritizes fixes.

**Key insight:** OpenCode.ai is a multi-agent *framework*. Claude Code is a full AI development *environment* with persistent memory, interactive collaboration, live tool access, and ecosystem integrations. Closing the gap requires adding infrastructure layers, not replacing agents.

---

## Capability Map

### 1. Tool Integration

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| Bash execution | ✅ native | ✅ allowed (worker/reviewer) | None |
| File read | ✅ native | ❌ denied (worker: no read tool) | Major — agents can't read files |
| File write | ✅ native | ✅ only worker | Partial |
| Web search | ✅ WebSearch MCP | ❌ none | Major |
| Web fetch | ✅ WebFetch MCP | ❌ none | Major |
| Glob/grep | ✅ native | ❌ none | Major |
| Git operations | ✅ native (MCP) | ❌ denied everywhere | Major |
| File watching | ✅ watcher config | ❌ none | Major |
| Task management | ✅ CronCreate/List/Delete | ❌ none | Major |
| Interactive prompts | ✅ AskUserQuestion | ❌ none | Major |
| Plan mode | ✅ EnterPlanMode | ❌ none | Major |

**Priority fix:** OpenCode.ai tool permissions are too restrictive. Agents need Glob, Grep, Read at minimum. The `focused-implementer.md` has `bash: false` — this prevents it from even running `ls`. Fix: change to `bash: allow` for read-only tools, or add `read: allow` equivalent.

### 2. Agent System

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| Subagent spawning | ✅ Agent tool (general-purpose, Explore, Plan, etc.) | ❌ no spawning mechanism | Major |
| Agent isolation | ✅ worktree mode | ❌ none | Major |
| Background agents | ✅ run_in_background | ❌ none | Major |
| Agent continuation | ✅ SendMessage to existing agent | ❌ stateless | Major |
| Specialized agent types | ✅ 20+ built-in types | ❌ none (flat list) | Major |

**Priority fix:** OpenCode.ai agents are prompt definitions only — they don't actually get instantiated. The framework runs one agent at a time. Adding a proper spawn mechanism is the biggest gap.

### 3. Memory & Persistence

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| Cross-session memory | ✅ MEMORY.md system | ❌ none | Major |
| Project memory | ✅ project/*.md | ❌ none | Major |
| User memory | ✅ user/*.md | ❌ none | Major |
| Feedback memory | ✅ feedback/*.md | ❌ none | Major |
| Reference memory | ✅ reference/*.md | ❌ none | Major |
| Per-conversation memory | ✅ .remember/ buffer | ❌ none | Major |
| Memory search | ✅ on user request | ❌ none | Major |

**Priority fix:** Add a memory layer to .opencode/. This is the single biggest missing piece for making agents "remember" across sessions. Could be implemented as a `memory.md` agent that reads/writes to a `.opencode/memory/` directory.

### 4. Interactive Collaboration

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| AskUserQuestion | ✅ structured multi-choice | ❌ none | Major |
| EnterPlanMode | ✅ architecture planning | ❌ none | Major |
| ExitPlanMode | ✅ user approval | ❌ none | Major |
| Confirmation prompts | ✅ destructive ops | ❌ none | Major |
| Skill invocation | ✅ Skill tool with dynamic loading | ❌ none | Major |

**Priority fix:** OpenCode.ai has no user interaction mechanism. The swarm pipeline assumes fully autonomous execution. This needs a `collaborator.md` agent that can:
- Pause pipeline and ask user a question
- Present options for user to choose
- Request plan approval before proceeding

### 5. MCP Ecosystem

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| GitHub MCP | ✅ PR, issues, repo ops | ❌ none | Major |
| AWS Serverless MCP | ✅ SAM, Lambda, ESM | ❌ none | Major |
| AWS Pricing MCP | ✅ cost analysis | ❌ none | Major |
| MongoDB MCP | ✅ database ops | ❌ none | Major |
| Chrome DevTools MCP | ✅ browser control | ❌ none | Major |
| Playwright MCP | ✅ browser automation | ❌ none | Major |
| Firebase MCP | ✅ Firebase ops | ❌ none | Major |
| Pinecone MCP | ✅ vector search | ❌ none | Major |
| Context7 MCP | ✅ library docs | ❌ none | Major |
| Microsoft Learn MCP | ✅ docs search | ❌ none | Major |
| Prisma MCP | ✅ migrations | ❌ none | Major |
| Deploy-on-AWS MCP | ✅ CloudFormation/CDK | ❌ none | Major |
| Spotify Ads MCP | ✅ ad management | ❌ none | Major |
| Gmail/Calendar MCP | ✅ email/calendar | ❌ none | Major |
| Notion MCP | ✅ Notion integration | ❌ none | Major |

**Priority fix:** OpenCode.ai MCP server support is unknown. Check if the framework can connect to external MCP servers. If not, this is a fundamental architectural gap. If yes, need documentation on how to configure MCP connections.

### 6. Code Intelligence

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| LSP go-to-definition | ✅ native | ❌ none | Major |
| LSP find-references | ✅ native | ❌ none | Major |
| LSP hover | ✅ type/doc info | ❌ none | Major |
| LSP document symbols | ✅ native | ❌ none | Major |
| LSP workspace symbols | ✅ native | ❌ none | Major |
| Code review agents | ✅ 10+ pr-review-toolkit agents | ❌ basic reviewer only | Major |
| Type design analyzer | ✅ pr-review-toolkit | ❌ none | Major |
| Comment analyzer | ✅ pr-review-toolkit | ❌ none | Major |
| Silent failure hunter | ✅ pr-review-toolkit | ❌ none | Major |
| Test coverage analyzer | ✅ pr-review-toolkit | ❌ none | Major |
| Code simplifier | ✅ code-simplifier agent | ❌ none | Major |

**Priority fix:** The `pr-review-toolkit/` agents are specialized reviewers (code-reviewer, comment-analyzer, type-design-analyzer, etc.) that do deep analysis. .opencode/ has one flat `reviewer.md` that does everything at a shallow level.

### 7. Skills System

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| Skill invocation | ✅ Skill tool | ❌ none | Major |
| Skill loading | ✅ dynamic from plugins | ❌ none | Major |
| Skill reviewer | ✅ plugin-dev:skill-reviewer | ❌ none | Major |
| Built-in skills | ✅ 20+ (TDD, brainstorming, etc.) | ❌ none | Major |
| Skill type: rigid | ✅ TDD, debugging strict enforcement | ❌ none | Major |
| Skill type: flexible | ✅ patterns | ❌ none | Major |

**Priority fix:** OpenCode.ai has no skill system equivalent. Need to add:
1. A `skills/` directory with prompt-based skills
2. A `skill-loader.md` agent that loads skills dynamically
3. A skill quality reviewer

### 8. Planning & Architecture

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| EnterPlanMode | ✅ full codebase exploration | ❌ none | Major |
| Feature architect agent | ✅ feature-dev:code-architect | ❌ none | Major |
| Code explorer agent | ✅ feature-dev:code-explorer | ❌ none | Major |
| Code reviewer agent | ✅ feature-dev:code-reviewer | ❌ none | Major |
| Architecture blueprints | ✅ implementation plans | ❌ none | Major |

**Priority fix:** The `/research` command exists but it's just a prompt template, not a planning mode. Add a proper `EnterPlanMode` equivalent with:
1. Codebase exploration agent
2. Architecture design agent
3. Implementation planning agent

### 9. Deployment & Infrastructure

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| AWS SAM build/deploy | ✅ aws-serverless-mcp | ❌ none | Major |
| SAM local invoke | ✅ aws-serverless-mcp | ❌ none | Major |
| CloudFormation validation | ✅ awsiac | ❌ none | Major |
| CDK documentation | ✅ awsiac search | ❌ none | Major |
| Deployment guidance | ✅ aws-serverless-mcp | ❌ none | Major |
| ESM optimization | ✅ aws-serverless-mcp | ❌ none | Major |

**Priority fix:** OpenCode.ai has a `/deploy` command but no AWS integration. The deploy command just runs shell commands. Need MCP-backed deployment with proper validation and rollback.

### 10. Database & Storage

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| MongoDB operations | ✅ mongodb-mcp | ❌ none | Major |
| Pinecone vector ops | ✅ pinecone-mcp | ❌ none | Major |
| Prisma migrations | ✅ prisma-mcp | ❌ none | Major |
| PlanetScale | ✅ planetscale-mcp (OAuth) | ❌ none | Major |

**Priority fix:** OpenCode.ai has no database integrations at all. This is a complete gap.

### 11. Browser & Web Automation

| Capability | Claude Code | .opencode/ | Gap |
|------------|-------------|------------|-----|
| Chrome DevTools | ✅ chrome-devtools-mcp | ❌ none | Major |
| Playwright | ✅ playwright-mcp | ❌ browser-use only | Major |
| Browser snapshots | ✅ accessibility tree | ❌ none | Major |
| Screenshot | ✅ full page/element | ❌ none | Major |
| Network monitoring | ✅ requests/console | ❌ none | Major |
| Performance tracing | ✅ Lighthouse/trace | ❌ none | Major |

**Priority fix:** .opencode/ uses `browser-use` as a tool but has no dedicated browser agent equivalent. The `computer_agent/` in swarm-bot does this but OpenCode.ai has no browser automation agent.

---

## Missing Agents (Priority Order)

### P0 — Bot-Breaking Gaps

1. **`agent/memory.md`** — Cross-session memory agent
   - Reads/writes `.opencode/memory/` directory
   - Implements MEMORY.md index pattern
   - Types: project, user, feedback, reference

2. **`agent/collaborator.md`** — Interactive user collaboration
   - Pauses pipeline for user input
   - Presents structured choices via AskUserQuestion pattern
   - Requests plan approval

3. **`agent/planner-enhanced.md`** — Enhanced planner with EnterPlanMode equivalent
   - Uses Explore agent to research before planning
   - Writes architecture blueprints
   - Gets user approval before spawning workers

### P1 — Reliability Gaps

4. **`agent/lsp-reader.md`** — LSP integration reader
   - go-to-definition, find-references, hover
   - Read-only, no modifications

5. **`agents/review/code-reviewer.md`** — Deep code review
   - Bug detection, logic errors, security
   - Style enforcement

6. **`agents/review/test-analyzer.md`** — Test coverage analysis
   - PR test completeness review
   - Gap identification

7. **`agents/review/comment-analyzer.md`** — Comment/docstring audit
   - Accuracy, completeness, technical debt

### P2 — Ecosystem Gaps

8. **`agents/mcp/github-agent.md`** — GitHub operations
   - PR creation, review, merge
   - Issue management
   - Repo operations

9. **`agents/mcp/aws-agent.md`** — AWS operations
   - SAM deploy/validate
   - CloudFormation operations
   - Cost analysis

10. **`agents/mcp/mongodb-agent.md`** — MongoDB operations
    - CRUD operations
    - Aggregation pipelines

11. **`agents/mcp/browser-agent.md`** — Browser automation
    - Playwright-based
    - Screenshot, navigation, form fill

### P3 — Quality Gaps

12. **`agents/review/type-design-analyzer.md`** — Type design review
    - Invariant expression
    - Encapsulation analysis

13. **`agents/review/silent-failure-hunter.md`** — Error handling audit
    - Silent failure detection
    - Fallback behavior analysis

14. **`agents/skill/skill-reviewer.md`** — Skill quality review
    - Quality scoring
    - Best practice enforcement

15. **`agents/skill/skill-creator.md`** — Skill generation
    - Creates new skills from descriptions
    - Follows skill template

---

## Commands to Add

| Command | Description | Priority |
|---------|-------------|----------|
| `/plan` | Enter plan mode with codebase exploration | P0 |
| `/review` | Deep code review with specialized sub-agents | P1 |
| `/memory` | Query/add cross-session memory | P0 |
| `/aws` | AWS operations (SAM, CFN, CDK) | P2 |
| `/mcp` | MongoDB, GitHub, browser operations | P2 |
| `/skill` | Create/manage skills | P3 |
| `/test-coverage` | Analyze test coverage | P1 |

---

## Anti-Hallucination Gap Analysis

.opencode/ already has strong anti-hallucination rules. How they compare:

| Rule | Claude Code | .opencode/ | Verdict |
|------|-------------|------------|---------|
| Evidence over statements | ✅ implicit | ✅ explicit (The One Law) | .opencode/ wins |
| 0 bytes = failed | ✅ implicit | ✅ explicit | .opencode/ wins |
| No benefit of doubt | ✅ implicit | ✅ explicit | .opencode/ wins |
| Proof required | ✅ implicit | ✅ PROOF_FORMAT mandatory | .opencode/ wins |
| Read before write | ✅ implicit | ✅ Phase A mandatory | .opencode/ wins |
| Contract format | ❌ informal | ✅ CONTRACT format strict | .opencode/ wins |

**Verdict:** .opencode/'s anti-hallucination framework is actually *more rigorous* than Claude Code's. This is an area where .opencode/ should stay as-is.

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (do first)

1. **Fix tool permissions** in all agents — add Glob, Grep, Read, Bash to all agents that need them
2. **Add memory system** — `agent/memory.md` + `.opencode/memory/` directory
3. **Add collaborator** — `agent/collaborator.md` for interactive pauses
4. **Add enhanced planner** — `agent/planner-enhanced.md` with exploration

### Phase 2: Code Intelligence

5. **Add LSP reader** — `agent/lsp-reader.md`
6. **Add specialized reviewers** — `agents/review/` directory with deep review agents
7. **Add code simplifier** — `agent/code-simplifier.md`

### Phase 3: Ecosystem

8. **Add GitHub agent** — `agents/mcp/github-agent.md`
9. **Add AWS agent** — `agents/mcp/aws-agent.md`
10. **Add browser agent** — `agents/mcp/browser-agent.md`
11. **Add database agents** — MongoDB, Pinecone

### Phase 4: Skills & Planning

12. **Add skill system** — `skills/` directory + skill loader
13. **Add plan mode** — proper `EnterPlanMode` equivalent
14. **Add feature architect** — `feature-dev:code-architect` equivalent

---

## Quick Wins (1-hour fixes)

1. **Remove `bash: false`** from focused-implementer.md — it can't even run `ls`
2. **Add `read: allow`** to focused-implementer.md and diff-analyzer.md
3. **Add `glob: allow`** and `grep: allow`** to all research/read-only agents
4. **Add `edit: allow`** to reviewer.md — it needs to write review files
5. **Add model temperature override** to agents that need it (reviewer: 0.0, worker: 0.2)

---

## What NOT to Change

- **CONTRACT format** — it's excellent and well-tested
- **Anti-hallucination rules** — more rigorous than Claude Code's
- **Swarm pipeline flow** — 4-agent loop is sound
- **Task type detection** — STEP 0 classification is good
- **Agent identity separation** — planner/worker/diff-analyzer/reviewer roles are correct

