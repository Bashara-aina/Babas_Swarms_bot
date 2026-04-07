#!/bin/bash
# LegionSwarm v4 → v5 Migration Script
set -e

echo "======================================"
echo "  LegionSwarm v4 → v5 Migration"
echo "======================================"

echo "[1/7] Pulling latest code..."
git pull origin main

echo "[2/7] Activating virtualenv..."
source .venv/bin/activate

echo "[3/7] Installing new dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if command -v node &> /dev/null; then
    echo "[4/7] Installing ruflo Node.js sidecar..."
    cd tools/ruflo && npm install && cd ../..
else
    echo "[4/7] Node.js not found — ruflo will be disabled."
fi

echo "[5/7] Pulling gemma4:e4b local model (requires Ollama)..."
if command -v ollama &> /dev/null; then
    ollama pull gemma4:e4b
    echo "      ✅ gemma4:e4b ready (~6GB VRAM on RTX 3060)"
else
    echo "      ⚠️  Ollama not found — local vision will be unavailable"
fi

echo "[6/7] Initializing MiroFish submodule..."
git submodule update --init --recursive

echo "[7/7] Running test suite..."
pytest tests/ -v --tb=short -x || echo "⚠️  Some tests failed — check output above"

echo ""
echo "======================================"
echo "  Migration complete! Start with:"
echo "  python3 main.py"
echo "  or: sudo systemctl restart swarm-bot"
echo "======================================"
