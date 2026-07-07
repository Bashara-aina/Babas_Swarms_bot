#!/usr/bin/env bash
# train_singletask_psr.sh — Launch single-task PSR-only ConvNeXt-Tiny training
#
# Purpose: third single-task baseline — isolates PSR to determine whether
# multi-task training helps or hurts PSR performance.
#
# Current multi-task PSR:  0.7018 F1 (D3)
# V3 (with fix, in flight): target 0.78+ F1
# Single-task PSR:         unknown (key comparison vs multi-task)
#
# OOM safeguard: checks GPU availability before launch. Defer if GPU busy.
#
# Runs the training from the industreal_improved project on the external drive.
# The train_singletask_psr.py patches src.config to enable ONLY the PSR head
# (with the ablation_psr_only preset), then delegates to train.py.
#
# Usage: scripts/train_singletask_psr.sh
#   Monitor: tail -f /tmp/train_singletask_psr.log
#   Kill:    kill "$(cat /tmp/train_singletask_psr_pid 2>/dev/null)"

set -uo pipefail

PROJECT_ROOT="/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved"
LOG_FILE="/tmp/train_singletask_psr.log"
PID_FILE="/tmp/train_singletask_psr_pid"

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
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] BLOCKED: GPU busy — deferring single-task PSR training."
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

# PSR_SEQ_EVERY_N_BATCHES=1: every batch is a sequence batch (recommended
# when PSR is the only head being trained, as per ablation_psr_only preset)
export PSR_SEQ_EVERY_N_BATCHES=1
export TRAIN_MAX_STEPS=0

# ---- Pre-cleanup ----
for _old_pid in $(cat "${PID_FILE}" 2>/dev/null); do
    kill "${_old_pid}" 2>/dev/null || true
done
sleep 2
rm -f "${PID_FILE}"

cd "${PROJECT_ROOT}"

echo "$$" > "${PID_FILE}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Single-task PSR Training"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========================================"
echo ""
echo "  Backbone:        ConvNeXt-Tiny (ablation_psr_only preset)"
echo "  Tasks:           PSR ONLY (detection/pose/activity disabled)"
echo "  Init:            COCO-pretrained backbone (no checkpoint resume)"
echo "  Batch size:      2 (RTX 3060 OOM mitigation)"
echo "  Epochs:          5"
echo "  Precision:       bf16 mixed precision"
echo "  Sequence mode:   PSR_SEQ_EVERY_N_BATCHES=1 (every batch is seq batch)"
echo "  Log file:        ${LOG_FILE}"
echo ""

python -u src/training/train_singletask_psr.py \
    --batch-size 2 \
    --max-epochs 5 \
    --sequence-mode \
    >> "${LOG_FILE}" 2>&1

EXIT_CODE=$?
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Training exited with code ${EXIT_CODE}"
rm -f "${PID_FILE}"
exit ${EXIT_CODE}
