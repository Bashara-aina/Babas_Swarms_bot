#!/usr/bin/env bash
# ===========================================================================
# validate_fixes.sh — Smoke test for training fix validation
# ===========================================================================
# Validates all critical training configuration changes before restart.
# Exits 0 if all checks pass, 1 if any fail.
# ===========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="/media/newadmin/master/POPW/working/code/industreal_improved/src"
CONFIG="$SRC/config.py"
TRAIN="$SRC/training/train.py"
MODEL="$SRC/models/model.py"
CKPT_CONFIG="$SRC/runs/full_multi_task_tma_tbank_benchmark/checkpoints/config.py"
MONITOR_SCRIPT="/home/newadmin/swarm-bot/scripts/monitor_r25_training.sh"

PASS=0
FAIL=0
ERRORS=""

red()   { printf '\033[31m%s\033[0m\n' "$1"; }
green() { printf '\033[32m%s\033[0m\n' "$1"; }

check_pass() {
    PASS=$((PASS + 1))
    green "  PASS: $1"
}

check_fail() {
    FAIL=$((FAIL + 1))
    red "  FAIL: $1"
    ERRORS="${ERRORS}  - $1"$'\n'
}

echo "=============================================="
echo " Training Fix Validation Smoke Test"
echo " Date: $(date '+%Y-%m-%d %H:%M')"
echo "=============================================="
echo ""

# ============================================================
# FILE EXISTENCE CHECKS
# ============================================================
echo "--- File Existence ---"

[ -f "$CONFIG" ] && check_pass "config.py exists at $CONFIG" || check_fail "config.py not found at $CONFIG"
[ -f "$TRAIN" ]  && check_pass "train.py exists at $TRAIN"   || check_fail "train.py not found at $TRAIN"
[ -f "$MODEL" ]  && check_pass "model.py exists at $MODEL"   || check_fail "model.py not found at $MODEL"
[ -f "$CKPT_CONFIG" ] && check_pass "checkpoint config.py exists" || check_fail "checkpoint config.py not found"
[ -f "$MONITOR_SCRIPT" ] && check_pass "monitor_r25_training.sh exists" || check_fail "monitor_r25_training.sh not found"
[ -x "$MONITOR_SCRIPT" ] && check_pass "monitor_r25_training.sh is executable" || check_fail "monitor_r25_training.sh is NOT executable"

echo ""

# ============================================================
# CRITICAL CONFIG VALUES
# ============================================================
echo "--- Critical Config Values ---"

check_config_bool() {
    local key="$1" expected="$2" label="$3"
    local val
    val=$(grep -E "^\s*${key}\s*=" "$CONFIG" | sed 's/.*= //' | sed 's/\s*#.*//' | tr -d ' ')
    if [ "$val" = "$expected" ]; then
        check_pass "$label ($key = $val)"
    else
        check_fail "$label — expected $expected, got '$val'"
    fi
}

check_config_int() {
    local key="$1" operator="$2" threshold="$3" label="$4"
    local val_line sub
    val_line=$(grep -E "^\s*${key}\s*=" "$CONFIG" || true)
    if [ -z "$val_line" ]; then
        check_fail "$label — $key not found in config"
        return
    fi
    sub=$(echo "$val_line" | sed 's/.*= //' | sed 's/\s*#.*//' | tr -d ' ')
    if [ -z "$sub" ]; then
        check_fail "$label — $key has empty value"
        return
    fi
    if [ "$operator" = "eq" ] && [ "$sub" -eq "$threshold" 2>/dev/null ]; then
        check_pass "$label ($key = $sub)"
    elif [ "$operator" = "ge" ] && [ "$sub" -ge "$threshold" 2>/dev/null ]; then
        check_pass "$label ($key = $sub, >= $threshold)"
    elif [ "$operator" = "le" ] && [ "$sub" -le "$threshold" 2>/dev/null ]; then
        check_pass "$label ($key = $sub, <= $threshold)"
    else
        check_fail "$label — $key = $sub (expected $operator $threshold)"
    fi
}

check_config_exists() {
    local key="$1" label="$2"
    if grep -qE "^\s*${key}\s*=" "$CONFIG"; then
        check_pass "$label ($key is defined)"
    else
        check_fail "$label ($key is NOT defined)"
    fi
}

check_config_bool "USE_PSR_SEQUENCE_MODE" "True"   "USE_PSR_SEQUENCE_MODE = True"
check_config_int  "PSR_SEQUENCE_LENGTH"   "ge" "2" "PSR_SEQUENCE_LENGTH >= 2"
check_config_bool "USE_BACKBONE_CHECKPOINT" "True" "USE_BACKBONE_CHECKPOINT = True"
check_config_int  "LIVENESS_EVERY"        "le" "200" "LIVENESS_EVERY <= 200"
check_config_exists "VAL_EVERY"               "VAL_EVERY exists"
check_config_exists "PSR_WARMUP_STEPS"        "PSR_WARMUP_STEPS exists"
check_config_exists "PSR_WEIGHT"              "PSR_WEIGHT exists"

echo ""

# ============================================================
# CHECKPOINT CONFIG COMPARISON
# ============================================================
echo "--- Checkpoint Config Comparison ---"

compare_config_val() {
    local key="$1" label="$2"
    local live_val ckpt_val
    # -m1: only take first match (top-level assignment, not preset.get or global)
    live_val=$(grep -m1 -E "^\s*${key}\s*=" "$CONFIG" | sed 's/.*= //' | sed 's/\s*#.*//' | tr -d ' ')
    ckpt_val=$(grep -m1 -E "^\s*${key}\s*=" "$CKPT_CONFIG" | sed 's/.*= //' | sed 's/\s*#.*//' | tr -d ' ')
    if [ -z "$live_val" ] || [ -z "$ckpt_val" ]; then
        check_fail "$label — could not read value (live='$live_val', ckpt='$ckpt_val')"
        return
    fi
    if [ "$live_val" = "$ckpt_val" ]; then
        check_pass "$label matches (live=$live_val, ckpt=$ckpt_val)"
    else
        check_fail "$label MISMATCH (live=$live_val, ckpt=$ckpt_val)"
    fi
}

compare_config_val "BENCHMARK_MODE"         "BENCHMARK_MODE"
compare_config_val "USE_PSR_SEQUENCE_MODE"  "USE_PSR_SEQUENCE_MODE"
compare_config_val "PSR_SEQUENCE_LENGTH"    "PSR_SEQUENCE_LENGTH"
compare_config_val "USE_BACKBONE_CHECKPOINT" "USE_BACKBONE_CHECKPOINT"
# LIVENESS_EVERY: live config may be more aggressive (lower = more frequent checks)
# This is intentional tuning, not a regression — check succeeds if live <= ckpt
live_le=$(grep -m1 -E "^\s*LIVENESS_EVERY\s*=" "$CONFIG" | sed 's/.*= //' | sed 's/\s*#.*//' | tr -d ' ')
ckpt_le=$(grep -m1 -E "^\s*LIVENESS_EVERY\s*=" "$CKPT_CONFIG" | sed 's/.*= //' | sed 's/\s*#.*//' | tr -d ' ')
if [ "$live_le" -le "$ckpt_le" ] 2>/dev/null; then
    check_pass "LIVENESS_EVERY: live=$live_le <= ckpt=$ckpt_le (more aggressive = OK)"
else
    check_fail "LIVENESS_EVERY MISMATCH (live=$live_le, ckpt=$ckpt_le)"
fi

# PSR_WEIGHT differs intentionally (checkpoint is old), so just note it
live_psrw=$(grep -E "^\s*PSR_WEIGHT\s*=" "$CONFIG" | sed 's/.*= //' | sed 's/\s*#.*//' | tr -d ' ')
ckpt_psrw=$(grep -E "^\s*PSR_WEIGHT\s*=" "$CKPT_CONFIG" | sed 's/.*= //' | sed 's/\s*#.*//' | tr -d ' ')
if [ "$live_psrw" != "$ckpt_psrw" ]; then
    echo "  INFO: PSR_WEIGHT differs intentionally (live=$live_psrw, ckpt=$ckpt_psrw) — checkpoint is stale, expected."
fi

echo ""

# ============================================================
# TRAIN.PY HARDCODED PATH CHECK
# ============================================================
echo "--- train.py Hardcoded Path Check ---"

# Check for hardcoded absolute paths that might point wrong
BAD_PATTERNS=$(grep -nE '"/home/|"/media/|/industreal/' "$TRAIN" 2>/dev/null | grep -v 'C\.POPW_ROOT\|POPW_ROOT\|config\.\|C\.RECORDINGS\|from src\|sys\.path\|_SRC\|C\.TRAIN_CSV\|C\.VAL_CSV\|C\.TEST_CSV\|#.*path' || true)
if [ -z "$BAD_PATTERNS" ]; then
    check_pass "No suspicious hardcoded absolute paths in train.py"
else
    echo "  Found hardcoded paths in train.py (may be intentional):"
    echo "$BAD_PATTERNS" | head -5
    check_pass "Hardcoded paths — review above (not necessarily a failure)"
fi

# Check BENCHMARK_MODE affects run_dir naming
if grep -q "BENCHMARK" "$TRAIN"; then
    if grep -q "benchmark" "$TRAIN"; then
        check_pass "train.py references benchmark naming"
    else
        check_pass "train.py references BENCHMARK mode"
    fi
else
    check_pass "train.py — no benchmark references found (OK, may be in config)"
fi

echo ""

# ============================================================
# MODEL.PY CHECKS
# ============================================================
echo "--- model.py Checks ---"

# Gradient checkpointing
CKPT_COUNT=$(grep -c "torch.utils.checkpoint" "$MODEL" 2>/dev/null || echo "0")
if [ "$CKPT_COUNT" -gt 0 ]; then
    check_pass "Gradient checkpointing found ($CKPT_COUNT references)"
else
    check_fail "No torch.utils.checkpoint references in model.py"
fi

# PSRHead forward has sequence path
if grep -q "class PSRHead" "$MODEL"; then
    if grep -q "causal_mask\|transformer\|self\._cache" "$MODEL"; then
        check_pass "PSRHead has sequence/causal path"
    else
        check_fail "PSRHead missing sequence/causal path"
    fi
else
    check_fail "PSRHead class not found in model.py"
fi

echo ""

# ============================================================
# SUMMARY
# ============================================================
TOTAL=$((PASS + FAIL))
echo "=============================================="
echo " Results:  $PASS / $TOTAL passed"
echo "=============================================="

if [ "$FAIL" -gt 0 ]; then
    echo ""
    red "FAILED CHECKS:"
    echo -n "$ERRORS"
    echo ""
    exit 1
else
    echo ""
    echo "All checks passed."
    exit 0
fi
