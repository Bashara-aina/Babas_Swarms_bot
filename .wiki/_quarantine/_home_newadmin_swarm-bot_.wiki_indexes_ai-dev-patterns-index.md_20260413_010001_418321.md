---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/indexes/ai-dev-patterns-index.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:01.418357"
}
---

# AI-Driven Development Patterns Index
Source: ~/swarm-bot/.wiki/research/ai-dev-patterns (README.md — 522 tools)

## Top 20 AI-Driven Development Patterns for Python + Multi-Agent Systems

### 1. Multi-Agent Orchestration Patterns
- **Pattern**: Use orchestrators like LangGraph, CrewAI, AutoGen
- **When**: Complex tasks requiring multiple specialized agents
- **Apply**: Define agent roles, tools, and handoff protocols

### 2. Context Engineering for Agents
- **Pattern**: Systematic optimization of context windows
- **When**: Long-running agent sessions, complex codebases
- **Apply**: Use RAG, context pruning, summarization, external memory

### 3. Iterative Self-Refinement (Self-Refine)
- **Pattern**: Agent critiques and improves own output
- **When**: Code generation, writing tasks
- **Apply**: Add reflection loop: generate → review → improve

### 4. Tool Use with Function Calling
- **Pattern**: LLMs trigger external tools via structured calls
- **When**: Need to interact with APIs, files, databases
- **Apply**: Define JSON schemas, implement handler functions

### 5. ReAct (Reasoning + Acting)
- **Pattern**: Interleave reasoning traces with actions
- **When**: Complex problem-solving, web browsing
- **Apply**: Generate thought → action → observation → repeat

### 6. TDD with AI Agents
- **Pattern**: AI writes tests before implementation
- **When**: Reliable, maintainable code required
- **Apply**: Use shortest or testzeus-hercules for AI test generation

### 7. SWE-Bench Inspired Issue Resolution
- **Pattern**: Autonomous issue-to-PR pipeline
- **When**: Large-scale code maintenance
- **Apply**: Use SWE-agent, OpenHands for autonomous fixing

### 8. Claude Code-Style Background Agents
- **Pattern**: Parallel async agent execution
- **When**: Multiple independent tasks
- **Apply**: Use opencode-background-agents plugin

### 9. Memory-Augmented Agents
- **Pattern**: Persistent context across sessions
- **When**: Long-term projects, learning systems
- **Apply**: Use Mem0, simple-memory, or opencode-mem

### 10. Model Context Protocol (MCP)
- **Pattern**: Standardized tool/context sharing
- **When**: Multi-agent systems, tool interoperability
- **Apply**: Implement MCP servers for GitHub, databases, etc.

### 11. Chain of Thought with Tree Search
- **Pattern**: Explore multiple reasoning paths
- **When**: Complex decision making
- **Apply**: Use Tree of Thoughts, beam search over reasoning

### 12. Spec-Driven Development
- **Pattern**: Write specs first, AI implements
- **When**: Complex features, clear requirements
- **Apply**: Use Kiro, OpenSpec for spec-first workflow

### 13. Git-Aware Agent Workflows
- **Pattern**: Agent understands git history and context
- **When**: Code review, feature development
- **Apply**: Use aider, gitingest for git-native coding

### 14. Parallel Agent Sprint
- **Pattern**: Multiple agents work on sub-tasks simultaneously
- **When**: Time-critical features, independent work items
- **Apply**: Use Claude Squad, orchestr8, or opencode-workspace

### 15. Human-in-the-Loop Guardrails
- **Pattern**: Human approval for destructive/critical actions
- **When**: Production systems, security-sensitive operations
- **Apply**: Implement approval gates, use Zenable for guardrails

### 16. Token-Efficient Context Management
- **Pattern**: Compress, prune, and optimize context
- **When**: Long sessions, expensive API calls
- **Apply**: Use opencode-snip (60-90% reduction), context pruning

### 17. Swarm Intelligence for Agents
- **Pattern**: Emergent behavior from simple agent interactions
- **When**: Complex optimization, creative tasks
- **Apply**: Use opencode-swarm-plugin for swarm coordination

### 18. RAG-Augmented Codebase Context
- **Pattern**: Retrieve relevant code snippets for context
- **When**: Large codebases, unfamiliar code
- **Apply**: Use Context7 MCP, claude-context for code search

### 19. Durable Execution for Long Tasks
- **Pattern**: Fault-tolerant task execution with persistence
- **When**: Long-running workflows, potential failures
- **Apply**: Use Temporal for durable agent workflows

### 20. Security-First AI Coding
- **Pattern**: Continuous security scanning in AI workflow
- **When**: Production code, sensitive data
- **Apply**: Use Snyk Code, Guardrails AI, codegate

## Top 10 Testing Patterns
1. **AI-Generated Tests**: shortest, testzeus-hercules, qodo-cover
2. **Mutation Testing**: mutahunter for AI-generated code validation
3. **TDD Guard**: tdd-guard for automated TDD enforcement
4. **Visual Testing**: arbigent for multi-platform UI testing
5. **Security Scanning**: HexStrike, VulnViper in CI pipeline
6. **Code Quality**: Zenable guardrails for team standards
7. **VibeLint**: Make codebases LLM-friendly
8. **Vet Verification**: Standalone verification for agent outputs
9. **Hawkeye**: Observability for AI agent sessions
10. **Eval Marketplace**: Security evaluation for MCP servers

## Key Multi-Agent Frameworks for Python
| Framework | Best For | Stars |
|-----------|----------|-------|
| LangGraph | Graph-based orchestration | 30k+ |
| CrewAI | Role-based agents | 25k+ |
| AutoGen | Microsoft multi-agent | 35k+ |
| MetaGPT | Software company sim | 40k+ |
| Mastra | TypeScript-first | Growing |
| DSPy | Programming not prompting | 30k+ |
