---
title: Mcp Servers Available
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- tools
created: '2026-04-14'
updated: '2026-04-14'
summary: '**MCP (Model Context Protocol)** is the open standard that enables AI models
  to connect to external tools and data sources. Think of it as "USB-C for AI" — a
  standardized interface between the LLM ...'
wikilinks: []
confidence: medium
source: research
---
**MCP (Model Context Protocol)** is the open standard that enables AI models to connect to external tools and data sources. Think of it as "USB-C for AI" — a standardized interface between the LLM and the tools it needs.

For Legion, the key value is: **Legion can self-install MCP servers on demand** to gain new capabilities without manual setup.
---


## 2. Memory Servers

Servers that provide persistent memory and context management for agents.

### 2.1 Memory-Bank
- **What it does**: Long-term memory for AI assistants — stores user preferences, conversation history, learned facts
- **When Legion uses it**: To remember Bashara's preferences across sessions (e.g., preferred language, recurring task patterns)
- **Install**: `pip install memory-bank` or via MCP registry

### 2.2 Mem0 Server
- **What it does**: Universal memory layer with +26% accuracy over OpenAI Memory on LOCOMO benchmark
- **When Legion uses it**: Cross-session memory for user (Bashara) + session memory for each Telegram conversation
- **Install**: Self-hosted via `pip install mem0ai` or use hosted platform at app.mem0.ai
- **Note**: Already referenced in MEMORY-ARCHITECTURE-GUIDE.md

### 2.3 Zep Memory Server
- **What it does**: Temporal knowledge graph + memory for AI agents
- **When Legion uses it**: Build a knowledge graph of Bashara's life context (projects, appointments, relationships)
- **Install**: Docker or self-hosted; `zep pull` for the server

### 2.4 Letta Server
- **What it does**: Stateful agent memory with memory blocks; Obsidian plugin for vault sync
- **When Legion uses it**: Deep integration with Obsidian vault (`.wiki/`) for knowledge management
- **Install**: Self-hosted via `pip install letta` or use letta cloud

---

## 3. Search Servers

### 3.1 Web Search

| Server | What it does | Install |
|--------|--------------|---------|
| **DuckDuckGo Search** | Web search via DuckDuckGo | `npx duckduckgo-mcp-server` |
| **Google Search** | Web search via Google API | Via Composio or custom |
| **SerpAPI** | Real-time Google/YouTube/Amazon search | Already in `skills/web_search.py` |
| **Bing Search** | Microsoft Bing search API | Via MCP registry |
| **Exa Search** | Semantic web search for AI agents | `pip install exa-python` |

**Legion priority**: DuckDuckGo (already has duckduckgo-search in requirements.txt) — no API key needed

### 3.2 Code Search

| Server | What it does | Install |
|--------|--------------|---------|
| **GitHub Search** | Search repos, code, issues, PRs | `npx @modelcontextprotocol/server-github` |
| **Sourcegraph** | Semantic code search across all repos | Via Sourcegraph MCP |
| **Search Code** | Natural language code search | Via RegFF or custom |

**Legion priority**: GitHub MCP server — enables searching Bashara's repos and open-source code

### 3.3 Document Search

| Server | What it does | Install |
|--------|--------------|---------|
| **Notion** | Search Notion pages and databases | `npx notion-mcp-server` |
| **Obsidian** | Search vault contents | Via Letta Obsidian plugin |
| **Google Drive** | Search Drive documents | Via Google Drive MCP |

**Legion priority**: Obsidian/Letta — already uses `.wiki/` which is an Obsidian vault

---

## 4. Data Servers

### 4.1 Database

| Server | What it does | Install |
|--------|--------------|---------|
| **PostgreSQL** | Direct SQL queries on Postgres | `npx @modelcontextprotocol/server-postgres` |
| **Supabase** | PostgreSQL + real-time + auth | Already has `skills/database_agent.py` |
| **SQLite** | Local database queries | `npx @modelcontextprotocol/server-sqlite` |
| **MongoDB** | NoSQL document queries | Via MCP registry |
| **MySQL** | Relational DB queries | Via MCP registry |
| **AnyQuery** | Query 40+ apps via SQL | `npx anyquery` — local-first, private |

**Legion priority**: Supabase (already integrated via `DatabaseAgent`) — add MCP for direct SQL access

### 4.2 Spreadsheet

| Server | What it does | Install |
|--------|--------------|---------|
| **Google Sheets** | Read/write/append rows | Via Composio or `npx sheets-mcp` |
| **Airtable** | Query and update Airtable bases | Via Composio |
| **Excel** | Local Excel file operations | Via custom MCP |

**Legion priority**: Google Sheets — for tracking thesis progress, business metrics

### 4.3 API Connectors

| Server | What it does | Install |
|--------|--------------|---------|
| **REST API** | Generic REST API → MCP | `npx APIFold` (18 free public servers) |
| **Pipedream** | Connect 2500+ APIs | Via `npx @pipedream/mcp-server` |
| **MindsDB** | Connect and unify data across platforms | `pip install mindsdb` |

---

## 5. Communication Servers

### 5.1 Email

| Server | What it does | Install |
|--------|--------------|---------|
| **Gmail** | Send, read, search emails | `npx gmail-mcp-server` |
| **Outlook** | Microsoft email | Via Composio |
| ** SMTP** | Send emails via any SMTP provider | Via custom MCP |

**Legion priority**: Gmail — for sending booking confirmations, invoice notifications

### 5.2 Calendar

| Server | What it does | Install |
|--------|--------------|---------|
| **Google Calendar** | Read/write events | Via Composio or custom |
| **Cal.com** | Scheduling and availability | `npx calcom-mcp` |
| **Notion Calendar** | Calendar inside Notion | Via Notion MCP |

**Legion priority**: Google Calendar — for managing thesis zemi, appointments

### 5.3 Messaging

| Server | What it does | Install |
|--------|--------------|---------|
| **Slack** | Post messages, search history | `npx @modelcontextprotocol/server-slack` |
| **WhatsApp** | Send/receive WhatsApp messages | `npx whatsapp-mcp-server` |
| **Telegram** | (Legion already uses this natively) | N/A — core platform |

**Legion priority**: WhatsApp — for connecting with Haniyah; Slack for potential team comms

### 5.4 WhatsApp MCP Servers

| Server | Stars | What it does |
|--------|-------|--------------|
| [VARSL/shared-mcp-whatsapp](https://github.com/VARSL/shared-mcp-whatsapp) | 4 | Multi-device WhatsApp integration |
| [vinodsr/mcp-whatsapp](https://github.com/vinodsr/mcp-whatsapp) | 1.3k | Full WhatsApp Web API via Baileys |
| [fr Maggie horizonte](https://github.com/maggie-horowitz) | — | Send/receive with AI responses |
| [kaiz-apple mcp-whatsapp](https://github.com/kaiz-apple/mcp-whatsapp) | — | Baileys-based server |

---

## 6. Code Servers

### 6.1 GitHub

| Server | What it does | Install |
|--------|--------------|---------|
| **GitHub MCP Server** | Repos, issues, PRs, actions, search | `npx @modelcontextprotocol/server-github` |
| **GitHub CLI** | gh commands via MCP | `npx gh-mcp-server` |

**Legion action**: This is already partially available via `tools/github.py` — wrap as MCP for consistency

### 6.2 Git

| Server | What it does | Install |
|--------|--------------|---------|
| **Git MCP Server** | Branch, commit, diff, log | `npx git-mcp-server` |
| **GitLab** | GitLab repos and merge requests | Via GitLab MCP |

### 6.3 CI/CD

| Server | What it does | Install |
|--------|--------------|---------|
| **GitHub Actions** | Trigger and monitor workflows | Via GitHub MCP |
| **Jenkins** | Trigger builds, get status | Via Jenkins MCP |
| **CircleCI** | CI pipeline management | Via CircleCI MCP |

---

## 7. Business Servers

### 7.1 CRM

| Server | What it does | Install |
|--------|--------------|---------|
| **Salesforce** | CRM operations | Via Composio |
| **HubSpot** | CRM + marketing | Via Composio |
| **Pipedream** | 2500+ app integrations | `npx pipedream-mcp` |

### 7.2 Invoicing / Finance

| Server | What it does | Install |
|--------|--------------|---------|
| **Stripe** | Payment processing, invoices | Via Composio |
| **QuickBooks** | Accounting, invoicing | Via Composio |
| **Xero** | Accounting for SMBs | Via MCP registry |

**Legion relevance**: For rumahlabuh.com (booking payments) and cekwajar.id (salary SaaS)

### 7.3 Analytics

| Server | What it does | Install |
|--------|--------------|---------|
| **Google Analytics** | Web analytics data | Via Composio |
| **Mixpanel** | Product analytics | Via MCP registry |
| **Supabase** | Database analytics | Already available |

---

## 8. Media Servers

### 8.1 Screen & Audio

| Server | What it does | Install |
|--------|--------------|---------|
| **Screenpipe** | Continuous screen + audio capture | `brew screenpipe` or Docker |
| **Audio** | Whisper transcription, TTS | Via MCP registry |
| **FFmpeg** | Video/audio processing | Via custom MCP |

**Legion priority**: Screenpipe — for screen awareness, screenshot analysis

### 8.2 Vision & Images

| Server | What it does | Install |
|--------|--------------|---------|
| **OpenAI Image** | DALL-E image generation | Via Composio or custom |
| **Image generation** | Stable Diffusion, etc. | Via image gen MCP |
| **PDF extraction** | Parse PDFs for content | `npx pdf-mcp-server` |

---

## 9. Knowledge Servers

### 9.1 Wikipedia & Research

| Server | What it does | Install |
|--------|--------------|---------|
| **Wikipedia** | Query Wikipedia articles | `npx wikipedia-mcp-server` |
| **arXiv** | Academic paper search | Via MCP registry |
| **PubMed** | Medical/life science papers | Via MCP registry |
| **Semantic Scholar** | Academic paper search + citations | Via MCP registry |

### 9.2 Vector Stores

| Server | What it does | Install |
|--------|--------------|---------|
| **Pinecone** | Managed vector database | Via Pinecone MCP |
| **ChromaDB** | Local vector store | Already in requirements.txt |
| **Qdrant** | Vector similarity search | `docker pull qdrant/qdrant` |
| **Weaviate** | Semantic search engine | Via Docker |

**Legion priority**: ChromaDB (already in requirements.txt) + Qdrant for production

---

## 10. How Legion Can Self-Install MCP Servers

### 10.1 Architecture
```
Legion detects missing capability
  → LLM decides which MCP server to install
  → Legion runs: npx/pip install <server>
  → Server starts as subprocess or via stdio
  → Tool definitions loaded into context
  → Capability available immediately
```

### 10.2 Dynamic Server Manifest
```python
# skills/mcp_servers.json — Legion's known MCP servers
{
  "servers": [
    {
      "name": "github",
      "install": "npx @modelcontextprotocol/server-github",
      "tools": ["search_repos", "get_issue", "create_pr"],
      "description": "GitHub operations"
    },
    {
      "name": "filesystem", 
      "install": "npx @modelcontextprotocol/server-filesystem",
      "tools": ["read_file", "write_file", "list_directory"],
      "description": "File system operations"
    }
  ]
}
```

### 10.3 Self-Install Workflow
1. **Detect**: Tool call fails → capability not available
2. **Decide**: LLM chooses appropriate MCP server from manifest
3. **Install**: `pip install` or `npx` based on server type
4. **Verify**: Run health check on server
5. **Register**: Load tool definitions into active context
6. **Retry**: Re-execute original tool call

---

## 11. Priority MCP Servers for Legion

### Tier 1 — Critical
| Server | Purpose | Install |
|--------|---------|---------|
| **GitHub** | Repo operations, issue management | `npx @modelcontextprotocol/server-github` |
| **filesystem** | `.wiki/` access, project file ops | `npx @modelcontextprotocol/server-filesystem` |
| **Supabase/Postgres** | Database queries | `npx @modelcontextprotocol/server-postgres` |
| **Gmail** | Booking confirmations, notifications | `npx gmail-mcp-server` |

### Tier 2 — High Value
| Server | Purpose | Install |
|--------|---------|---------|
| **Google Calendar** | Schedule management | Via Composio |
| **WhatsApp** | Personal messaging with Hanifah | `npx whatsapp-mcp-server` |
| **Google Sheets** | Thesis progress, business metrics | Via Sheets MCP |
| **Screenpipe** | Screen capture for debugging | `brew screenpipe` |

### Tier 3 — Experimental
| Server | Purpose | Install |
|--------|---------|---------|
| **arxiv** | Thesis literature search | Via MCP registry |
| **Slack** | Team communications | `npx @modelcontextprotocol/server-slack` |
| **Mem0** | Cross-session user memory | `pip install mem0ai` |
| **Letta** | Obsidian vault sync | `pip install letta` |

---

## 12. MCP Server Resources

- **Registry**: [glama.ai/mcp/servers](https://glama.ai/mcp/servers) — searchable directory
- **Discord**: [mcp Discord](https://glama.ai/mcp/discord) — community support
- **Reddit**: [r/mcp](https://www.reddit.com/r/mcp/)
- **State of MCP 2025**: [glama.ai/blog/2025-12-07-the-state-of-mcp-in-2025](https://glama.ai/blog/2025-12-07-the-state-of-mcp-in-2025)
