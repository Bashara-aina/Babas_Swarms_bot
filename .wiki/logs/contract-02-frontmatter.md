---
title: Contract 02 Frontmatter
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: Run wiki health scan to identify files missing frontmatter, then add frontmatter
  to each identified file.
wikilinks: []
confidence: medium
source: research
---
## CONTRACT #2: Fix wiki articles missing frontmatter via health scan

WHAT:
  Run wiki health scan to identify files missing frontmatter, then add frontmatter to each identified file.

FILES:
  READ:  /home/newadmin/swarm-bot/.gitignore (to understand skip patterns)
  RUN:   python3 -c "script to list missing frontmatter files"
  WRITE: Multiple files in /home/newadmin/swarm-bot/.wiki/

DONE_WHEN:
  - Health scan runs without error and outputs list of files missing frontmatter
  - All identified files have valid Legion frontmatter added
  - Each frontmatter contains required fields: title, type, status, tags, created, updated, summary

PROOF_FORMAT:
  CODE: `python3 -c "
import os, re, yaml
from pathlib import Path

WIKI_ROOT = Path('/home/newadmin/swarm-bot/.wiki')
SKIP_DIRS = {'_scripts', '_meta', '_quality_report.md'}

def has_legion_frontmatter(content):
    if not content.startswith('---'):
        return False
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False
    try:
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
            return False
        required = {'title', 'type', 'status', 'tags', 'created', 'updated', 'summary'}
        return required.issubset(data.keys())
    except:
        return False

missing = []
for filepath in WIKI_ROOT.rglob('*.md'):
    if any(skip in filepath.parts for skip in SKIP_DIRS):
        continue
    try:
        content = filepath.read_text(encoding='utf-8')
    except:
        continue
    if not has_legion_frontmatter(content):
        rel = filepath.relative_to(WIKI_ROOT)
        missing.append(str(rel))

print(f'Files missing frontmatter: {len(missing)}')
for f in sorted(missing):
    print(f'  {f}')
"`
  Expected output after fix: "Files missing frontmatter: 0"

BLOCKER_IF:
  - Health scan script fails with error
  - More than 50 files identified as missing (indicates something went wrong with prior fix)

DEPENDS_ON: none
