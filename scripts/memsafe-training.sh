#!/usr/bin/env bash
# memsafe-training.sh — Launch training with OOM protection
#
# Prevents desktop freezes by:
#   1. Checking system health before launch
#   2. Setting a cgroup memory limit on training (auto-kill before OOM)
#   3. Monitoring memory pressure and killing training if critical
#   4. Logging memory usage for post-mortem
#
# Usage: ./scripts/memsafe-training.sh [training args...]
#   Pass all args directly to the training command.
#   Example: ./scripts/memsafe-training.sh --batch-size 2 --max-epochs 100
#
# Environment overrides:
#   MEMSAFE_MEM_LIMIT_GB — cgroup memory limit (default: 40)
#   MEMSAFE_PRESSURE_KB — available RAM threshold to kill (default: 2097152 = 2GB)
#   MEMSAFE_CHECK_INTERVAL — monitor check seconds (default: 30)

set -u
ME=$(basename "$0")
LOG_DIR="/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs"
mkdir -p "$LOG_DIR" 2>/dev/null

MONITOR_LOG="$LOG_DIR/memsafe-monitor.log"
PID_FILE="/tmp/memsafe-training.pid"

MEM_LIMIT_GB="${MEMSAFE_MEM_LIMIT_GB:-40}"
PRESSURE_KB="${MEMSAFE_PRESSURE_KB:-2097152}"
CHECK_INTERVAL="${MEMSAFE_CHECK_INTERVAL:-30}"

log() { echo "[$ME] $(date) $*" | tee -a "$MONITOR_LOG"; }

log "Starting memsafe training wrapper"
log "Memory limit: ${MEM_LIMIT_GB}GB, pressure threshold: $(( PRESSURE_KB / 1024 ))MB"

# ---- Health checks ----
total_ram_kb=$(awk '/MemTotal/  {print $2}' /proc/meminfo)
avail_ram_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
log "System RAM: $(( total_ram_kb / 1024 / 1024 ))GB total, $(( avail_ram_kb / 1024 / 1024 ))GB available"

if (( avail_ram_kb < 4194304 )); then
    log "FATAL: Only $(( avail_ram_kb / 1024 / 1024 ))GB RAM available -- need at least 4GB to run"
    exit 1
fi

if command -v nvidia-smi &>/dev/null; then
    while IFS= read -r line; do
        log "$line"
    done < <(nvidia-smi --query-gpu=index,name,memory.free --format=csv,noheader 2>/dev/null)
fi

# ---- Launch training with systemd scope (cgroup v2, no root needed) ----
# systemd-run --user --scope creates a transient scope unit in the user.slice
# with proper cgroup limits. This works without root access.
TRAIN_DIR="/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src"
cd "$TRAIN_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TRAIN_LOG="$LOG_DIR/memsafe-train-${TIMESTAMP}.log"

MEM_LIMIT_BYTES=$(( MEM_LIMIT_GB * 1024 * 1024 * 1024 ))

log "Launching under systemd scope (${MEM_LIMIT_GB}GB mem limit, no swap)"
log "Training log: $TRAIN_LOG"

systemd-run --user --scope --unit="memsafe-training" \
    -p "MemoryMax=${MEM_LIMIT_BYTES}" \
    -p "MemorySwapMax=0" \
    -p "MemoryAccounting=yes" \
    -p "TasksMax=infinity" \
    -q \
    python -m training.train "$@" &>"$TRAIN_LOG" &
TRAIN_PID=$!

echo "$TRAIN_PID" > "$PID_FILE"
log "Training PID: $TRAIN_PID"

# ---- Memory monitor loop ----
cleanup() {
    log "Cleanup triggered"
    if kill -0 "$TRAIN_PID" 2>/dev/null; then
        log "Killing training (PID $TRAIN_PID)"
        kill -TERM "$TRAIN_PID" 2>/dev/null
        sleep 5
        kill -KILL "$TRAIN_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    log "Shutdown complete"
}
trap cleanup EXIT INT TERM

log "Monitoring every ${CHECK_INTERVAL}s (pressure threshold: $(( PRESSURE_KB / 1024 ))MB)"

while kill -0 "$TRAIN_PID" 2>/dev/null; do
    avail_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
    free_kb=$(awk '/MemFree/      {print $2}' /proc/meminfo)
    swap_total=$(awk '/SwapTotal/ {print $2}' /proc/meminfo)
    swap_free=$(awk '/SwapFree/   {print $2}' /proc/meminfo)
    swap_used=$(( swap_total - swap_free ))

    now=$(date +%H:%M:%S)
    echo "[MONITOR] $now avail=${avail_kb}KB swap_used=${swap_used}KB" >> "$MONITOR_LOG"

    if (( avail_kb < PRESSURE_KB )); then
        log "CRITICAL: Available RAM ${avail_kb}KB below threshold ${PRESSURE_KB}KB!"
        log "Killing training to prevent system freeze."
        kill -TERM "$TRAIN_PID" 2>/dev/null || true
        sleep 3
        kill -KILL "$TRAIN_PID" 2>/dev/null || true
        log "Training killed. System should recover."
        exit 2
    fi

    sleep "$CHECK_INTERVAL"
done
wait "$TRAIN_PID" || true
TRAIN_EXIT=$?

case "$TRAIN_EXIT" in
    42) log "Training self-killed (OOM protection: available RAM dropped below 1.5GB)" ;;
    0)  log "Training completed successfully" ;;
    *)  log "Training exited with code $TRAIN_EXIT -- see training log for details" ;;
esac
exit $TRAIN_EXIT
