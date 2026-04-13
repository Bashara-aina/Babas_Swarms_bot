---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/logs/dead-purge-plan.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-13T01:00:00.509340"
}
---

# Dead File Purge Execution Plan
> Created: 2026-04-11 | Planner: @planner | Task: Safe dead file cleanup with 3-pass confirmation

## Overview
Identify and safely remove confirmed-dead files from `/home/newadmin/swarm-bot` using a 3-pass confirmation protocol and graveyard pattern.

---

## Safety Rules (MUST FOLLOW)

1. **Git checkpoint BEFORE any file operations**
2. **Never delete whitelisted files**:
   - `app/layout.tsx`, `page.tsx`, `globals.css`, `next.config.mjs`, `tailwind.config.ts`, `tsconfig.json`
   - `package.json`, `.eslintrc.json`, `jest.config.js`, `components.json`, `postcss.config.mjs`
   - `supabase/*`, `__tests__/*`, `.env*`, `README.md`, `CONTRIBUTING.md`, `LICENSE`
3. **Always move to graveyard first** (never `rm` directly)
4. **3-pass confirmation required** before any deletion
5. **Log everything** to `CLEANUP_LOG.md`

---

## Whitelist Patterns (Never Delete)

```
# Config files
*.json (if package.json, .eslintrc.json, jest.config.js, components.json, tsconfig.json)
*.mjs, *.ts (if next.config, tailwind.config, tsconfig)

# Environment
.env*

# Documentation
README.md
CONTRIBUTING.md
LICENSE

# Test directories
**/__tests__/**
**/tests/**

# Supabase
**/supabase/**

# Core project files
AGENTS.md
CLAUDE.md
pyproject.toml
requirements*.txt
Makefile
docker-compose.yml
.pre-commit-config.yaml
.gitmodules

# Wiki
.wiki/

# Config dir
config/

# Data dir
data/
logs/
papers/
skills/
prompts/
scripts/
.github/
.vscode/
.cursor/
```

---

## STAGE 0: Environment Setup
**Agent**: @worker

### 0.1 Git Checkpoint
```bash
cd /home/newadmin/swarm-bot
git add -A
git commit -m "CHORE: pre-dead-file-purge checkpoint"
git push origin $(git branch --show-current) 2>/dev/null || true
```

### 0.2 Create Graveyard Directory
```bash
mkdir -p /home/newadmin/swarm-bot/_graveyard/20260411
```

### 0.3 Initialize Cleanup Log
```bash
cat > /home/newadmin/swarm-bot/CLEANUP_LOG.md << 'EOF'
# Dead File Purge Cleanup Log
> Date: 2026-04-11

## Whitelist (Never Delete)
- app/layout.tsx, page.tsx, globals.css, next.config.mjs, tailwind.config.ts, tsconfig.json
- package.json, .eslintrc.json, jest.config.js, components.json, postcss.config.mjs
- supabase/*, __tests__/*, .env*, README.md, CONTRIBUTING.md, LICENSE
- AGENTS.md, CLAUDE.md, pyproject.toml, requirements*.txt, Makefile
- .wiki/, config/, data/, logs/, papers/, skills/, prompts/, scripts/

## Pass 1: Static Import Analysis (YYYY-MM-DD)
<!-- Results table -->

## Pass 2: Runtime/Dynamic Usage Check (YYYY-MM-DD)
<!-- Results table -->

## Pass 3: Future Use Check (YYYY-MM-DD)
<!-- Results table -->

## Confirmed Dead Files
<!-- Final list of files moved to graveyard -->

## Deletion Log (After 30-day retention)
<!-- Record of actual deletions -->
EOF
```

### 0.4 Create File Inventory
```bash
cd /home/newadmin/swarm-bot
# Get all tracked files (excluding gitignored)
git ls-files > /tmp/all_tracked_files.txt
# Get all untracked files
git ls-files --others --exclude-standard > /tmp/all_untracked_files.txt
# Combine into full inventory
cat /tmp/all_tracked_files.txt /tmp/all_untracked_files.txt | sort -u > /tmp/file_inventory.txt
wc -l /tmp/file_inventory.txt
```

**Verification**: Confirm inventory has reasonable count (should be <5000 files)

---

## STAGE 1: Pass 1 — Static Import Analysis
**Agent**: @worker

### Goal
Find files with ZERO static imports (never referenced by any other file).

### 1.1 Find All Python Import References
```bash
cd /home/newadmin/swarm-bot
# Create a list of all .py files
find . -name "*.py" -not -path "./.venv/*" -not -path "./.git/*" > /tmp/all_py_files.txt
# For each file, check if it's imported anywhere
python3 << 'PYEOF'
import os
import re
from pathlib import Path

# Read all py files
py_files = Path('.').glob('**/*.py')
py_files = [f for f in py_files if '.venv' not in str(f) and '.git' not in str(f)]

# Build import map
file_imports = {}
for f in py_files:
    try:
        content = f.read_text()
        imports = re.findall(r'^(?:from|import)\s+[\w.]+', content, re.MULTILINE)
        file_imports[str(f)] = imports
    except:
        pass

# Find orphaned files (not imported by anyone)
all_import_targets = set()
for imports in file_imports.values():
    for imp in imports:
        # Extract module path
        match = re.search(r'from\s+([\w.]+)', imp) or re.search(r'import\s+([\w.]+)', imp)
        if match:
            all_import_targets.add(match.group(1))

# Check which files are never imported
orphaned = []
for f in py_files:
    fname = str(f).replace('./', '').replace('.py', '').replace('/', '.')
    if fname not in all_import_targets:
        # Also check for __init__ pattern
        init_name = str(f).replace('/', '.').replace('./', '') + '.__init__'
        if init_name not in all_import_targets:
            orphaned.append(str(f))

print("ORPHANED_PY_FILES:")
for f in sorted(orphaned):
    print(f)
PYEOF
```

### 1.2 Find Unused Non-Python Files
```bash
cd /home/newadmin/swarm-bot
# Check for unused .md, .txt, .yaml, .yml, .json (excluding config)
python3 << 'PYEOF'
import os
import re
from pathlib import Path

whitelist_extensions = {'.py', '.md', '.txt', '.yaml', '.yml', '.json', '.sh', '.html', '.css', '.js', '.ts', '.tsx'}

all_files = []
for root, dirs, files in os.walk('.'):
    # Skip ignored dirs
    if any(ignored in root for ignored in ['.venv', '.git', 'node_modules', '__pycache__', '.pytest_cache', 'logs', 'data', 'papers', 'skills', 'prompts', 'scripts', '.wiki', 'config', 'llm_client']):
        continue
    for f in files:
        ext = os.path.splitext(f)[1]
        if ext in whitelist_extensions:
            all_files.append(os.path.join(root, f))

# Read all text files and build reference map
references = set()
for f in all_files:
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            content = fp.read()
            # Find file references (relative)
            refs = re.findall(r'\.\/[\w\-\.\/]+|\.\.[\w\-\.\/]+|[\w\-\.]+\.(?:py|md|txt|yaml|yml|json|sh)', content)
            references.update(refs)
    except:
        pass

# Find files never referenced
never_referenced = []
for f in all_files:
    fname = os.path.basename(f)
    if fname not in references and not any(s in f for s in ['AGENTS.md', 'CLAUDE.md', 'README.md', 'requirements', 'test_', 'conftest']):
        never_referenced.append(f)

print("NEVER_REFERENCED_FILES:")
for f in sorted(never_referenced):
    print(f)
PYEOF
```

### 1.3 Compile Initial Dead File List
```bash
cd /home/newadmin/swarm-bot
# Combine orphaned Python files and never-referenced files
# Filter against whitelist
python3 << 'PYEOF'
import os

whitelist = {
    'AGENTS.md', 'CLAUDE.md', 'README.md', 'CONTRIBUTING.md', 'LICENSE',
    'requirements.txt', 'requirements_no_tiktoken.txt', 'pyproject.toml',
    'Makefile', 'docker-compose.yml', '.pre-commit-config.yaml', '.gitmodules',
    'main.py', 'agents.py', 'router.py', 'task_orchestrator.py', 'daily_harvester.py',
    'test_apis.py', 'computer_agent.py.bak', '.env', '.env.example', '.env.bak',
    'AUDIT_REPORT.md', 'CHANGELOG.md', 'DEEP_AUDIT_2026-04-10.md', 'DEPLOYMENT.md',
    'IMPLEMENTATION_STATUS.md', 'LEGION_MASTER_PROMPT.md', 'MASTER_FIX_PROMPT.md',
    'MASTER_PROMPT.md', 'SOUL.md', 'SWARM_WIRING.md', 'TESTING.md',
    'restart.sh', 'deploy.sh', 'bot.log', 'legion_output.log', 'swarm-structured.log',
    'legion.db', 'computer_agent.py.bak', '.coverage', '.ruff_cache', '.pytest_cache',
    'obsidian_1.8.10_amd64.deb', 'memory.backup', '=0.23.0',
}

# These are the files identified as potentially dead from Pass 1
# (This would be populated from the actual analysis above)
potential_dead = []

for f in potential_dead:
    fname = os.path.basename(f)
    if fname not in whitelist:
        print(f)
PYEOF
```

**Verification**: Review the list manually before proceeding

---

## STAGE 2: Pass 2 — Runtime/Dynamic Usage Check
**Agent**: @worker

### Goal
Check if files are used at runtime (imports, dynamic requires, etc.)

### 2.1 Runtime Import Verification
```bash
cd /home/newadmin/swarm-bot
python3 << 'PYEOF'
import ast
import os
from pathlib import Path

# Parse main.py to get runtime imports
def get_runtime_imports(filepath):
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read())
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        return imports
    except:
        return set()

# Get imports from main entry points
runtime_imports = set()
for entry in ['main.py', 'agents.py', 'router.py', 'task_orchestrator.py', 'daily_harvester.py']:
    if os.path.exists(entry):
        runtime_imports.update(get_runtime_imports(entry))

print("RUNTIME_IMPORTS:")
for imp in sorted(runtime_imports):
    print(imp)
PYEOF
```

### 2.2 Check Against Active Importers
```bash
cd /home/newadmin/swarm-bot
# For each potential dead file, check if any active module imports it
python3 << 'PYEOF'
import os
import re

# List of files confirmed as dead from Pass 1
# Replace with actual list from Pass 1
confirmed_dead = []

# Get all active Python files (not in __pycache__, .venv, .git)
active_files = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['.venv', '.git', '__pycache__', '.pytest_cache', 'node_modules']]
    for f in files:
        if f.endswith('.py'):
            active_files.append(os.path.join(root, f))

# For each potentially dead file, check if any active file imports it
still_used = []
for dead_file in confirmed_dead:
    dead_module = dead_file.replace('./', '').replace('/', '.').replace('.py', '')
    for active in active_files:
        try:
            with open(active, 'r') as f:
                content = f.read()
            if dead_module in content or dead_file.replace('./', '') in content:
                still_used.append((dead_file, active))
                break
        except:
            pass

if still_used:
    print("STILL_USED_FILES:")
    for pair in still_used:
        print(f"{pair[0]} <- {pair[1]}")
else:
    print("NO_RUNTIME_USAGE_FOUND")
PYEOF
```

**Verification**: Any file found in runtime usage is RECOVERED (removed from dead list)

---

## STAGE 3: Pass 3 — Future Use Check
**Agent**: @worker

### Goal
Check for TODO comments, documentation references, roadmaps, etc.

### 3.1 Check for TODO/FIXME References
```bash
cd /home/newadmin/swarm-bot
python3 << 'PYEOF'
import os
import re

# List of potential dead files from Pass 2
potential_dead = []

# Search all active files for references to potential dead files
future_references = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['.venv', '.git', '__pycache__', '.pytest_cache', 'node_modules', '_graveyard']]
    for f in files:
        filepath = os.path.join(root, f)
        if filepath in potential_dead:
            continue
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
            for dead in potential_dead:
                dead_name = os.path.basename(dead).replace('.py', '')
                if dead_name in content and ('TODO' in content or 'FIXME' in content or 'XXX' in content):
                    future_references.append((dead, filepath))
        except:
            pass

if future_references:
    print("FUTURE_USE_REFERENCES:")
    for pair in future_references:
        print(f"{pair[0]} <- {pair[1]}")
else:
    print("NO_FUTURE_USE_FOUND")
PYEOF
```

### 3.2 Check Documentation References
```bash
cd /home/newadmin/swarm-bot
# Search docs, wikis, and comments for references
rg -l "computer_agent\.py\.bak|obsidian|legion\.db" --type py --type md . 2>/dev/null | head -20
```

**Verification**: Any file with future references is RECOVERED

---

## STAGE 4: Pattern Hunter — Unused Modules
**Agent**: @worker

### 4.1 Find Unused Agent Files
```bash
cd /home/newadmin/swarm-bot
python3 << 'PYEOF'
import os
import re

# Get all agent files
agent_files = []
for root, dirs, files in os.walk('./agents'):
    for f in files:
        if f.endswith('.py') and f != '__init__.py':
            agent_files.append(os.path.join(root, f))

# Check which agents are imported in agents.py
with open('agents.py', 'r') as f:
    agents_py_content = f.read()

unused_agents = []
for agent in agent_files:
    agent_name = os.path.basename(agent).replace('.py', '')
    if agent_name not in agents_py_content:
        unused_agents.append(agent)

print("UNUSED_AGENT_FILES:")
for a in sorted(unused_agents):
    print(a)
PYEOF
```

### 4.2 Find Unused Handler Files
```bash
cd /home/newadmin/swarm-bot
# Check handlers against router registration
rg "from handlers|import.*handlers" --type py -l . 2>/dev/null | wc -l
# List all handlers
ls -la handlers/
```

---

## STAGE 5: Pattern Hunter — Components/Libraries
**Agent**: @worker

### 5.1 Find Unused Core Modules
```bash
cd /home/newadmin/swarm-bot
python3 << 'PYEOF'
import os
from pathlib import Path

# Get all core modules
core_modules = list(Path('./core').glob('**/*.py'))
core_modules = [f for f in core_modules if f.name != '__init__.py' and '__pycache__' not in str(f)]

# Check which are used
used_modules = set()
for f in Path('.').glob('**/*.py'):
    if '__pycache__' in str(f) or '.venv' in str(f):
        continue
    try:
        content = f.read_text()
        for module in core_modules:
            mod_name = module.stem
            if f != module and f.name != '__init__.py':
                if mod_name in content:
                    used_modules.add(mod_name)
    except:
        pass

unused = [m for m in core_modules if m.stem not in used_modules]
print("UNUSED_CORE_MODULES:")
for m in sorted(unused):
    print(m)
PYEOF
```

### 5.2 Find Unused Tools
```bash
cd /home/newadmin/swarm-bot
ls -la tools/
# Check tools against main.py and agents.py
rg "from tools|import.*tools" --type py -l . 2>/dev/null
```

---

## STAGE 6: Pattern Hunter — Test Files
**Agent**: @worker

### 6.1 Find Orphaned Test Files
```bash
cd /home/newadmin/swarm-bot
python3 << 'PYEOF'
import os

# Get all test files
test_files = []
for root, dirs, files in os.walk('./tests'):
    for f in files:
        if f.startswith('test_') and f.endswith('.py'):
            test_files.append(os.path.join(root, f))

# Get all source files
source_files = []
for root, dirs, files in os.walk('.'):
    if any(ignored in root for ignored in ['.venv', '.git', '__pycache__', 'tests', 'node_modules']):
        continue
    for f in files:
        if f.endswith('.py'):
            source_files.append(os.path.join(root, f))

# Extract module names from test files
def get_test_target(test_file):
    name = os.path.basename(test_file).replace('test_', '').replace('.py', '')
    return name

# Check if corresponding source exists
orphaned_tests = []
for test in test_files:
    target = get_test_target(test)
    found = False
    for src in source_files:
        if target in src:
            found = True
            break
    if not found:
        orphaned_tests.append(test)

print("ORPHANED_TEST_FILES:")
for t in sorted(orphaned_tests):
    print(t)
PYEOF
```

---

## STAGE 7: Execute Deletions
**Agent**: @worker

### 7.1 Final Review of Confirmed Dead Files
```bash
cd /home/newadmin/swarm-bot
# List all confirmed dead files (from Pass 1-6)
# IMPORTANT: Review this list manually before proceeding!

cat << 'EOF'
CONFIRMED_DEAD_FILES_REQUIRES_MANUAL_REVIEW:
1. computer_agent.py.bak (backup file)
2. obsidian_1.8.10_amd64.deb (installer, not source)
3. =0.23.0 (invalid filename)
4. memory.backup (backup file)
5. [Add more after Pass 1-6 analysis]
EOF
```

### 7.2 Move to Graveyard (Not Delete!)
```bash
cd /home/newadmin/swarm-bot

# Move confirmed dead files to graveyard
# Example (REPLACE with actual list):
# mv computer_agent.py.bak _graveyard/20260411/
# mv =0.23.0 _graveyard/20260411/
# mv memory.backup _graveyard/20260411/

# ALWAYS use mv, NEVER rm!

echo "Files moved to _graveyard/20260411/"
ls -la _graveyard/20260411/
```

### 7.3 Log All Moved Files
```bash
cd /home/newadmin/swarm-bot
# Update CLEANUP_LOG.md with all moved files
echo "## Files Moved to Graveyard (2026-04-11)" >> CLEANUP_LOG.md
echo "" >> CLEANUP_LOG.md
echo "| File | Reason | Pass |" >> CLEANUP_LOG.md
echo "|------|--------|------|" >> CLEANUP_LOG.md
# Add entries for each file
```

---

## STAGE 8: Cleanup Loose Ends
**Agent**: @worker

### 8.1 Update .gitignore (If Needed)
```bash
cd /home/newadmin/swarm-bot
# Check if _graveyard should be in gitignore
grep "_graveyard" .gitignore || echo "_graveyard/" >> .gitignore
```

### 8.2 Remove Cache Files
```bash
cd /home/newadmin/swarm-bot
# Clean Python cache if any remaining
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
```

### 8.3 Git Commit
```bash
cd /home/newadmin/swarm-bot
git add -A
git status
# Commit only after manual verification of changes
git diff --cached --stat
```

---

## Verification Checklist

- [ ] Stage 0: Git checkpoint created
- [ ] Stage 0: Graveyard directory created
- [ ] Stage 0: CLEANUP_LOG.md initialized
- [ ] Stage 0: File inventory completed
- [ ] Stage 1: Pass 1 static analysis completed
- [ ] Stage 2: Pass 2 runtime check completed
- [ ] Stage 3: Pass 3 future use check completed
- [ ] Stages 4-6: Pattern hunters completed
- [ ] Stage 7: All dead files moved to graveyard
- [ ] Stage 8: .gitignore updated
- [ ] Stage 8: Cache files cleaned
- [ ] Stage 8: Final git commit created
- [ ] CLEANUP_LOG.md fully documented

---

## Retention Policy

Files in `_graveyard/` are retained for **30 days** before permanent deletion.
After 30 days, run:
```bash
# DELETE FROM GRAVEYARD (30+ days old)
find _graveyard -type f -mtime +30 -delete
```

---

## Rollback Plan

If rollback needed:
```bash
# Restore from git
git checkout HEAD -- .

# Or restore specific file from graveyard
mv _graveyard/20260411/<filename> .
```
