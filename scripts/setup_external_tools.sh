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
