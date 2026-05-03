#!/bin/bash
# .opencode/scripts/health-check.sh
# Phase 10 — Complete Stack Health Dashboard
set -euo pipefail

PASS=0; FAIL=0; WARN=0
log() { echo "[$1] $2"; }

# Python environment
python --version 2>&1 | grep -qE "3\.1[0-9]|3\.13|3\.12|3\.11"
if [ $? -eq 0 ]; then
  log "PASS" "Python 3.11+ ✓"
  PASS=$((PASS+1))
else
  log "FAIL" "Python version wrong"
  FAIL=$((FAIL+1))
fi

# Critical Python imports
python3 -c "import swarms, litellm, fastapi, telegram, supabase" 2>&1 | \
    grep -q "Error" && { log "FAIL" "Python deps broken"; ((FAIL++)); } || { log "PASS" "Python deps ✓"; ((PASS++)); }

# Ruff available
command -v ruff &>/dev/null && log "PASS" "ruff available ✓" && ((PASS++)) || { log "FAIL" "ruff not installed"; ((FAIL++)); }

# Mypy available
command -v mypy &>/dev/null && log "PASS" "mypy available ✓" && ((PASS++)) || { log "WARN" "mypy not installed"; ((WARN++)); }

# Pre-commit hooks
test -f .git/hooks/pre-commit && log "PASS" "pre-commit hooks installed ✓" && ((PASS++)) || { log "WARN" "pre-commit not installed"; ((WARN++)); }

# opencode.json valid
python3 -c "import json; json.load(open('.opencode/opencode.json'))" 2>&1 | \
    grep -q "Error" && { log "FAIL" "opencode.json invalid JSON"; ((FAIL++)); } || { log "PASS" "opencode.json valid ✓"; ((PASS++)); }

# API keys hardcoded check (security) — exclude backups which store .env files
grep -r "fc-[0-9a-f]\{32,\}\|exaApiKey=[0-9a-f]" .opencode/ --exclude-dir=backups 2>/dev/null && \
    { log "FAIL" "HARDCODED API KEYS FOUND IN .opencode/"; ((FAIL++)); } || \
    { log "PASS" "No hardcoded API keys in .opencode/ ✓"; ((PASS++)); }

# Hermes submodule
git submodule status ext/hermes-agent 2>/dev/null | grep -q "^-" && \
    { log "WARN" "Hermes submodule not initialized"; ((WARN++)); } || \
    { log "PASS" "Hermes submodule initialized ✓"; ((PASS++)); }

# Wiki dir
test -d .wiki && log "PASS" ".wiki dir exists ✓" && ((PASS++)) || { log "FAIL" ".wiki dir missing"; ((FAIL++)); }

# Node/pnpm
node --version 2>&1 | grep -q "v1[89]\|v2[0-9]" && log "PASS" "Node 18+ ✓" && ((PASS++)) || { log "WARN" "Node version check failed"; ((WARN++)); }

# Agent file structure — check for meaningful content (not specific section names)
python3 -c "
import os
agents_dir = '.opencode/agents'
broken = []
for f in os.listdir(agents_dir):
    if f.endswith('.md'):
        path = os.path.join(agents_dir, f)
        content = open(path).read()
        size = len(content)
        has_frontmatter = content.startswith('---')
        has_title = '# ' in content
        # Agent files need: frontmatter AND (title OR sections)
        if has_frontmatter and not (has_title or '## ' in content):
            broken.append(f'{f} (no content)')
        # Empty or tiny files
        if size < 100:
            broken.append(f'{f} (empty/tiny {size}b)')
if broken:
    print('AGENT_ISSUES: ' + '; '.join(broken))
else:
    print('AGENTS_OK')
" | grep -q "AGENT_ISSUES" && { log "WARN" "Some agent files may be incomplete"; ((WARN++)); } || { log "PASS" "Agent files well-structured ✓"; ((PASS++)); }

# Watcher binary files ignored — check for flatpak, pdf, zip, venv
python3 -c "
import json
cfg = json.load(open('.opencode/opencode.json'))
ignore = cfg.get('watcher',{}).get('ignore',[])
critical = ['.flatpak', '.pdf', '.zip', '.venv']
missing = [r for r in critical if not any(r in i for i in ignore)]
print('MISSING_IGNORES: '+str(missing) if missing else 'WATCHER_OK')
" | grep -q "MISSING" && { log "WARN" "Watcher ignore list incomplete"; ((WARN++)); } || { log "PASS" "Watcher ignore list complete ✓"; ((PASS++)); }

echo ""
echo "═══════════════════════════════════════"
echo "  HEALTH SUMMARY: PASS=$PASS WARN=$WARN FAIL=$FAIL"
echo "═══════════════════════════════════════"
if [ $FAIL -gt 0 ]; then
    echo "STATUS: ✗ CRITICAL — fix FAIL items before working"
    exit 1
elif [ $WARN -gt 3 ]; then
    echo "STATUS: ⚠ DEGRADED — address WARN items soon"
else
    echo "STATUS: ✓ HEALTHY"
fi