#!/usr/bin/env bash
# Replay evaluation on an old checkpoint with the current eval code.
# Usage: ./replay_epoch_eval.sh epoch_8.pth
set -e

CKPT=$1
if [ -z "$CKPT" ]; then
  echo "Usage: $0 <checkpoint_filename>"
  exit 1
fi

CKPT_PATH="/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/rf_stages/checkpoints/$CKPT"
OUT_DIR="/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/rf_stages/checkpoints/replay_eval"
mkdir -p "$OUT_DIR"

cd /media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved

CUDA_VISIBLE_DEVICES=1 python3 src/evaluation/subprocess_eval.py \
  --ckpt "$CKPT_PATH" \
  --out_path "$OUT_DIR/${CKPT%.pth}_replay.json" \
  --EVAL_MAX_BATCHES 0
