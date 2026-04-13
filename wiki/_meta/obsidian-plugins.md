# Obsidian Plugins Configuration

## Required Plugins

### Core (bundled with Obsidian)
- **Backlinks** — Shows incoming links to each page
- **Outgoing Links** — Shows outgoing links from page
- **Internal Embed** — uses embed syntax

### Community Plugins (must install)

#### Required
1. **Dataview** (v0.5.64+)
   - Purpose: Query wiki pages inline
   - Source: Community plugins marketplace
   - Required for: `INDEX.md` queries

#### Recommended
2. **Obsidian Git** (v2.x)
   - Purpose: Auto-backup vault to git
   - Source: Community plugins marketplace
   - Config: Set auto-commit interval (5 min)

3. **Metadata Extractor** (v1.x)
   - Purpose: Auto-extract YAML frontmatter
   - Source: Community plugins marketplace

#### Optional
4. **Quick Explorer** — File tree navigation
5. **Advanced Tables** — Table formatting
6. **Paste URL into Selection** — Smart link pasting

## Installation Instructions

### Step 1: Enable Community Plugins
1. Open Obsidian Settings (⚙️)
2. Go to **Community Plugins**
3. Toggle off "Safe Mode" at bottom
4. Click "Browse" to see marketplace

### Step 2: Install Dataview
1. Search "Dataview" in marketplace
2. Click "Install"
3. Click "Enable"

### Step 3: Install Obsidian Git
1. Search "Obsidian Git" in marketplace
2. Install and Enable
3. Go to Settings → Obsidian Git
4. Configure:
   - Auto commit interval: `5` minutes
   - Auto backup interval: `30` minutes
   - Commit message format: `vault backup: {{date}}`

### Step 4: Configure Vault
1. Open vault at `~/swarm-bot/wiki/`
2. Dataview queries will auto-execute
3. Git will auto-backup if configured

## Dataview Query Syntax

### Basic Table
```dataview
TABLE title, status, tags
FROM "wiki/concepts"
WHERE status = "active"
SORT updated DESC
```

### Entity List
```dataview
TABLE title, status
FROM "wiki/entities"
WHERE status = "active"
SORT title ASC
```

### Recent Decisions
```dataview
TABLE title, date(created) as Created
FROM "wiki/decisions"
SORT created DESC
LIMIT 10
```

### Project Overview
```dataview
TABLE title, status, tags
FROM "wiki/projects"
SORT title ASC
```

## Graph View Configuration

Use `graph-config.json` in vault root for node coloring.

## Related Pages

- [[_meta/graph-config.json]] — Graph colors
- [[wiki/INDEX.md]] — Main index with queries
