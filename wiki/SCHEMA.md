# Legion Wiki Schema v1.0

## Rules Legion MUST follow when writing wiki pages:

### Page format:

- Title: # PageName
- Last updated: `_Last updated: YYYY-MM-DD by Legion_`
- Summary: 2-3 sentence TL;DR at the top
- Body: structured with ## headers
- Cross-references: link to related pages with [[wiki/path/page.md]]
- Confidence: mark uncertain facts with `[uncertain]`
- Source: mark where info came from `[source: conversation 2026-04-08]`

### When to create a new page:

- A topic comes up 3+ times in conversation → deserves its own page
- Bashara explicitly tells Legion something important → save immediately
- Legion does deep research on a topic → synthesize into a page
- A significant bug is fixed → log in relevant issues_log.md

### When to UPDATE an existing page:

- New information contradicts existing → update + note the change
- Bashara corrects Legion → update immediately
- A bug is resolved → move from open to resolved in issues_log.md

### What NOT to put in the wiki:

- Raw conversation transcripts (use mem0 for that)
- Temporary/one-off information
- Speculative information without [uncertain] tag
- Private credentials or keys (NEVER)

### Cross-reference syntax:

[[wiki/rumahlabuh/database_schema.md]] → links to that page
[[wiki/bashara/preferences.md#pytorch]] → links to specific section

### INDEX.md must be updated every time a new page is created.
