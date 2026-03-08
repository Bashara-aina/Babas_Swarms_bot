#!/bin/bash
# Quick deployment script for Swarms Bot updates
# Usage: ./deploy.sh

set -e  # Exit on error

echo "====================================="
echo "Babas Swarms Bot - Quick Deploy"
echo "====================================="
echo ""

# Check if running in correct directory
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found. Please run from swarm-bot directory."
    exit 1
fi

echo "[1/5] Pulling latest changes from GitHub..."
git pull origin main

echo ""
echo "[2/5] Checking Ollama service..."
if systemctl is-active --quiet ollama; then
    echo "  ✓ Ollama is running"
else
    echo "  ⚠️  Ollama is not running. Starting..."
    sudo systemctl start ollama
    sleep 2
    if systemctl is-active --quiet ollama; then
        echo "  ✓ Ollama started successfully"
    else
        echo "  ❌ Ollama failed to start. Please check manually."
        exit 1
    fi
fi

echo ""
echo "[3/5] Verifying Ollama model..."
if ollama list | grep -q "qwen3.5:35b"; then
    echo "  ✓ qwen3.5:35b model found"
else
    echo "  ⚠️  qwen3.5:35b model not found. Pulling (this may take a while)..."
    ollama pull qwen3.5:35b
    echo "  ✓ Model pulled successfully"
fi

echo ""
echo "[4/5] Restarting swarm-bot service..."
sudo systemctl restart swarm-bot

echo ""
echo "[5/5] Waiting for service to start..."
sleep 3

if systemctl is-active --quiet swarm-bot; then
    echo "  ✓ Service started successfully"
    echo ""
    echo "====================================="
    echo "Deployment complete!"
    echo "====================================="
    echo ""
    echo "Monitor logs with:"
    echo "  sudo journalctl -u swarm-bot -f"
    echo ""
    echo "Check status with:"
    echo "  sudo systemctl status swarm-bot"
    echo ""
    echo "Recent logs:"
    echo "-------------------------------------"
    sudo journalctl -u swarm-bot -n 20 --no-pager
else
    echo "  ❌ Service failed to start"
    echo ""
    echo "Check logs for errors:"
    echo "  sudo journalctl -u swarm-bot -n 50"
    exit 1
fi
