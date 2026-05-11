# Brain Dump — obsidian-mind /om-dump

## What It Does

Takes freeform input about anything (decisions, meetings, wins, blockers) and routes each piece to the right vault note.

The user talks about their day. The agent:
1. Classifies each piece of information
2. Updates or creates the appropriate notes
3. Links notes together via wikilinks
4. Confirms what was filed

## When to Use

After a meeting, a decision, an incident, or any significant conversation.

## Input Format

```
/om-dump Just had a 1:1 with Sarah. She's happy with the auth work but wants
us to add error monitoring before release. Also, Tom mentioned the cache
migration is deferred to Q2. Decision: defer Redis migration. Win: Sarah
praised the auth architecture.
```

## Expected Actions

Given the above input, the agent should:

1. **1:1 Update** → Created/updated `work/1-1/Sarah YYYY-MM-DD.md`
2. **Decision Record** → Created `brain/Key Decisions/YYYY-MM-DD-defer-redis-migration.md`
3. **Work Update** → Updated `work/active/Auth Refactor.md` with error monitoring task
4. **Brag Entry** → Added to `perf/Brag Doc.md`: "Auth architecture praised by Sarah"
5. **Confirmation** → Listed all notes updated/created

## Classification Rules

| Content Type | Route To |
|-------------|----------|
| Decision made | brain/Key Decisions/ |
| 1:1 meeting | work/1-1/ |
| Win/praise | perf/Brag Doc.md |
| Blocker | brain/North Star.md (blockers section) or work/active/ |
| Technical learning | brain/Patterns.md |
| Mistake/gotcha | brain/Gotchas.md |
| Person mentioned | org/people/[Name].md |
| Incident | work/incidents/ |

## Notes for Claude

- Always create decision records with the full template
- Link new notes to existing related notes
- Update indexes (Memories.md) when adding new topics
- Never discard information — if unsure where to file, create a new note in thinking/ and route later
