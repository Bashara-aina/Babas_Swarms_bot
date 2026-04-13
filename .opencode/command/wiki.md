# /wiki — Knowledge Base Writer

Write or update a wiki article for the task described below.
Always read wiki/SCHEMA.md before writing any wiki article.

## Mandatory Pre-Write Steps
1. Run: cat wiki/SCHEMA.md | head -80 → understand the frontmatter spec
2. Run: cat wiki/INDEX.md | head -40 → check if article already exists
3. Run: find wiki/ -name "*[keyword]*" | sort → find related articles

## Write the Article
Create or update wiki/[type]/[slug].md following SCHEMA.md article structure.
Frontmatter must have ALL required fields: title, type, status, tags, created, updated, summary, wikilinks, confidence, source.

## After Writing
1. cat [new file] | head -20 → verify frontmatter present
2. wc -w [new file] → must exceed minimum (concept: 200w, entity: 150w, project: 400w)
3. python3 -c "import yaml; yaml.safe_load(open('[file]').read().split('---')[1]); print('YAML VALID')"
4. Update wiki/INDEX.md with a link to the new article
5. Update wiki/_meta/compile_state.json article count

Task to execute: