#!/usr/bin/env bash
# train_singletask_pose.sh — Launch single-task head-pose-only ConvNeXt-Tiny training
#
# Purpose: produce a clean same-architecture pose-only denominator for multi-task
# cost analysis. Multi-task pose: 9.14deg fwd / 7.78deg up. Single-task expected:
# 5-7deg fwd (50% better). If single-task < multi-task, multi-task HELPS pose.
# If single-task > multi-task, multi-task is fine for pose.
#
# OOM safeguard: checks GPU availability before launch. Defer if GPU busy.
#
# Runs the training from the industreal_improved project on the external drive.
# The train_singletask_pose.py patches src.config to enable ONLY the head-pose
# head, then delegates to train.py.
#
# Usage: scripts/train_singletask_pose.sh
#   Monitor: tail -f /tmp/train_singletask_pose.log
#   Kill:    kill "$(cat /tmp/train_singletask_pose_pid 2>/dev/null)"

set -uo pipefail

PROJECT_ROOT="/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved"
LOG_FILE="/tmp/train_singletask_pose.log"
PID_FILE="/tmp/train_singletask_pose_pid"

# ---- GPU availability check ----
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking GPU availability..."
GPU_BUSY=0
while IFS=, read -r idx util mem; do
    idx=$(echo "$idx" | xargs)
    util=$(echo "$util" | xargs | sed 's/%//')
    mem=$(echo "$mem" | xargs | sed 's/ MiB//')
    if [ "$util" -gt 10 ] || [ "$mem" -gt 2000 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] GPU $idx busy: util=${util}%, mem=${mem}MiB"
        GPU_BUSY=1
    fi
done < <(nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader 2>/dev/null)

if [ "$GPU_BUSY" -eq 1 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED: GPU busy — deferring single-task pose training."
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Run again when GPUs are idle."
    exit 1
fi

export CUDA_VISIBLE_DEVICES=0

# ---- Thread / OOM mitigation ----
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export NUMEXPR_NUM_THREADS=4
export MALLOC_ARENA_MAX=4
export RAM_CACHE_MAX_IMAGES=0

# ---- Pre-cleanup ----
for _old_pid in $(cat "${PID_FILE}" 2>/dev/null); do
    kill "${_old_pid}" 2>/dev/null || true
done
sleep 2
rm -f "${PID_FILE}"

cd "${PROJECT_ROOT}"

echo "$$" > "${PID_FILE}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Single-task Head-Pose Training"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========================================"
echo ""
echo "  Backbone:        ConvNeXt-Tiny"
echo "  Tasks:           head-pose ONLY (detection/act/psr disabled)"
echo "  Init:            COCO-pretrained backbone (no checkpoint resume)"
echo "  Batch size:      2 (OOM mitigation)"
echo "  Epochs:          5"
echo "  LR:              5e-4"
echo "  Precision:       bf16 mixed precision"
echo "  Log file:        ${LOG_FILE}"
echo ""

python src/training/train_singletask_pose.py \
    --batch-size 2 \
    --epochs 5 \
    --lr 5e-4 \
    >> "${LOG_FILE}" 2>&1

EXIT_CODE=$?
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Training exited with code ${EXIT_CODE}"
rm -f "${PID_FILE}"
exit ${EXIT_CODE}
