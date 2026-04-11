# Self-Knowledge Extraction Plan
> Created: 2026-04-11 | Planner: Bashara

## Repo Locations (Verified)
| Alias | Repo Name | Actual Path |
|-------|-----------|-------------|
| cekwajar | slip_cekwajar_id | `~/swarm-bot/.wiki/knowledge/cekwajar/` (extracted wiki) |
| legion | Babas_Swarms_bot | `~/swarm-bot/` (self) |
| popw | popw-protocol | `~/Documents/popw-protocol/` |
| rumahlabuh | v0-labuh-booking-design | `~/swarm-bot/wiki/rumahlabuh/` |

---

## STAGE 0: SETUP
| Subtask | Description | Worker | Output |
|---------|-------------|--------|--------|
| S0-1 | Create `WIKI_ROOT=~/swarm-bot/.wiki/self-knowledge/` with subdirs: cekwajar/, legion/, popw/, rumahlabuh/, shared/, architecture/ | @worker | Directory structure created |
| S0-2 | Create `EXTRACTION_LOG.md` with task checklist | @worker | Tracking file |

**S0-1 → S0-2 (sequential, S0-2 depends on S0-1)**

---

## STAGE 1: cekwajar Extraction
| Subtask | Description | Worker | Output |
|---------|-------------|--------|--------|
| S1A | Extract business logic formulas (PPh 21, BPJS, lembur calculations) from TypeScript code | @worker | `cekwajar/formulas.md` |
| S1B | Extract all API routes from app/api/ with auth, tables, methods | @worker | `cekwajar/api-routes.md` |
| S1C | Extract Supabase migrations (tables, RLS policies, functions) | @worker | `cekwajar/supabase-schema.md` |
| S1D | Extract all env vars and their usage | @worker | `cekwajar/env-vars.md` |
| S1E | Extract hardcoded constants and magic numbers | @worker | `cekwajar/constants.md` |
| S1F | Extract git commit history as narrative | @worker | `cekwajar/git-history.md` |
| S1G | Extract all prompt/context files | @worker | `cekwajar/prompts.md` |

**S1A-S1G: Can run IN PARALLEL (all read-only extraction from different source areas)**

---

## STAGE 2: Legion Extraction
| Subtask | Description | Worker | Output |
|---------|-------------|--------|--------|
| S2A | Extract bot commands and agent architecture | @worker | `legion/bot-commands.md`, `legion/agent-architecture.md` |
| S2B | Extract all tool definitions/capabilities | @worker | `legion/tool-definitions.md` |
| S2C | Extract git history as operational log | @worker | `legion/git-history.md` |
| S2D | Extract configuration (models, costs, rate limits) | @worker | `legion/config.md` |

**S2A-S2D: Can run IN PARALLEL (all read-only extraction)**

---

## STAGE 3: popw-protocol Extraction
| Subtask | Description | Worker | Output |
|---------|-------------|--------|--------|
| S3A | Extract model architecture (FiLM, ResNet, FPN classes, hyperparameters) | @worker | `popw/model-architecture.md` |
| S3B | Extract experiment results from JSON/logs | @worker | `popw/experiment-results.md` |

**S3A and S3B: Can run IN PARALLEL**

---

## STAGE 4: rumahlabuh Extraction
| Subtask | Description | Worker | Output |
|---------|-------------|--------|--------|
| S4A | Extract design system, components, and rental domain logic | @worker | `rumahlabuh/design-system.md` |
| S4B | Extract API structure and booking flow | @worker | `rumahlabuh/booking-flow.md` |

**S4A and S4B: Can run IN PARALLEL**

---

## STAGE 5: CROSS-REPO ANALYSIS
| Subtask | Description | Worker | Output |
|---------|-------------|--------|--------|
| S5A | Build master ADR across all repos (shared patterns, architectural decisions) | @reviewer | `decisions/ADR-SELF-KNOWLEDGE-001.md` |
| S5B | Generate cross-repo patterns (env vars, auth patterns, error handling) | @worker | `shared/cross-repo-patterns.md` |

**S5A → S5B (S5B depends on S5A review)**

---

## STAGE 6: GENERATE INDEX
| Subtask | Description | Worker | Output |
|---------|-------------|--------|--------|
| S6A | Count all wiki pages created, generate `INDEX.md` | @worker | `self-knowledge/INDEX.md` |

---

## STAGE 7: COMMIT
| Subtask | Description | Worker | Output |
|---------|-------------|--------|--------|
| S7A | Git add + commit all `.wiki/self-knowledge/` changes | @worker | Committed changes |

---

## EXECUTION SEQUENCE (Dependency Graph)

```
S0-1 → S0-2
         ↓
[S1A][S1B][S1C][S1D][S1E][S1F][S1G]  ← PARALLEL
[S2A][S2B][S2C][S2D]                  ← PARALLEL
[S3A][S3B]                            ← PARALLEL
[S4A][S4B]                            ← PARALLEL
         ↓
        S5A (reviewer)
         ↓
        S5B
         ↓
        S6A
         ↓
        S7A
```

## Parallel Groups
- **PARALLEL GROUP 1**: S1A, S1B, S1C, S1D, S1E, S1F, S1G, S2A, S2B, S2C, S2D, S3A, S3B, S4A, S4B

## Key Source Files Per Repo

### cekwajar
- Source: `~/swarm-bot/.wiki/knowledge/cekwajar/` (already extracted)
- Also check: `~/swarm-bot/wiki/` for original design docs

### legion
- Source: `~/swarm-bot/` root files (main.py, agents.py, handlers/, core/, tools/, config/)
- Git log: `git log --oneline`

### popw
- Source: `~/Documents/popw-protocol/datasets/` (structure TBD)
- Check for: model code, configs, experiment logs

### rumahlabuh
- Source: `~/swarm-bot/wiki/rumahlabuh/`
- Check for: design files, component specs

---

## Progress Tracking
- Update: `~/.wiki/logs/active-tasks.md` after each subtask completion
- Final report: `EXTRACTION_LOG.md`
