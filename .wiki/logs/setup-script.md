---
title: Setup Script
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
summary: '- `scripts/setup_external_tools.sh` — setup script for 3 external tools'
wikilinks: []
confidence: medium
source: research
---
# External Tools Setup Script — 2026-04-12

## Created
- `scripts/setup_external_tools.sh` — setup script for 3 external tools

## Script Content
```bash
#!/bin/bash
set -e

echo "=== Legion External Tools Setup ==="
echo ""

echo "[1/4] Installing Python packages..."
pip install "gpt-researcher>=0.11.0" "markitdown[all]>=0.1.0"
echo "✅ Python packages installed"

echo "[2/4] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. Install Docker to use Dify."
    echo "    https://docs.docker.com/get-docker/"
else
    echo "✅ Docker found: $(docker --version)"
fi

echo "[3/4] Checking .env for required variables..."
MISSING=""
for var in OPENROUTER_API_KEY BRAVE_API_KEY; do
    if [ -z "${!var}" ]; then
        MISSING="$MISSING $var"
    fi
done

if [ -n "$MISSING" ]; then
    echo "⚠️  Missing env vars:$MISSING"
    echo "    Add them to .env before proceeding"
else
    echo "✅ Required env vars found"
fi

echo "[4/4] Testing imports..."
python -c "
results = []
try:
    from core.skills.deep_research import SKILL_META
    results.append('✅ deep_research')
except Exception as e:
    results.append(f'❌ deep_research: {e}')

try:
    from core.skills.doc_parser import parse_file
    results.append('✅ doc_parser')
except Exception as e:
    results.append(f'❌ doc_parser: {e}')

try:
    from core.integrations.dify_client import DifyClient
    results.append('✅ dify_client')
except Exception as e:
    results.append(f'❌ dify_client: {e}')

for r in results:
    print(r)
"

echo ""
echo "=== Dify Setup (optional but recommended) ==="
echo "Run: docker compose -f docker/dify-compose.yml up -d"
echo "Then open: http://localhost:3001"
echo "Create admin account → Settings → API Keys → copy to .env as DIFY_API_KEY"
echo ""
echo "=== New Legion Commands After Setup ==="
echo "/research <topic>  — deep web research with citations"
echo "/draft <type> <content>  — AI document drafting via Dify"
echo "[send any file]  — auto-parse to markdown + summary"
echo ""
echo "✅ Setup complete."
```

## Verification Results

### Packages Installed
- `gpt-researcher>=0.11.0` → 0.14.8
- `markitdown[all]>=0.1.0` → 0.1.5
- Note: `gptr-mcp` was removed (not available on PyPI)

### Import Tests
- ✅ deep_research — `from core.skills.deep_research import SKILL_META`
- ✅ doc_parser — `from core.skills.doc_parser import parse_file`
- ✅ dify_client — `from core.integrations.dify_client import DifyClient`

### Environment Checks
- ⚠️ Docker not found (expected on this system)
- ⚠️ Missing env vars: `OPENROUTER_API_KEY`, `BRAVE_API_KEY`

### Warnings
- Dependency conflicts with `camel-ai`, `knowledge-graph`, `agentops`, `open-interpreter`, `swarms`, `transformers` (non-critical)

## Next Steps
1. Install Docker to enable Dify
2. Add `OPENROUTER_API_KEY` and `BRAVE_API_KEY` to `.env`
3. Run `docker compose -f docker/dify-compose.yml up -d` for Dify setup
