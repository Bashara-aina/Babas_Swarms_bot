#!/usr/bin/env bash
# Monitor active R2.5 training run — auto-detects PID and latest dedicated log
set -e

TRAIN_DIR=/media/newadmin/master/POPW/working/code/industreal_improved/src/runs
TODAY=$(date +%Y-%m-%d)

# Auto-detect: find the training PID (main process, not workers)
PID=$(ps aux | grep 'python.*train.py.*--preset' | grep -v grep | awk '{print $2}' | head -1)
if [ -z "$PID" ]; then
    PID=$(ps aux | grep 'python.*train.py' | grep -v grep | awk '{print $2}' | head -1)
fi

# Auto-detect: find the newest dedicated training log
LOG=$(find "$TRAIN_DIR" -name 'paper_run_r25_*.log' -o -name 'paper_run_r25_reinit_*.log' 2>/dev/null \
    | sort | tail -1)

if [ -z "$LOG" ] || [ ! -f "$LOG" ]; then
    # Fallback: any train.log
    LOG=$(find "$TRAIN_DIR" -name 'train.log' -path '*/logs/*' -printf '%T@ %p\n' 2>/dev/null \
        | sort -rn | head -1 | cut -d' ' -f2-)
fi

if [ -z "$PID" ] || [ -z "$LOG" ]; then
    echo "[MONITOR] No training process or log found"
    if [ -n "$LOG" ]; then
        echo "[MONITOR] Log at ${LOG} — checking for completion/crash"
        if grep -qi "training completed\|validation.*finished\|evaluation.*complete" "$LOG" 2>/dev/null; then
            echo "[MONITOR] Training completed normally"
        elif grep -qi "traceback\|error\|exception" "$LOG" 2>/dev/null; then
            echo "[MONITOR] Training CRASHED — last traceback:"
            tac "$LOG" | grep -A5 -i "traceback" | head -10
        fi
        echo ""
        echo "Last 10 log lines:"
        tail -10 "$LOG"
    fi
    exit 1
fi

echo "[MONITOR] PID ${PID} ALIVE — $(ps -p ${PID} -o etime --no-headers 2>/dev/null || echo 'N/A')"
echo "[MONITOR] Log: $(basename "$(dirname "$LOG")")/$(basename "$LOG")"

# Step progress from progress bar lines
LATEST=$(tail -1000 "$LOG" | grep -oP 'Epoch \d+ batch \d+/\d+' | tail -1)
echo "---"
echo "LATEST: $LATEST"

# GRAD_NAN events (always from current run — log is dedicated)
NAN_COUNT=$(grep -c "GRAD_NAN" "$LOG" 2>/dev/null || true)
echo "GRAD_NAN events (total): ${NAN_COUNT:-0}"

# Latest LIVENESS_GRAD (grad-norm liveness)
LIVENESS_GRAD=$(grep "LIVENESS_GRAD" "$LOG" | tail -1)
if [ -n "$LIVENESS_GRAD" ]; then
    echo "LIVENESS_GRAD: $LIVENESS_GRAD"
fi

# Latest LIVENESS output-magnitude
LIVENESS_OUT=$(grep "LIVENESS step=" "$LOG" | tail -1)
echo "LIVENESS (output): $LIVENESS_OUT"

# Kendall log_vars from reinit header or runtime
KENDALL=$(grep "Kendall log_var" "$LOG" | tail -1)
echo "LOG_VARS: $KENDALL"

# Loss trend — last 5 non-seq batches (from progress bar lines containing all losses)
echo "---"
echo "Last 5 loss snapshots (non-seq batches):"
tail -1000 "$LOG" | grep -oP \
    'loss=[\d.]+ det=[\d.]+\(c=[\d.]+.*?\) pose=[\d.]+ act=[\d.]+ psr=[\d.]+' \
    | tail -5 | while read -r line; do
    loss=$(echo "$line" | grep -oP 'loss=\K[\d.]+')
    det=$(echo "$line" | grep -oP 'det=\K[\d.]+')
    act=$(echo "$line" | grep -oP 'act=\K[\d.]+')
    psr=$(echo "$line" | grep -oP 'psr=\K[\d.]+')
    pose=$(echo "$line" | grep -oP 'pose=\K[\d.]+')
    printf "  loss=%-8s det=%-8s act=%-8s psr=%-8s pose=%s\n" "$loss" "$det" "$act" "$psr" "$pose"
done

echo ""
echo "Last 3 seq batches (PSR-only):"
tail -1000 "$LOG" | grep -oP 'loss=[\d.]+ det=0.000 pose=0.000 act=0.000 psr=[\d.]+ seq=1' | tail -3

# GPU usage
echo "---"
echo "GPU: $(nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null | head -1)"
