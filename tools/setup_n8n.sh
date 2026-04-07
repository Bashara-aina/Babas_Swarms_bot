#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[n8n] Checking docker availability..."
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Install docker and docker compose first."
  exit 1
fi

echo "[n8n] Starting n8n container via docker compose..."
docker compose up -d n8n

echo "[n8n] Done. Check status with: docker compose ps n8n"
