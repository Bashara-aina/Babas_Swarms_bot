#!/usr/bin/env bash
# Training health monitor — run every 15 min via cron
# Checks: train alive, loss trend, NaN counter, liveness, validation
set -u

LOG=/tmp/full_train.log
REPORT=/tmp/train_monitor_report.txt

echo "=== Training Monitor $(date -Iseconds) ===" > "$REPORT"

# 1. Still running?
PROCS=$(ps aux | grep 'train.py.*preset paper_run' | grep -v grep | wc -l)
echo "Running processes: $PROCS" >> "$REPORT"
if [ "$PROCS" -lt 2 ]; then
    echo "WARNING: Training may have stopped!" >> "$REPORT"
fi

# 2. Current step
tail -3 "$LOG" 2>/dev/null | grep -oP 'batch \d+' | tail -1 >> "$REPORT"

# 3. NaN counter
grep -c 'GRAD_NAN\|grad_nan\|NAN_COUNTER' "$LOG" 2>/dev/null | xargs -I{} echo "NaN events: {}" >> "$REPORT"

# 4. Liveness (latest)
grep 'LIVENESS_GRAD' "$LOG" 2>/dev/null | tail -3 >> "$REPORT"

# 5. Validation results
grep -i 'eval.*top1\|act_top1\|val_loss\|segment eval' "$LOG" 2>/dev/null | tail -5 >> "$REPORT"

# 6. Recent loss (last non-zero line)
grep 'loss=' "$LOG" 2>/dev/null | grep -v 'det=0.000' | tail -1 >> "$REPORT"

# 7. GPU state
nvidia-smi --query-gpu=memory.used,memory.free,temperature.gpu,utilization.gpu --format=csv,noheader 2>/dev/null >> "$REPORT"

cat "$REPORT"
