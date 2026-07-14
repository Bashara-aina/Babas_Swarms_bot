# Token efficiency (always active)
- Be concise in responses. Omit narrative, give direct answers.
- Read files >50KB in chunks: `Read(file, limit=200)` then page.
- Prefer `Edit` over `Write` for large files (smaller diff).
- Prefer `Grep` over full-file `Read` for targeted lookups.
- Prefer targeted `Glob` over `Bash(find)`.

# graphify: `/graphify query "..."` for codebase graph.
# Design references (on demand): `.claude/reference/ui-ux-excellence.md`, `taste-router.md`
# Fable 5 (on demand): `.claude/reference/fable5-*.md`
