#!/bin/bash
# opencode_wrapper.sh — runs opencode with correct environment for swarm-bot
# Uses system Python (miniconda3 was lost with old hard disk)

set -e

cd /home/newadmin/swarm-bot

# Run opencode with the system binary (not .venv)
exec /home/newadmin/.opencode/bin/opencode "$@"
