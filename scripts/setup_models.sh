#!/bin/bash
set -e

echo "Pulling required Ollama models for LegionSwarm v5..."
ollama pull gemma4:e4b
echo "Model setup complete."
echo "VRAM usage estimate: ~6GB / 12GB available on RTX 3060"
