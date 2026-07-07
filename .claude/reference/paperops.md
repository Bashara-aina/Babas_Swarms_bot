# PaperOps — Academic LaTeX DevOps

## Overview

PaperOps is a LaTeX project template for academic paper writing with DevOps automation. It supports a hybrid local/Overleaf workflow, automatic bibliography formatting, difference reports between versions, and minimal archive generation.

**Source:** https://github.com/giacomolanciano/paperops  
**License:** MIT  
**Template location in this project:** `tools/paperops-template/`

## Key Features

- **Makefile-driven build** — `make` builds the full manuscript, drafts, and abstracts
- **Bibliography control** — automatic URL stripping for arXiv; `make bib-fmt` formats per config
- **Version diffing** — `make main-diff-<COMMIT>.pdf` generates a redline PDF via `latexdiff`
- **Archive generation** — `bundledoc` collects only needed files; `archive-safe` strips comments for arXiv
- **Overleaf-compatible** — generates `nourl` variants so Overleaf can build without custom Makefile support
- **Devcontainer** — `.devcontainer.json` with full TeX Live, bibtool, latexdiff, etc.

## Template Structure

| File | Purpose |
|------|---------|
| `main.tex` | Root document, includes all sections |
| `abstract.tex` | Abstract section |
| `background.tex`, `approach.tex`, `experiments.tex`, etc. | Section files |
| `biblio.bib` | Bibliography source |
| `orcidlink.sty` | ORCID link styling |
| `img/` | Figures and images |
| `.latexmkrc` | latexmk configuration (Overleaf v2 compatible) |
| `.bibtoolrsc` | Bibliography formatting rules |
| `.bibtoolrsc-nourl` | Rules for stripping URLs |
| `.bundledoc.cfg` | Archive bundling config |
| `.devcontainer.json` | Dev container definition |
| `scripts/create-biblio-nourl.sh` | URL-stripping bib generator |

## Dependencies

Core: `make`, `latexmk`, `bibtool`, `latexdiff`, `bundledoc`, `arxiv_latex_cleaner`, `jsonlint`, `jq`

All dependencies are pre-installed in the devcontainer image `ghcr.io/giacomolanciano/devcontainer-latex:v1.7.0`.

## Workflow Integration

### Bootstrap a new paper

```bash
mkdir -p papers/my-new-paper
cp -r tools/paperops-template/* tools/paperops-template/.* papers/my-new-paper/
cd papers/my-new-paper && make config
git init
git add -A && git commit -m "Initial commit from paperops template"
```

### Remote setup with Overleaf

1. Create a project on Overleaf, clone its Git repo
2. Copy the template files into the cloned repo
3. Push to Overleaf remote — collaborators edit via web GUI
4. Optionally add a GitHub remote (manual sync only, not shared with collaborators)

### CI/CD via GitHub Actions

The template includes `.github/workflows/build.yml` for on-demand GitHub Actions builds.

## Common Makefile Targets

- `make` — Build `main.pdf` (full manuscript)
- `make abstract` — Build `main-abstract.pdf` (title + abstract only)
- `make draft` — Draft mode (faster, skips heavy figure processing)
- `make bib-fmt` — Format bibliography per `.bibtoolrsc`
- `make main-diff-<COMMIT>.pdf` — Diff between commit and HEAD
- `make archive` — Minimal .zip for camera-ready
- `make archive-safe` — arXiv-safe archive (comments stripped)
- `make clean` — Remove auto-generated files
- `make config` — Initial setup (set git core.fileMode false, chmod scripts)

## Design Notes

- `nourl` variants of `.tex` and `.bib` are auto-generated so the build works on Overleaf
- `.dep` file from `snapshot` package may list deleted temp files — Makefile removes `.w18` entries before `bundledoc`
- `latexdiff` ignores table environments due to known bugs
