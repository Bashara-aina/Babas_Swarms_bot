# Domain Docs Layout

Where domain documentation lives and how skills consume it.

## Single Context (Most Repos)

One global `CONTEXT.md` + `docs/adr/` at repo root.

```
repo/
├── CONTEXT.md              # Project-wide domain glossary
├── docs/
│   └── adr/                # Architecture Decision Records
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

**Skills read:**
- `CONTEXT.md` — domain glossary for `diagnose`, `improve-codebase-architecture`, `tdd`
- `docs/adr/*.md` — past decisions for `improve-codebase-architecture`, `triage`

## Multi-Context (Monorepos)

`CONTEXT-MAP.md` at root pointing to per-context documentation.

```
repo/
├── CONTEXT-MAP.md           # Points to each context
├── docs/
│   └── adr/                # System-wide ADRs only
└── src/
    ├── ordering/
    │   ├── CONTEXT.md        # Ordering context glossary
    │   └── docs/adr/         # Ordering-specific ADRs
    └── billing/
        ├── CONTEXT.md        # Billing context glossary
        └── docs/adr/         # Billing-specific ADRs
```

**CONTEXT-MAP.md format:**

```markdown
# Context Map

| Context | Location |
|---------|----------|
| ordering | src/ordering/CONTEXT.md |
| billing | src/billing/CONTEXT.md |
```

## What Skills Need

### CONTEXT.md Contains
- Domain term definitions (meaningful to domain experts)
- NOT implementation details
- NOT type signatures or file paths

### ADR Format
- Numbered sequentially (0001, 0002, ...)
- Contains: Context, Decision, Alternatives, Consequences
- Written when decision is made, not after

## Skills Consuming These

| Skill | Reads |
|-------|-------|
| `diagnose` | `CONTEXT.md` + relevant ADRs |
| `improve-codebase-architecture` | `CONTEXT.md` + all ADRs |
| `tdd` | `CONTEXT.md` for vocabulary |
| `triage` | ADRs for context on past decisions |