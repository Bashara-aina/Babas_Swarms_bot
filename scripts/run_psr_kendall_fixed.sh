#!/usr/bin/env bash
# =============================================================================
# Run PSR training with KENDALL_FIXED_WEIGHTS=1 (fixed-Kendall ablation).
#
# Per Opus v8: fixes detection head-weights so the backbone is driven by
# detection loss instead of learned-Kendall's head_pose over-weighting.
#
# Env-driven (no code edit needed): KENDALL_FIXED_WEIGHTS=1
#   → config.py line 96 reads os.environ.get('KENDALL_FIXED_WEIGHTS', '0') == '1'
#   → Fixed λ=0.2 for head_pose (KENDALL_HP_FIXED_LAMBDA, config.py line 108)
#   → KENDALL_HP_PREC_CAP=True remains active (config.py line 89)
#
# Usage:
#   ./scripts/run_psr_kendall_fixed.sh
# =============================================================================
set -euo pipefail

# ── Hardware ─────────────────────────────────────────────────────────────────
export CUDA_VISIBLE_DEVICES=0          # RTX 5060 Ti

# ── Ablation env vars ────────────────────────────────────────────────────────
export KENDALL_FIXED_WEIGHTS=1         # Fixed weights instead of learned Kendall
# NOTE: KENDALL_HP_FIXED_LAMBDA defaults to 0.2 (config.py line 108)
# NOTE: KENDALL_HP_PREC_CAP defaults to True  (config.py line 89)
# Both are the correct values for this ablation — no override needed.

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT="/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved"
CHECKPOINT="${PROJECT_ROOT}/src/runs/full_multi_task_tma_tbank_benchmark/checkpoints/crash_recovery.pth"
LOG_FILE="/tmp/train_kendall_fixed.log"

# ── Launch ───────────────────────────────────────────────────────────────────
cd "${PROJECT_ROOT}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Launching KENDALL_FIXED_WEIGHTS=1 training..."
echo "  Checkpoint: ${CHECKPOINT}"
echo "  Batch size: 2 (avoids CUDA timeout on RTX 5060 Ti)"
echo "  Log file:   ${LOG_FILE}"
echo ""

python src/training/train.py \
    --batch-size 2 \
    --resume "${CHECKPOINT}" \
    >> "${LOG_FILE}" 2>&1

EXIT_CODE=$?
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Training exited with code ${EXIT_CODE}"
exit ${EXIT_CODE}
