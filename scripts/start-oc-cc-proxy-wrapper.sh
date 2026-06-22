#!/usr/bin/env bash
export PATH="/home/newadmin/miniconda3/bin:/home/newadmin/.local/bin:$PATH"
exec /home/newadmin/swarm-bot/scripts/start-oc-cc-proxy.sh "$@"
