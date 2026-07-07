---
name: paperops
description: "LaTeX paper DevOps — bootstrap, build, diff, archive, and format academic papers using the paperops template (Makefile-driven, Overleaf-compatible, arXiv-ready). Invoke when the user wants to create a new paper, build a LaTeX project, format bibliography, generate a diff PDF, or prepare a camera-ready/arXiv archive."
trigger: /paperops
---

# /paperops

Academic LaTeX paper writing meets DevOps. Automates build, diff, archive, and bibliography formatting.

## Template location

The paperops template is installed at `tools/paperops-template/`. To start a new paper:

```bash
mkdir -p papers/my-paper && cp -r tools/paperops-template/* tools/paperops-template/.* papers/my-paper/ 2>/dev/null
cd papers/my-paper && make config
```

## Dependencies

The full toolchain requires: `make`, `latexmk`, `bibtool`, `latexdiff`, `bundledoc`, `arxiv_latex_cleaner`, `jsonlint`, `jq`. The devcontainer at `.devcontainer.json` bundles all dependencies (image: `ghcr.io/giacomolanciano/devcontainer-latex:v1.7.0`).

## Available commands (from the Makefile)

| Command | Description |
|---------|-------------|
| `make` | Build `main.pdf` (the complete manuscript) |
| `make main.pdf` | Build PDF from `main.tex` |
| `make abstract` | Build `main-abstract.pdf` (title + abstract) |
| `make all` | Build both `main.pdf` and `main-abstract.pdf` |
| `make draft` | Build in draft mode (faster, skips figures) |
| `make config` | Apply initial configurations (needed once after copy) |
| `make bib-fmt` | Format `biblio.bib` per `.bibtoolrsc` rules |
| `make main-diff-<COMMIT>.pdf` | Diff PDF between `<COMMIT>` and HEAD |
| `make archive` | Minimal .zip for camera-ready submission |
| `make archive-safe` | Like archive, also strips comments (arXiv-safe) |
| `make clean` | Remove all auto-generated files |

## What to do when invoked

1. **If the user wants to create a new paper:** Copy the template to their target directory, run `make config`, and optionally initialize git. The template supports hybrid local/Overleaf workflow.
2. **If the user wants to build:** Run `make` (or the specific target) in the paper directory.
3. **If the user wants to format bibliography:** Run `make bib-fmt` in the paper directory.
4. **If the user wants a diff:** Run `make main-diff-<COMMIT>.pdf` to see changes since a commit.
5. **If the user wants an archive:** Run `make archive` (camera-ready) or `make archive-safe` (arXiv).
6. **If the user asks about structure:** Explain the template layout — `main.tex` is the root, each section in its own `.tex` file, `biblio.bib` for references, config files prefixed with `.`.

## Reference

Full details in `.claude/reference/paperops.md`.
