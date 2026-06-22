# Complete CLI Reference

Load this file when you need the full list of graphify subcommands and flags.

## Common commands

```
/graphify                                             # full pipeline on current directory
/graphify <path>                                      # full pipeline on specific path
/graphify query "<question>"                           # BFS traversal - broad context
/graphify path "AuthModule" "Database"                 # shortest path between two concepts
/graphify explain "SwinTransformer"                    # plain-language explanation of a node
```

## Build flags

| Flag | Description |
|------|-------------|
| `--mode deep` | Thorough extraction, richer INFERRED edges |
| `--update` | Re-extract only new/changed files |
| `--directed` | Build directed graph |
| `--whisper-model medium` | Use larger Whisper model for audio |
| `--cluster-only` | Rerun clustering on existing graph |
| `--no-viz` | Skip visualization |
| `--svg` | Export graph.svg (embeds in Notion, GitHub) |
| `--graphml` | Export graph.graphml (Gephi, yEd) |
| `--neo4j` | Generate cypher.txt for Neo4j |
| `--neo4j-push bolt://host:7687` | Push directly to Neo4j |
| `--mcp` | Start MCP stdio server |
| `--watch` | Watch folder, auto-rebuild on changes |
| `--wiki` | Build agent-crawlable wiki |
| `--obsidian --obsidian-dir ~/vaults/x` | Write vault to custom path |

## Query flags

```
/graphify query "<question>" --dfs          # DFS - trace a specific path
/graphify query "<question>" --budget 1500  # cap answer at N tokens
```

## Add command

```
/graphify add <url>                                  # fetch URL, save to ./raw, update graph
/graphify add <url> --author "Name"                   # tag who wrote it
/graphify add <url> --contributor "Name"              # tag who added it to the corpus
```

## GitHub URLs

```
/graphify https://github.com/<owner>/<repo>           # clone repo then run full pipeline
/graphify https://github.com/<owner>/<repo> --branch  # clone a specific branch
/graphify <url1> <url2> ...                           # clone multiple repos, merge
```
