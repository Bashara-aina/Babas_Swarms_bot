#!/bin/bash
# opencode_wrapper.sh — runs opencode with correct environment for swarm-bot
# Uses miniconda3 Python (has aiogram + all dependencies)

set -e

cd /home/newadmin/swarm-bot

# Source conda base to ensure conda is available
if [ -f "/home/newadmin/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/home/newadmin/miniconda3/etc/profile.d/conda.sh"
    conda activate base 2>/dev/null || true
fi

# Run opencode with the system binary (not .venv)
exec /home/newadmin/.opencode/bin/opencode "$@"
