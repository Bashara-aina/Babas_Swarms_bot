#!/usr/bin/env bash
# Monitor .gpu_heartbeat file age. Alert if > 10 min stale.
set -e

HEARTBEAT="/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/.gpu_heartbeat"

if [ -f "$HEARTBEAT" ]; then
  AGE=$(( $(date +%s) - $(stat -c %Y "$HEARTBEAT") ))
  if [ $AGE -gt 600 ]; then
    echo "[HEARTBEAT_STALE] .gpu_heartbeat is $AGE seconds old (threshold 600)"
    exit 1
  fi
else
  echo "[HEARTBEAT_MISSING] $HEARTBEAT does not exist"
  exit 1
fi
