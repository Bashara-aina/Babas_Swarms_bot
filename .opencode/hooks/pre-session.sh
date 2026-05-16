#!/bin/bash
# pre-session.sh — runs before each OpenCode session starts
set -e

LOGFILE="${HOME}/.legion/logs/session-$(date +%Y%m%d-%H%M).log"
mkdir -p "$(dirname "$LOGFILE")"
echo "[$(date -Iseconds)] Session starting" >> "$LOGFILE"

# Restore latest session if exists
if [ -f "${HOME}/.legion/sessions/latest" ]; then
    echo "[$(date -Iseconds)] Restoring session context" >> "$LOGFILE"
fi

# Activate conda environment
if [ -f "/home/newadmin/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/home/newadmin/miniconda3/etc/profile.d/conda.sh"
    conda activate swarm-bot 2>/dev/null || true
fi

echo "[$(date -Iseconds)] Pre-session complete" >> "$LOGFILE"
