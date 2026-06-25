---
name: graphify
description: "Use for any question about a codebase, its architecture, file relationships, or project content — especially when graphify-out/ exists, where the question should be treated as a graphify query first. Turns any input (code, docs, papers, images, videos) into a persistent knowledge graph with god nodes, community detection, and query/path/explain tools."
trigger: /graphify
---

# /graphify

Turn any folder of files into a navigable knowledge graph with community detection, an honest audit trail, and three outputs: interactive HTML, GraphRAG-ready JSON, and a plain-language GRAPH_REPORT.md.

## Usage

See `references/cli.md` for the full command reference. Common patterns:

```
/graphify                             # full pipeline on current directory
/graphify <path>                       # full pipeline on specific path
/graphify query "<question>"           # BFS traversal on existing graph
/graphify path "A" "B"                # shortest path between two concepts
/graphify explain "Node"              # plain-language explanation of a node
```

## What graphify is for

Drop any folder of code, docs, papers, images, or video into graphify and get a queryable knowledge graph. Persistent across sessions, honest audit trail (EXTRACTED/INFERRED/AMBIGUOUS), community detection surfaces cross-document connections.

## What You Must Do When Invoked

If the user invoked `/graphify --help` or `/graphify -h`, print the common usage patterns above and stop.

**Fast path — existing graph:** Before anything else, check if `graphify-out/graph.json` exists. If it does AND the user's request is a natural-language question about the codebase (not a rebuild command): skip Steps 1-5 and jump to `## For /graphify query`. Run `graphify query "<question>"` immediately.

If no path was given, use `.` (current directory). If the path starts with `https://github.com/` or `http://github.com/`, run Step 0 first.

Follow these steps in order.

### Step 0 - GitHub repos and multi-path merge

Only for `https://github.com/...` URLs or multiple local paths. See `references/github-and-merge.md` for clone, cross-repo merge, and monorepo flows.

### Step 1 - Ensure graphify is installed

```bash
python3 -c "import graphify" 2>/dev/null || (command -v uv >/dev/null 2>&1 && uv tool install graphifyy -q || pip install graphifyy -q)
mkdir -p graphify-out; python3 -c "import sys; open('graphify-out/.graphify_python','w').write(sys.executable)"
```

If that fails, see `references/install.md` for the full Python detection script. In every subsequent bash block, replace `python3` with `$(cat graphify-out/.graphify_python)`.

### Step 2 - Detect files

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.detect import detect
from pathlib import Path
result = detect(Path('INPUT_PATH'))
print(json.dumps(result, ensure_ascii=False))
" > graphify-out/.graphify_detect.json
```

Present a clean summary: `Corpus: X files · ~Y words`, omitting categories with 0 files. Then:
- 0 files → stop with "No supported files found."
- `total_words` > 2M or `total_files` > 500 → show warning, compute top 5 subdirectories by file count, ask which to narrow to
- Otherwise → proceed to Step 2.5 if video files exist, else Step 3

### Step 2.5 - Video and audio

Skip if no `video` files detected. See `references/transcribe.md`.

### Step 3 - Extract entities and relationships

Track `DEEP_MODE=true` if `--mode deep` was given.

Check for `GEMINI_API_KEY` or `GOOGLE_API_KEY`. If set, use `graphify.llm.extract_corpus_parallel(files, backend="gemini")`. Otherwise fall through to Claude subagent dispatch below. If neither set, print: "Tip: set GEMINI_API_KEY or GOOGLE_API_KEY to use Gemini for semantic extraction."

Run Part A (AST) and Part B (semantic) in parallel.

**Part A - AST for code files:**
```bash
$(cat graphify-out/.graphify_python) -c "
import sys, json
from graphify.extract import collect_files, extract
from pathlib import Path
code_files = []
detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))
for f in detect.get('files', {}).get('code', []):
    code_files.extend(collect_files(Path(f)) if Path(f).is_dir() else [Path(f)])
if code_files:
    result = extract(code_files, cache_root=Path('.'))
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'AST: {len(result[\"nodes\"])} nodes, {len(result[\"edges\"])} edges')
else:
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps({'nodes':[],'edges':[],'input_tokens':0,'output_tokens':0}))
    print('No code files - skipping AST')
"
```

**Part B - Semantic extraction:** If zero docs/papers/images detected (code-only corpus), skip Part B entirely. Otherwise read `references/extraction-spec.md` for the subagent prompt template and dispatch subagents in parallel using the Agent tool (general-purpose type, NOT Explore). Split uncached files into chunks of 20-25. All Agent calls in one message.

After all subagents complete, merge chunks and save to cache. See the full logic in `references/extraction-spec.md`.

**Part C - Merge AST + semantic:**
```bash
$(cat graphify-out/.graphify_python) -c "
import json; from pathlib import Path
ast = json.loads(Path('graphify-out/.graphify_ast.json').read_text(encoding='utf-8'))
sem = json.loads(Path('graphify-out/.graphify_semantic.json').read_text(encoding='utf-8'))
seen = {n['id'] for n in ast['nodes']}
merged = {'nodes': ast['nodes'] + [n for n in sem['nodes'] if n['id'] not in seen], 'edges': ast['edges'] + sem['edges'], 'hyperedges': sem.get('hyperedges', []), 'input_tokens': sem.get('input_tokens', 0), 'output_tokens': sem.get('output_tokens', 0)}
Path('graphify-out/.graphify_extract.json').write_text(json.dumps(merged, indent=2))
print(f'Merged: {len(merged[\"nodes\"])} nodes, {len(merged[\"edges\"])} edges')
"
```

### Step 4 - Build graph, cluster, analyze, generate outputs

Pass `directed=True` if `--directed` was given.

```bash
mkdir -p graphify-out
$(cat graphify-out/.graphify_python) -c "
import json, sys
from graphify.build import build_from_json; from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate; from graphify.export import to_json
from pathlib import Path
extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding='utf-8'))
detection = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))
G = build_from_json(extraction)
communities = cluster(G)
cohesion = score_all(G, communities)
gods = god_nodes(G)
surprises = surprising_connections(G, communities)
labels = {cid: 'Community ' + str(cid) for cid in communities}
questions = suggest_questions(G, communities, labels)
report = generate(G, communities, cohesion, labels, gods, surprises, detection, {'input': extraction.get('input_tokens',0), 'output': extraction.get('output_tokens',0)}, '.', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report, encoding='utf-8')
to_json(G, communities, 'graphify-out/graph.json')
analysis = {'communities': {str(k):v for k,v in communities.items()}, 'cohesion': {str(k):v for k,v in cohesion.items()}, 'gods': gods, 'surprises': surprises, 'questions': questions}
Path('graphify-out/.graphify_analysis.json').write_text(json.dumps(analysis, indent=2), encoding='utf-8')
if G.number_of_nodes() == 0: print('ERROR: Graph is empty'); sys.exit(1)
print(f'Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities')
"
```

If `ERROR: Graph is empty`, stop and tell the user.

### Step 5 - Label communities

Read `graphify-out/.graphify_analysis.json`. For each community, write a 2-5 word name. Then regenerate the report:

```bash
$(cat graphify-out/.graphify_python) -c "
import json
from graphify.build import build_from_json; from graphify.cluster import score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate; from pathlib import Path
extraction = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding='utf-8'))
detection = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))
analysis = json.loads(Path('graphify-out/.graphify_analysis.json').read_text(encoding='utf-8'))
G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
labels = LABELS_DICT  # your 2-5 word names here
questions = suggest_questions(G, communities, labels)
report = generate(G, communities, {int(k):v for k,v in analysis['cohesion'].items()}, labels, analysis['gods'], analysis['surprises'], detection, {'input': extraction.get('input_tokens',0), 'output': extraction.get('output_tokens',0)}, '.', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report, encoding='utf-8')
Path('graphify-out/.graphify_labels.json').write_text(json.dumps({str(k):v for k,v in labels.items()}))
print('Report updated with community labels')
"
```

### Step 6 - Generate outputs

Generate HTML always (unless `--no-viz`). Obsidian vault only if `--obsidian` was given:
```bash
graphify export html
# graphify export obsidian [--dir ~/vaults/my-project]
```

### Steps 6b-8 - Wiki, Neo4j, SVG, GraphML, MCP (flag-gated only)

See `references/exports.md`. Run `--wiki` export before Step 9.

### Step 9 - Save manifest, update cost tracker, clean up, report

```bash
$(cat graphify-out/.graphify_python) -c "
import json; from pathlib import Path; from datetime import datetime, timezone
from graphify.detect import save_manifest
detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))
save_manifest(detect.get('all_files') or detect['files'])
extract = json.loads(Path('graphify-out/.graphify_extract.json').read_text(encoding='utf-8'))
cost_path = Path('graphify-out/cost.json')
cost = json.loads(cost_path.read_text(encoding='utf-8')) if cost_path.exists() else {'runs':[],'total_input_tokens':0,'total_output_tokens':0}
cost['runs'].append({'date': datetime.now(timezone.utc).isoformat(), 'input_tokens': extract.get('input_tokens',0), 'output_tokens': extract.get('output_tokens',0), 'files': detect.get('total_files',0)})
cost['total_input_tokens'] += extract.get('input_tokens',0); cost['total_output_tokens'] += extract.get('output_tokens',0)
cost_path.write_text(json.dumps(cost, indent=2), encoding='utf-8')
print(f'This run: {extract.get(\"input_tokens\",0):,} in / {extract.get(\"output_tokens\",0):,} out tokens')
print(f'All time: {cost[\"total_input_tokens\"]:,} in / {cost[\"total_output_tokens\"]:,} out ({len(cost[\"runs\"])} runs)')
"
rm -f graphify-out/.graphify_detect.json graphify-out/.graphify_extract.json graphify-out/.graphify_ast.json graphify-out/.graphify_semantic.json graphify-out/.graphify_analysis.json graphify-out/.graphify_chunk_*.json
rm -f graphify-out/.needs_update 2>/dev/null || true
```

Tell the user:
```
Graph complete. Outputs in PATH/graphify-out/
  graph.html       - interactive graph
  GRAPH_REPORT.md  - audit report
  graph.json       - raw graph data
```

Then paste God Nodes, Surprising Connections, and Suggested Questions sections from the report. Offer to explore the most interesting question.

---

## For /graphify query

When `graphify-out/graph.json` already exists:
```bash
graphify query "<question>"
```
Answer using only graph output. Quote `source_location` when citing facts. See `references/query.md` for `--dfs`, `--budget`, `save-result`, `path`, and `explain` flows.

## For --update and --cluster-only

See `references/update.md`.

## For /graphify add and --watch

See `references/add-watch.md`.

## For the commit hook and CLAUDE.md integration

See `references/hooks.md`.

## Honesty Rules

- Never invent an edge. Use AMBIGUOUS if unsure.
- Never skip the corpus check warning.
- Always show token cost in the report.
- Never hide cohesion scores - show raw numbers.
- Never run HTML viz on >5,000 nodes without warning.
