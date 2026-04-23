# Wiki Guardian — Obsidian + Karpathy KB Protocol

`.wiki/` is the Obsidian vault containing synthesized project knowledge. All sessions that touch `.wiki/` must follow this protocol.

## WIKI BOOT — Run BEFORE touching .wiki/

**STEP 1** — Verify Obsidian vault is pointed at the right directory:
```bash
ls .wiki/.obsidian/ 2>/dev/null || echo "⚠️ NO .obsidian/ DIR"
ls .wiki/.obsidian/plugins/ 2>/dev/null | head -10
```
Correct vault root: `.wiki/` (at repo root) — NOT `wiki/` (deprecated)

**STEP 2** — Check compile state:
```bash
python3 -c "
import json, os
f = '.wiki/_meta/compile_state.json'
if os.path.exists(f):
    d = json.load(open(f))
    print(f'Articles: {d.get(\"articles\", \"?\")}')
    print(f'Last compiled: {d.get(\"last_compiled\", \"NEVER\")}')
else:
    print('❌ compile_state.json NOT FOUND')
"
```

**STEP 3** — Quick health pulse (15-second full scan):
```python
python3 << 'EOF'
import glob, yaml, re, os
wiki_files = [f for f in glob.glob('.wiki/**/*.md', recursive=True)
              if not any(x in f for x in ['INDEX','SCHEMA','_meta','output','raw'])]
total = len(wiki_files)
no_fm = [f for f in wiki_files if not open(f).read().startswith('---')]
yaml_fails = []
for f in wiki_files:
    p = open(f).read().split('---', 2)
    if len(p) >= 3:
        try: yaml.safe_load(p[1])
        except: yaml_fails.append(f)
all_content = ''.join(open(f).read() for f in glob.glob('.wiki/**/*.md', recursive=True))
broken_links = sum(len(re.findall(r'\[\[[^\]]+\.md\]\]', open(f).read())) for f in wiki_files)
orphans = [f for f in wiki_files
           if all_content.count(f'[[{os.path.splitext(os.path.basename(f))[0]}]]') == 0]
print(f'Total articles: {total}')
print(f'Missing frontmatter: {len(no_fm)} {"✅" if not no_fm else "❌"}')
print(f'YAML failures: {len(yaml_fails)} {"✅" if not yaml_fails else "❌"}')
print(f'Broken .md wikilinks: {broken_links} {"✅" if not broken_links else "❌"}')
print(f'Orphan articles: {len(orphans)} {"⚠️" if orphans else "✅"}')
EOF
```

**GATE**: If YAML failures > 0 OR broken wikilinks > 0: Stop. Fix those first.

**STEP 4** — Read the KB constitution and INDEX:
```bash
cat .wiki/SCHEMA.md | head -80
cat .wiki/INDEX.md | head -60
```

## The Karpathy KB Pattern — 5 Laws

1. **SYNTHESIZE, NOT DUMP**: Distill what you LEARNED into 200-500 words. Write what a FUTURE AI needs to know.
2. **EVERY ARTICLE IS COMPLETE IN ISOLATION**: Valid YAML frontmatter (all 10 fields), TL;DR in first 3 sentences, ≥1 wikilink, ≥1 concrete example with real paths/numbers, "Current Status" section.
3. **THE GRAPH IS THE KNOWLEDGE**: Every new article must link TO existing articles.
4. **RAW/ IS IMMUTABLE, .wiki/ IS SYNTHESIZED**: Never copy-paste from raw/ → .wiki/ without transformation.
5. **THE COMPILE STATE IS THE HEALTH MONITOR**: `.wiki/_meta/compile_state.json` must be updated after EVERY session that touches .wiki/.

## Obsidian Correctness Rules

- **Wikilinks**: NEVER use `.md` extension ✅ `[[concepts/memory-architecture]]` ❌ `[[concepts/memory-architecture.md]]`
- **Paths**: Always relative from `.wiki/` root ✅ `[[entities/litellm]]` ❌ `[[.wiki/entities/litellm]]`
- **Wikilinks field**: MUST be YAML list, never inline
- **Tags**: MUST be YAML list
- **Dates**: MUST be ISO 8601 without quotes
- **Dataview queries**: Use vault-relative paths (NOT `.wiki/` prefix)

## Article Word Count Minimums

| Type | Minimum |
|------|---------|
| concept | ≥ 250 |
| entity | ≥ 200 |
| project | ≥ 500 |
| architecture | ≥ 350 |
| decision | ≥ 250 |
| timeline | ≥ 200 |
| person | ≥ 150 |
| skill | ≥ 200 |

## Path Rules (absolute — never deviate)

| Action | Path |
|--------|------|
| WRITE TO | `.wiki/` ✅ |
| NEVER TO | `wiki/` ❌ (deprecated) |
| NEVER TO | `~/swarm-bot/wiki/` ❌ (deprecated) |
| INDEX at | `.wiki/INDEX.md` ✅ |
| SCHEMA at | `.wiki/SCHEMA.md` ✅ |

## Session End Protocol

```python
python3 << 'EOF'
import json, datetime, glob, os
f = '.wiki/_meta/compile_state.json'
d = json.load(open(f)) if os.path.exists(f) else {}
articles = len([x for x in glob.glob('.wiki/**/*.md', recursive=True)
                if not any(s in x for s in ['_meta','INDEX','SCHEMA','output'])])
d.update({
    'last_compiled': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
    'articles': articles,
})
json.dump(d, open(f, 'w'), indent=2)
print(f'Compile state updated: {articles} articles')
EOF
git add .wiki/ && git commit -m "wiki: [what changed]"
```