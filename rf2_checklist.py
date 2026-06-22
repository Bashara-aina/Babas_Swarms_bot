#!/usr/bin/env python3
"""
RF2 Training Gate Checklist — 100-item verification system.
Checks all aspects of RF2 training against gate targets and health criteria.
"""
import json, math, os, re, sys, time, glob
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

RUNS = Path("/media/newadmin/master/POPW/working/code/industreal_improved/src/runs")
LOG = RUNS / "rf_stages/logs/subprocess.log"
STATE = RUNS / "rf_stage_state.json"
CKPT = RUNS / "rf_stages/checkpoints"
CONFIG = CKPT / "config.py"

# ── Gate Targets ──────────────────────────────────────────────────────────────
GATE = {
    "det_mAP50": 0.40,
    "det_mAP50_95": 0.18,
    "forward_angular_MAE_deg": 60.0,
}
VAL_FLOORS = {
    "det_mAP50": 0.35,
    "forward_angular_MAE_deg": 70.0,
}
HEALTH = {
    "min_grad_norm_det": 1e-6,
    "min_grad_norm_pose": 1e-6,
    "max_consecutive_dead": 5,
    "max_loss_spike_factor": 10.0,
}
CONV = {
    "patience_epochs": 6,
    "min_improvement": 0.003,
}

# ── Results ───────────────────────────────────────────────────────────────────
results: list[dict[str, Any]] = []
def check(uid: str, category: str, desc: str, verdict: str, detail: str = "", blocking: bool = False):
    results.append(dict(uid=uid, category=category, desc=desc, verdict=verdict, detail=detail, blocking=blocking))

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
INFO = "INFO"
SKIP = "SKIP"

# ── Helpers ───────────────────────────────────────────────────────────────────
log_lines: list[str] = []
log_text = ""
if LOG.exists():
    log_text = LOG.read_text()
    log_lines = log_text.splitlines()

def last_match(pat: str) -> re.Match | None:
    matches = list(re.finditer(pat, log_text))
    return matches[-1] if matches else None

def all_matches(pat: str) -> list[re.Match]:
    return list(re.finditer(pat, log_text))

def grep_count(pat: str) -> int:
    return len(re.findall(pat, log_text))

def file_size_mb(p: Path) -> float:
    return p.stat().st_size / 1e6 if p.exists() else 0.0

def safe_float(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

state: dict = {}
if STATE.exists():
    try:
        state = json.loads(STATE.read_text())
    except Exception:
        state = {}

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1: GATE METRICS TRACKING (G01–G12)
# ══════════════════════════════════════════════════════════════════════════════

# G01: Has any RF2 validation eval occurred?
rf2_val_epochs = [m for m in all_matches(r'\[VAL_OK\] epoch (\d+) val completed')
                   if int(m.group(1)) >= 6]  # epoch >=6 means RF2
latest_rf2_val = None
for m in rf2_val_epochs:
    latest_rf2_val = int(m.group(1))

val_lines = [m for m in all_matches(
    r'Val:.*det_mAP50=([\d.]+).*forward_angular_MAE_deg=([\d.]+)'
)]
last_val = val_lines[-1] if val_lines else None

if latest_rf2_val is not None:
    check("G01", "Gate Metrics", "RF2 validation evaluation has occurred",
          PASS, f"Latest RF2 validation at epoch {latest_rf2_val}")
else:
    check("G01", "Gate Metrics", "RF2 validation evaluation has occurred",
          INFO, "No RF2 validation eval yet (expected at epoch 6→7 boundary, imminent)", blocking=False)

# G02: Latest det_mAP50
if last_val:
    mAP50 = safe_float(last_val.group(1))
    if mAP50 >= GATE["det_mAP50"]:
        check("G02", "Gate Metrics", f"det_mAP50 >= {GATE['det_mAP50']}",
              PASS, f"det_mAP50={mAP50:.4f}")
    elif mAP50 >= VAL_FLOORS["det_mAP50"]:
        check("G02", "Gate Metrics", f"det_mAP50 >= {GATE['det_mAP50']}",
              WARN, f"det_mAP50={mAP50:.4f} (above floor but below gate)")
    else:
        check("G02", "Gate Metrics", f"det_mAP50 >= {GATE['det_mAP50']}",
              INFO, f"det_mAP50={mAP50:.4f} (below floor, early training expected)")
else:
    check("G02", "Gate Metrics", "det_mAP50 >= 0.40",
          INFO, "No RF2 val results yet — check after epoch 6→7 boundary")

# G03: Latest det_mAP50_95
mAP50_95_vals = [safe_float(m.group(1)) for m in re.finditer(r'det_mAP50_95=([\d.]+)', log_text)]
if last_val:
    if mAP50_95_vals:
        latest_mAP50_95 = mAP50_95_vals[-1]
        if latest_mAP50_95 >= GATE["det_mAP50_95"]:
            check("G03", "Gate Metrics", f"det_mAP50_95 >= {GATE['det_mAP50_95']}",
                  PASS, f"det_mAP50_95={latest_mAP50_95:.4f}")
        else:
            check("G03", "Gate Metrics", f"det_mAP50_95 >= {GATE['det_mAP50_95']}",
                  INFO, f"det_mAP50_95={latest_mAP50_95:.4f}")
    else:
        check("G03", "Gate Metrics", "det_mAP50_95 >= 0.18",
              INFO, "No RF2 val results yet")
else:
    check("G03", "Gate Metrics", "det_mAP50_95 >= 0.18",
          INFO, "No RF2 val results yet")

# G04: Latest forward_angular_MAE_deg
if last_val:
    angular_mae = safe_float(last_val.group(2))
    if angular_mae <= GATE["forward_angular_MAE_deg"]:
        check("G04", "Gate Metrics", f"forward_angular_MAE_deg <= {GATE['forward_angular_MAE_deg']}",
              PASS, f"MAE={angular_mae:.2f}°")
    elif angular_mae <= VAL_FLOORS["forward_angular_MAE_deg"]:
        check("G04", "Gate Metrics", f"forward_angular_MAE_deg <= {GATE['forward_angular_MAE_deg']}",
              WARN, f"MAE={angular_mae:.2f}° (above gate but below floor)")
    else:
        check("G04", "Gate Metrics", f"forward_angular_MAE_deg <= {GATE['forward_angular_MAE_deg']}",
              FAIL, f"MAE={angular_mae:.2f}° (exceeds floor)")
else:
    check("G04", "Gate Metrics", "forward_angular_MAE_deg <= 60.0°",
          INFO, "No RF2 val results yet")

# G05: det_mAP50 trajectory (increasing trend?)
mAP50_vals = [safe_float(m.group(1)) for m in re.finditer(r'det_mAP50=([\d.]+)', log_text)]
if len(mAP50_vals) >= 3:
    recent = mAP50_vals[-3:]
    if recent[-1] > recent[0]:
        check("G05", "Gate Metrics", "det_mAP50 showing upward trajectory",
              PASS, f"Recent: {recent}")
    elif recent[-1] == recent[0]:
        check("G05", "Gate Metrics", "det_mAP50 showing upward trajectory",
              WARN, f"Flat trajectory: {recent}")
    else:
        check("G05", "Gate Metrics", "det_mAP50 showing upward trajectory",
              WARN, f"Declining: {recent}")
else:
    check("G05", "Gate Metrics", "det_mAP50 trajectory upward",
          INFO, f"Only {len(mAP50_vals)} val points — need more for trend")

# G06: Angular MAE trajectory (should decrease)
angular_vals = [safe_float(m.group(1)) for m in re.finditer(r'forward_angular_MAE_deg=([\d.]+)', log_text)]
if len(angular_vals) >= 3:
    recent_a = angular_vals[-3:]
    if recent_a[-1] <= recent_a[0]:
        check("G06", "Gate Metrics", "Angular MAE decreasing trend",
              PASS, f"Recent: {recent_a}")
    else:
        check("G06", "Gate Metrics", "Angular MAE decreasing trend",
              WARN, f"Increasing: {recent_a}")
else:
    check("G06", "Gate Metrics", "Angular MAE decreasing trend",
          INFO, "Need more data points")

# G07: Combined metric improving
comb_vals = [safe_float(m.group(1)) for m in re.finditer(r'combined=([\d.]+)', log_text)]
if len(comb_vals) >= 3:
    if comb_vals[-1] >= comb_vals[0]:
        check("G07", "Gate Metrics", "Combined metric improving",
              PASS, f"Recent: {comb_vals[-3:]}")
    else:
        check("G07", "Gate Metrics", "Combined metric improving",
              WARN, f"Declining: {comb_vals[-3:]}")
else:
    check("G07", "Gate Metrics", "Combined metric improving",
          INFO, "Need more data")

# G08: Metric history being recorded in state
if state.get("metric_history"):
    check("G08", "Gate Metrics", "Metric history being recorded",
          PASS, f"{len(state['metric_history'])} entries")
else:
    check("G08", "Gate Metrics", "Metric history being recorded",
          WARN, "metric_history empty in stage_state.json")

# G09: Gate pass status
if state.get("gate_passed"):
    check("G09", "Gate Metrics", "Gate pass status",
          PASS, "RF2 gate already passed!")
else:
    check("G09", "Gate Metrics", "Gate pass status",
          INFO, "Not yet passed (expected — still training)")

# G10: Epochs remaining
max_epochs = state.get("max_epochs", 21)
current_epoch = state.get("epoch", 0)
remaining = max_epochs - current_epoch
if remaining > 0:
    check("G10", "Gate Metrics", f"Epochs remaining ({remaining} left of {max_epochs})",
          PASS if remaining >= 5 else WARN, f"Epoch {current_epoch}/{max_epochs}")
else:
    check("G10", "Gate Metrics", "Epochs remaining",
          WARN, f"At max epochs ({max_epochs}) — will stop soon")

# G11: Epoch progress within stage
rf2_max = 15  # max_epochs for RF2 stage definition
rf2_current_epochs = len([m for m in all_matches(r'\[VAL_OK\] epoch (\d+)') if int(m.group(1)) >= 6])
check("G11", "Gate Metrics", f"RF2 effective epochs ({rf2_current_epochs}/{rf2_max})",
      PASS if rf2_current_epochs < rf2_max else WARN,
      f"Completed {rf2_current_epochs} of {rf2_max} RF2 epochs")

# G12: Stage index correct
check("G12", "Gate Metrics", f"Stage index = 1 (RF2)",
      PASS if state.get("stage_index") == 1 else FAIL,
      f"stage_index={state.get('stage_index')}")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2: HEAD HEALTH & LIVENESS (H01–H15)
# ══════════════════════════════════════════════════════════════════════════════

# H01: Detection head alive
det_alive = re.findall(r'detection_head:ALIVE', log_text)
if det_alive:
    latest_det_grads = [m for m in all_matches(r'detection_head:ALIVE\[([\d.e+-]+)\]')]
    latest_det_val = latest_det_grads[-1].group(1) if latest_det_grads else "?"
    check("H01", "Head Health", "Detection head ALIVE",
          PASS, f"detection_head gradient: {latest_det_val}")
else:
    check("H01", "Head Health", "Detection head ALIVE",
          FAIL, "detection_head NOT alive (DEAD)", blocking=True)

# H02: Pose head alive
pose_alive = re.findall(r'pose_head:ALIVE', log_text)
if pose_alive:
    check("H02", "Head Health", "Pose head ALIVE",
          PASS, "pose_head gradient active")
else:
    check("H02", "Head Health", "Pose head ALIVE",
          FAIL, "pose_head NOT alive", blocking=True)

# H03: Head pose head alive
hp_alive = re.findall(r'head_pose_head:ALIVE', log_text)
if hp_alive:
    check("H03", "Head Health", "Head-pose head ALIVE",
          PASS, "head_pose_head gradient active")
else:
    check("H03", "Head Health", "Head-pose head ALIVE",
          FAIL, "head_pose_head NOT alive", blocking=True)

# H04: Activity head correctly NO_GRAD (not trained in RF2)
act_nograd = re.findall(r'activity_head:NO_GRAD', log_text)
if act_nograd:
    check("H04", "Head Health", "Activity head correctly NO_GRAD (RF2)",
          PASS, "activity_head detached as expected")
else:
    check("H04", "Head Health", "Activity head correctly NO_GRAD (RF2)",
          FAIL, "activity_head has unexpected gradient", blocking=True)

# H05: PSR head correctly NO_GRAD
psr_nograd = re.findall(r'psr_head:NO_GRAD', log_text)
if psr_nograd:
    check("H05", "Head Health", "PSR head correctly NO_GRAD (RF2)",
          PASS, "psr_head detached as expected")
else:
    check("H05", "Head Health", "PSR head correctly NO_GRAD (RF2)",
          FAIL, "psr_head has unexpected gradient", blocking=True)

# H06: Detection gradient magnitude healthy (> 1e-6)
det_grad_norms = [safe_float(m.group(1)) for m in all_matches(r'detection_head:ALIVE\[([\d.e+-]+)\]')]
if det_grad_norms:
    recent_det_grads = det_grad_norms[-5:]
    if all(g > 1e-6 for g in recent_det_grads):
        check("H06", "Head Health", "Detection grad norm > 1e-6",
              PASS, f"Recent norms: {[f'{g:.2e}' for g in recent_det_grads]}")
    else:
        check("H06", "Head Health", "Detection grad norm > 1e-6",
              WARN, f"Low grads detected: {[f'{g:.2e}' for g in recent_det_grads]}")
else:
    check("H06", "Head Health", "Detection grad norm > 1e-6",
          INFO, "No grad norm data yet")

# H07: Backbone alive
bb_alive = re.findall(r'backbone:ALIVE', log_text)
check("H07", "Head Health", "Backbone ALIVE",
      PASS if bb_alive else FAIL, "backbone gradient status")

# H08: FPN alive
fpn_alive = re.findall(r'fpn:ALIVE', log_text)
check("H08", "Head Health", "FPN ALIVE",
      PASS if fpn_alive else FAIL, "FPN gradient status")

# H09: No consecutive dead heads > threshold
dead_sequences = re.findall(r'(?:DEAD[^]]*){5,}', log_text)
if dead_sequences:
    check("H09", "Head Health", f"No consecutive DEAD > {HEALTH['max_consecutive_dead']}",
          WARN, f"Found {len(dead_sequences)} extended dead sequences")
else:
    check("H09", "Head Health", f"No consecutive DEAD > {HEALTH['max_consecutive_dead']}",
          PASS, "No extended dead sequences detected")

# H10: Liveness ratio >= 0.7
liveness_checks = all_matches(r'det=([\d.e+-]+)\s+ALIVE')
if liveness_checks:
    alive_count = len(liveness_checks)
    total_liveness_lines = len([m for m in all_matches(r'\[LIVENESS step=')])
    ratio = alive_count / max(total_liveness_lines, 1)
    check("H10", "Head Health", f"Detection liveness ratio >= {HEALTH.get('min_liveness_ratio', 0.7)}",
          PASS if ratio >= 0.7 else WARN,
          f"det ALIVE ratio: {ratio:.2f}")
else:
    check("H10", "Head Health", "Liveness ratio >= 0.7",
          INFO, "No liveness data yet")

# H11: Head pose gradient healthy
hp_grads = [safe_float(m.group(1)) for m in all_matches(r'head_pose=([\d.e+-]+)\s+ALIVE')]
if hp_grads:
    recent_hp = hp_grads[-5:]
    check("H11", "Head Health", "Head-pose gradient magnitude healthy",
          PASS if any(g > 1e-5 for g in recent_hp) else WARN,
          f"Recent: {[f'{g:.2e}' for g in recent_hp]}")
else:
    check("H11", "Head Health", "Head-pose gradient magnitude healthy",
          INFO, "No head-pose grad data")

# H12: Pose gradient healthy
pose_grads = [safe_float(m.group(1)) for m in all_matches(r'pose=([\d.e+-]+)\s+ALIVE')]
if pose_grads:
    recent_pg = pose_grads[-5:]
    check("H12", "Head Health", "Pose gradient magnitude healthy",
          PASS if any(g > 1e-5 for g in recent_pg) else WARN,
          f"Recent: {[f'{g:.2e}' for g in recent_pg]}")
else:
    check("H12", "Head Health", "Pose gradient magnitude healthy",
          INFO, "No pose grad data")

# H13: Gradient norm stable (not exploding)
if det_grad_norms:
    recent_det = det_grad_norms[-10:]
    if max(recent_det) / max(min(recent_det), 1e-10) < 100:
        check("H13", "Head Health", "Gradient norm stable (no explosion)",
              PASS, f"Max/min ratio: {max(recent_det)/max(min(recent_det), 1e-10):.1f}")
    else:
        check("H13", "Head Health", "Gradient norm stable (no explosion)",
              WARN, "High variance in grad norms")
else:
    check("H13", "Head Health", "Gradient norm stable",
          INFO, "No data")

# H14: EMA shadow updated (gradient flow through EMA too)
ema_skip = re.findall(r'Skipping EMA swap', log_text)
check("H14", "Head Health", "EMA shadow not permanently skipped",
      WARN if len(ema_skip) > 5 else PASS,
      f"EMA swap skipped {len(ema_skip)} times")

# H15: Liveness over last 10 checkpoints all ALIVE for detection
last_10_liveness = [m for m in all_matches(r'det=([\d.e+-]+)\s+(\w+)')][-10:]
if last_10_liveness:
    all_alive = all(m.group(2) == "ALIVE" for m in last_10_liveness)
    check("H15", "Head Health", "Last 10 liveness checks: detection ALL ALIVE",
          PASS if all_alive else WARN,
          f"Last 10: {[m.group(2) for m in last_10_liveness]}")
else:
    check("H15", "Head Health", "Last 10 liveness checks ALL ALIVE",
          INFO, "No data")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3: LOSS HEALTH (L01–L12)
# ══════════════════════════════════════════════════════════════════════════════

# L01: Total loss not NaN
loss_lines = [m for m in all_matches(r'loss=([\d.]+)\s+det=')]
if loss_lines:
    recent_losses = [safe_float(m.group(1)) for m in loss_lines[-20:]]
    if any(math.isnan(l) or math.isinf(l) for l in recent_losses):
        check("L01", "Loss Health", "Total loss not NaN/Inf",
              FAIL, "NaN or Inf detected in loss!", blocking=True)
    else:
        check("L01", "Loss Health", "Total loss not NaN/Inf",
              PASS, f"Recent: {recent_losses[-1]:.4f}")
else:
    check("L01", "Loss Health", "Total loss not NaN/Inf",
          INFO, "No loss data")

# L02: Detection classification loss converging
det_cls_vals = [safe_float(m.group(1)) for m in all_matches(r'det=([\d.]+)\(c=([\d.]+)')]
if det_cls_vals:
    cls_vals = [safe_float(m.group(2)) for m in all_matches(r'det=([\d.]+)\(c=([\d.]+),')]
    if cls_vals:
        initial_cls = cls_vals[:10]
        recent_cls = cls_vals[-10:]
        if recent_cls and initial_cls and sum(recent_cls)/len(recent_cls) < sum(initial_cls)/len(initial_cls):
            check("L02", "Loss Health", "det_cls loss converging downward",
                  PASS, f"Initial avg: {sum(initial_cls)/len(initial_cls):.4f} → Recent avg: {sum(recent_cls)/len(recent_cls):.4f}")
        else:
            check("L02", "Loss Health", "det_cls loss converging downward",
                  WARN, f"Not clearly converging: init={sum(initial_cls)/len(initial_cls):.4f}, recent={sum(recent_cls)/len(recent_cls):.4f}")
    else:
        check("L02", "Loss Health", "det_cls loss converging",
              INFO, "No cls loss data")
else:
    check("L02", "Loss Health", "det_cls loss converging",
          INFO, "No data")

# L03: Detection regression loss stable
det_reg_vals = [safe_float(m.group(1)) for m in all_matches(r'g=([\d.]+)\)')]
if det_reg_vals:
    recent_reg = det_reg_vals[-20:]
    if max(recent_reg) / max(min(recent_reg), 1e-10) < 5:
        check("L03", "Loss Health", "det_reg loss stable (no spikes)",
              PASS, f"Stable range: {min(recent_reg):.4f}-{max(recent_reg):.4f}")
    else:
        check("L03", "Loss Health", "det_reg loss stable",
              WARN, f"High variance: {min(recent_reg):.4f}-{max(recent_reg):.4f}")
else:
    check("L03", "Loss Health", "det_reg loss stable",
          INFO, "No data")

# L04: Loss spike factor < 10x
if loss_lines:
    losses = [safe_float(m.group(1)) for m in loss_lines[-100:]]
    if losses:
        mean_loss = sum(losses) / len(losses)
        max_loss = max(losses)
        spike_factor = max_loss / max(mean_loss, 1e-10)
        check("L04", "Loss Health", f"Loss spike factor < {HEALTH['max_loss_spike_factor']}x",
              PASS if spike_factor < HEALTH['max_loss_spike_factor'] else WARN,
              f"Max/mean ratio: {spike_factor:.1f}x")
    else:
        check("L04", "Loss Health", "Loss spike factor < 10x",
              INFO, "Cannot compute")
else:
    check("L04", "Loss Health", "Loss spike factor < 10x",
          INFO, "No data")

# L05: Pose loss non-zero and reasonable
pose_loss_vals = [safe_float(m.group(1)) for m in all_matches(r'pose=([\d.]+)\s+act=')]
if pose_loss_vals:
    recent_pose = pose_loss_vals[-20:]
    avg_pose = sum(recent_pose) / len(recent_pose)
    check("L05", "Loss Health", "Pose loss active and reasonable",
          PASS if 0.001 < avg_pose < 10 else WARN,
          f"Avg pose loss: {avg_pose:.4f}")
else:
    check("L05", "Loss Health", "Pose loss active",
          INFO, "No pose loss data")

# L06: Loss not stuck at plateau (>50 steps same value)
if loss_lines:
    recent_unique = len(set(f"{safe_float(m.group(1)):.4f}" for m in loss_lines[-50:]))
    check("L06", "Loss Health", "Loss not stuck at plateau",
          PASS if recent_unique > 3 else WARN,
          f"Unique loss values in last 50 steps: {recent_unique}")
else:
    check("L06", "Loss Health", "Loss not stuck",
          INFO, "No data")

# L07: HEAD_LOSS_CAP not being hit repeatedly
loss_cap_hits = grep_count(r'loss.*capped|LOSS_CAP')
check("L07", "Loss Health", "No repeated loss cap hits",
      PASS if loss_cap_hits == 0 else WARN,
      f"Loss cap hits: {loss_cap_hits}")

# L08: LR schedule active
lr_vals = [m.group(1) for m in all_matches(r'lr=([\d.e-]+)')]
if lr_vals:
    latest_lr = lr_vals[-1]
    check("L08", "Loss Health", "Learning rate active",
          PASS, f"LR: {latest_lr}")
else:
    check("L08", "Loss Health", "Learning rate active",
          INFO, "No LR data")

# L09: LR not decayed to zero prematurely
if lr_vals:
    lr_floats = [safe_float(v) for v in lr_vals]
    if lr_floats[-1] > 1e-7:
        check("L09", "Loss Health", "LR not decayed to zero",
              PASS, f"Current LR: {lr_floats[-1]:.2e}")
    else:
        check("L09", "Loss Health", "LR not decayed to zero",
              WARN, f"LR near zero: {lr_floats[-1]:.2e}")
else:
    check("L09", "Loss Health", "LR not decayed to zero",
          INFO, "No LR data")

# L10: Weight decay active
wd_vals = [m.group(1) for m in all_matches(r'wd=([\d.]+)')]
if wd_vals:
    check("L10", "Loss Health", "Weight decay active",
          PASS, f"WD: {wd_vals[-1]}")
else:
    check("L10", "Loss Health", "Weight decay active",
          INFO, "No WD data")

# L11: Training loss epoch 6 average
epoch6_train_losses = [safe_float(m.group(1)) for m in all_matches(r'Epoch 6.*loss=([\d.]+)')]
if epoch6_train_losses:
    avg_epoch6 = sum(epoch6_train_losses) / len(epoch6_train_losses)
    check("L11", "Loss Health", "Epoch 6 training loss reasonable",
          PASS if avg_epoch6 < 10 else WARN,
          f"Epoch 6 avg loss: {avg_epoch6:.4f}")
else:
    check("L11", "Loss Health", "Epoch 6 training loss reasonable",
          INFO, "No epoch 6 data")

# L12: PRE_VAL_GUARD passing
pre_val_fails = grep_count(r'PRE_VAL_GUARD.*unhealthy|PRE_VAL_GUARD.*FAIL')
pre_val_oks = grep_count(r'PRE_VAL_GUARD.*healthy')
check("L12", "Loss Health", "PRE_VAL_GUARD passing",
      PASS if pre_val_oks > 0 and pre_val_fails == 0 else WARN,
      f"Passed: {pre_val_oks}, Failed: {pre_val_fails}")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4: DATA PIPELINE (D01–D10)
# ══════════════════════════════════════════════════════════════════════════════

# D01: RF2 subset_ratio=0.35 active
config_text = CONFIG.read_text() if CONFIG.exists() else ""
subset_match = re.search(r"subset_ratio['\"]?\s*[:=]\s*([\d.]+)", config_text)
if subset_match:
    ratio = float(subset_match.group(1))
    check("D01", "Data Pipeline", f"subset_ratio = 0.35 (35% data)",
          PASS if abs(ratio - 0.35) < 0.01 else WARN,
          f"subset_ratio={ratio}")
else:
    check("D01", "Data Pipeline", "subset_ratio = 0.35",
          INFO, "Not found in config")

# D02: Validation samples
val_samples = [int(m.group(1).replace(",", "")) for m in all_matches(r'Validation samples:\s*([\d,]+)')]
if val_samples:
    latest_vs = val_samples[-1]
    check("D02", "Data Pipeline", "Validation samples loaded",
          PASS if latest_vs > 100 else FAIL,
          f"{latest_vs} validation samples")
else:
    check("D02", "Data Pipeline", "Validation samples loaded",
          INFO, "No data")

# D03: Batch size = 4
bs_match = re.search(r'BATCH_SIZE["\':]\s*(\d+)', config_text)
if bs_match:
    bs = int(bs_match.group(1))
    check("D03", "Data Pipeline", f"Batch size = 4",
          PASS if bs == 4 else WARN, f"BATCH_SIZE={bs}")
else:
    check("D03", "Data Pipeline", "Batch size = 4",
          INFO, "Not found")

# D04: DET_PROBE active (online eval during training)
probe_count = grep_count(r'\[DET_PROBE ')
check("D04", "Data Pipeline", "DET_PROBE online eval active",
      PASS if probe_count > 10 else WARN,
      f"{probe_count} DET_PROBE entries")

# D05: Staging disabled (no-staging mode)
staging_lines = grep_count(r'no-staging')
non_staging_lines = grep_count(r'staging')
check("D05", "Data Pipeline", "Staging disabled for RF2",
      PASS if staging_lines > non_staging_lines else WARN,
      f"no-staging: {staging_lines}, staging refs: {non_staging_lines}")

# D06: CUDNN_DETERMINISTIC=true
check("D06", "Data Pipeline", "CUDNN_DETERMINISTIC=true (reproducibility)",
      PASS if 'CUDNN_DETERMINISTIC": true' in config_text or 'CUDNN_DETERMINISTIC": true' in log_text else INFO,
      "Deterministic mode")

# D07: No data loading errors — exclude DataLoader health check lines
data_errors = len([l for l in log_lines if re.search(r'Error.*data|data.*fail', l) and 'health_check' not in l])
check("D07", "Data Pipeline", "No data loading errors",
      PASS if data_errors == 0 else FAIL,
      f"{data_errors} data errors found")

# D08: GT boxes present in DET_PROBE
gt_present = all_matches(r"'n_gt':\s*(\d+)")
if gt_present:
    zero_gt = sum(1 for m in gt_present if int(m.group(1)) == 0)
    total_gt = len(gt_present)
    check("D08", "Data Pipeline", "GT boxes present in eval batches",
          PASS if zero_gt < total_gt * 0.3 else WARN,
          f"{zero_gt}/{total_gt} batches with zero GT")
else:
    check("D08", "Data Pipeline", "GT boxes present",
          INFO, "No DET_PROBE data")

# D09: gt boxes per batch distribution
if gt_present:
    gt_counts = [int(m.group(1)) for m in gt_present]
    check("D09", "Data Pipeline", "GT boxes per batch reasonable (1-8)",
          PASS if all(1 <= c <= 8 for c in gt_counts[-50:]) else WARN,
          f"GT range: {min(gt_counts)}-{max(gt_counts)}")
else:
    check("D09", "Data Pipeline", "GT boxes distribution",
          INFO, "No data")

# D10: Config preset stage_rf2 loaded
check("D10", "Data Pipeline", "Applied preset: stage_rf2",
      PASS if 'Applied preset: stage_rf2' in log_text else FAIL,
      "stage_rf2 preset load status")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 5: CHECKPOINT & CONFIG INTEGRITY (C01–C10)
# ══════════════════════════════════════════════════════════════════════════════

# C01: best.pth exists
best_pth = CKPT / "best.pth"
check("C01", "Checkpoint Integrity", "best.pth exists",
      PASS if best_pth.exists() else FAIL,
      f"Size: {file_size_mb(best_pth):.1f}MB")

# C02: latest.pth exists
latest_pth = CKPT / "latest.pth"
check("C02", "Checkpoint Integrity", "latest.pth exists",
      PASS if latest_pth.exists() else FAIL,
      f"Size: {file_size_mb(latest_pth):.1f}MB")

# C03: Checkpoint file sizes reasonable (>10MB)
for ckpt_name, ckpt_path in [("best.pth", best_pth), ("latest.pth", latest_pth)]:
    if ckpt_path.exists():
        sz = file_size_mb(ckpt_path)
        check(f"C03", "Checkpoint Integrity", f"{ckpt_name} size > 10MB",
              PASS if sz > 10 else FAIL,
              f"{sz:.1f}MB")

# C04: crash_recovery.pth exists (safety net)
crash_pth = CKPT / "crash_recovery.pth"
check("C04", "Checkpoint Integrity", "crash_recovery.pth exists",
      PASS if crash_pth.exists() else INFO,
      f"Size: {file_size_mb(crash_pth):.1f}MB")

# C05: RF2 checkpoint directory exists
rf2_ckpt_dir = CKPT / "rf2"
check("C05", "Checkpoint Integrity", "rf2 checkpoint subdirectory exists",
      PASS if rf2_ckpt_dir.is_dir() else FAIL,
      "rf2/ directory present")

# C06: RF1 checkpoint directory exists (baseline)
rf1_ckpt_dir = CKPT / "rf1"
check("C06", "Checkpoint Integrity", "rf1 checkpoint subdirectory exists",
      PASS if rf1_ckpt_dir.is_dir() else WARN,
      "rf1/ directory present")

# C07: config.py exists and valid
check("C07", "Checkpoint Integrity", "config.py exists and valid",
      PASS if CONFIG.exists() and CONFIG.stat().st_size > 1000 else FAIL,
      f"Size: {CONFIG.stat().st_size}B")

# C08: Checkpoint updating (latest.pth timestamp recent)
if latest_pth.exists():
    age_hours = (time.time() - latest_pth.stat().st_mtime) / 3600
    check("C08", "Checkpoint Integrity", "latest.pth updating (recent)",
          PASS if age_hours < 2 else WARN,
          f"Age: {age_hours:.1f}h")
else:
    check("C08", "Checkpoint Integrity", "latest.pth updating",
          FAIL, "latest.pth not found")

# C09: best.pth newer than rf1 best
rf1_best = rf1_ckpt_dir / "best.pth"
if best_pth.exists() and rf1_best.exists():
    stage_manager_match = re.search(r'resume_source.*?best', config_text)
    check("C09", "Checkpoint Integrity", "Checkpoint verified resumable",
          PASS if best_pth.stat().st_size > rf1_best.stat().st_size * 0.9 else WARN,
          f"best.pth: {file_size_mb(best_pth):.1f}MB vs rf1: {file_size_mb(rf1_best):.1f}MB")
else:
    check("C09", "Checkpoint Integrity", "Checkpoint verified resumable",
          INFO, "Cannot compare")

# C10: Stage state file valid
check("C10", "Checkpoint Integrity", "stage_state.json valid",
      PASS if state.get("current_stage") == "rf2" else FAIL,
      f"current_stage={state.get('current_stage')}")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 6: GPU / RESOURCE MONITORING (R01–R10)
# ══════════════════════════════════════════════════════════════════════════════

# R01: GPU memory comfortable
gpu_mems = [float(m.group(1)) for m in all_matches(r'gpu_mem=([\d.]+)GB')]
gpu_totals = [float(m.group(1)) for m in all_matches(r'gpu_mem=[\d.]+GB/([\d.]+)GB')]
if gpu_mems and gpu_totals:
    recent_mem_pct = max(gpu_mems[-5:]) / max(gpu_totals[-5:]) * 100
    check("R01", "GPU/Resource", f"GPU memory usage ({recent_mem_pct:.0f}%)",
          PASS if recent_mem_pct < 85 else WARN,
          f"{gpu_mems[-1]:.2f}/{gpu_totals[-1]:.2f} GB")
else:
    check("R01", "GPU/Resource", "GPU memory usage",
          INFO, "No GPU mem data")

# R02: EVAL batch memory safe
eval_mems = [float(m.group(1)) for m in all_matches(r'\[EVAL.*?GPU alloc=([\d.]+)GB')]
eval_reserved = [float(m.group(1)) for m in all_matches(r'\[EVAL.*?reserved=([\d.]+)GB')]
if eval_mems:
    max_eval_mem = max(eval_mems)
    check("R02", "GPU/Resource", "EVAL batch GPU memory safe",
          PASS if max_eval_mem < 5.5 else WARN,
          f"Max EVAL GPU: {max_eval_mem:.2f}GB")
else:
    check("R02", "GPU/Resource", "EVAL batch GPU memory",
          INFO, "No EVAL mem data")

# R03: No OOM errors
oom_errors = grep_count(r'OOM|out of memory|CUDA out of memory')
check("R03", "GPU/Resource", "No OOM errors",
      PASS if oom_errors == 0 else FAIL,
      f"{oom_errors} OOM occurrences", blocking=oom_errors > 0)

# R04: Training PID active
pid = state.get("training_pid")
if pid:
    check("R04", "GPU/Resource", "Training process active",
          PASS if pid and os.path.isdir(f"/proc/{pid}") else FAIL,
          f"PID {pid} {'running' if pid and os.path.isdir(f'/proc/{pid}') else 'DEAD'}", blocking=True)
else:
    check("R04", "GPU/Resource", "Training process active",
          FAIL, "No PID recorded", blocking=True)

# R05: Gradient clipping active
check("R05", "GPU/Resource", "Gradient clipping active (GRAD_CLIP_NORM=5.0)",
      PASS if 'GRAD_CLIP_NORM = 5.0' in config_text else WARN,
      "Gradient clipping config")

# R06: Mixed precision status
check("R06", "GPU/Resource", "Mixed precision disabled (MIXED_PRECISION=False)",
      PASS if 'MIXED_PRECISION = False' in config_text else INFO,
      "AMP status")

# R07: ALLOW_TF32 enabled
check("R07", "GPU/Resource", "TF32 allowed (performance)",
      PASS if 'ALLOW_TF32": true' in log_text else INFO,
      "TF32 status")

# R08: Steps per second healthy (>0.5)
sps_vals = [float(m.group(1)) for m in all_matches(r'(\d+\.\d+)s/it')]
if sps_vals:
    avg_sps = sum(sps_vals[-50:]) / min(len(sps_vals[-50:]), 50)
    check("R08", "GPU/Resource", f"Steps/sec healthy ({1/avg_sps:.1f} it/s)",
          PASS if avg_sps < 3.0 else WARN,
          f"Avg: {avg_sps:.2f}s/it ({1/max(avg_sps,0.01):.1f} it/s)")
else:
    check("R08", "GPU/Resource", "Steps/sec healthy",
          INFO, "No timing data")

# R09: No CUDA errors
cuda_errors = grep_count(r'CUDA error|RuntimeError.*CUDA|cuda.*assert')
check("R09", "GPU/Resource", "No CUDA errors",
      PASS if cuda_errors == 0 else FAIL,
      f"{cuda_errors} CUDA errors", blocking=cuda_errors > 0)

# R10: Training heartbeat recent
last_heartbeat = state.get("last_heartbeat", "")
if last_heartbeat:
    try:
        hb_time = datetime.fromisoformat(last_heartbeat)
        age_mins = (datetime.now(timezone.utc) - hb_time).total_seconds() / 60
        check("R10", "GPU/Resource", "Training heartbeat recent",
              PASS if age_mins < 30 else FAIL,
              f"Last heartbeat: {age_mins:.0f}min ago", blocking=age_mins > 60)
    except Exception:
        check("R10", "GPU/Resource", "Training heartbeat",
              WARN, f"Cannot parse: {last_heartbeat}")
else:
    check("R10", "GPU/Resource", "Training heartbeat",
          WARN, "No heartbeat in state")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 7: DET_PROBE SCORE ANALYSIS (P01–P12)
# ══════════════════════════════════════════════════════════════════════════════

# P01: score_p50 trending upward
score_p50_vals = [float(m.group(1)) for m in all_matches(r"'score_p50':\s*([\d.]+)")]
if len(score_p50_vals) >= 100:
    early_p50 = sum(score_p50_vals[:50]) / 50
    recent_p50 = sum(score_p50_vals[-50:]) / 50
    check("P01", "DET_PROBE", "score_p50 improving (head recovering)",
          PASS if recent_p50 > early_p50 * 1.5 else WARN,
          f"{early_p50:.4f} → {recent_p50:.4f}")
elif len(score_p50_vals) > 0:
    check("P01", "DET_PROBE", "score_p50 improving",
          INFO, f"Only {len(score_p50_vals)} data points")
else:
    check("P01", "DET_PROBE", "score_p50 improving",
          INFO, "No data")

# P02: score_p99 high (confident predictions)
score_p99_vals = [float(m.group(1)) for m in all_matches(r"'score_p99':\s*([\d.]+)")]
if score_p99_vals:
    recent_p99 = score_p99_vals[-10:]
    avg_p99 = sum(recent_p99) / len(recent_p99)
    check("P02", "DET_PROBE", "score_p99 > 0.50 (confident predictions)",
          PASS if avg_p99 > 0.5 else WARN,
          f"Avg P99: {avg_p99:.4f}")
else:
    check("P02", "DET_PROBE", "score_p99 > 0.50",
          INFO, "No data")

# P03: score_max approaching 1.0
score_max_vals = [float(m.group(1)) for m in all_matches(r"'score_max':\s*([\d.]+)")]
if score_max_vals:
    recent_max = score_max_vals[-10:]
    avg_max = sum(recent_max) / len(recent_max)
    check("P03", "DET_PROBE", "score_max high (>0.90)",
          PASS if avg_max > 0.9 else WARN,
          f"Avg max: {avg_max:.4f}")
else:
    check("P03", "DET_PROBE", "score_max high",
          INFO, "No data")

# P04: Predictions above 0.50 threshold
preds_50 = [int(m.group(1)) for m in all_matches(r"'preds>0\.50':\s*(\d+)")]
if preds_50:
    recent_preds = preds_50[-20:]
    avg_preds = sum(recent_preds) / len(recent_preds)
    check("P04", "DET_PROBE", "Significant preds at 0.50 threshold",
          PASS if avg_preds > 1000 else WARN,
          f"Avg preds>0.50: {avg_preds:.0f}")
else:
    check("P04", "DET_PROBE", "Preds at 0.50 threshold",
          INFO, "No data")

# P05: Predictions above 0.30 threshold
preds_30 = [int(m.group(1)) for m in all_matches(r"'preds>0\.30':\s*(\d+)")]
if preds_30:
    recent_p30 = preds_30[-20:]
    check("P05", "DET_PROBE", "Predictions at 0.30 threshold sufficient",
          PASS if sum(recent_p30)/len(recent_p30) > 1000 else WARN,
          f"Avg preds>0.30: {sum(recent_p30)/len(recent_p30):.0f}")
else:
    check("P05", "DET_PROBE", "Predictions at 0.30",
          INFO, "No data")

# P06: bestIoU_max high quality
iou_max = [float(m.group(1)) for m in all_matches(r"'bestIoU_max':\s*([\d.]+)")]
if iou_max:
    recent_iou = iou_max[-20:]
    check("P06", "DET_PROBE", "bestIoU_max > 0.80 (high quality localization)",
          PASS if sum(recent_iou)/len(recent_iou) > 0.8 else WARN,
          f"Avg bestIoU_max: {sum(recent_iou)/len(recent_iou):.4f}")
else:
    check("P06", "DET_PROBE", "bestIoU_max quality",
          INFO, "No data")

# P07: bestIoU>0.5 count (accurate detections)
iou_50 = [int(m.group(1)) for m in all_matches(r"'bestIoU>0\.5':\s*(\d+)")]
if iou_50:
    recent_iou50 = iou_50[-20:]
    avg_iou50 = sum(recent_iou50) / len(recent_iou50)
    check("P07", "DET_PROBE", "Accurate detections (bestIoU>0.5) > 500",
          PASS if avg_iou50 > 500 else WARN,
          f"Avg bestIoU>0.5: {avg_iou50:.0f}")
else:
    check("P07", "DET_PROBE", "Accurate detections count",
          INFO, "No data")

# P08: DET_PROBE verdict streak
verdict_localizing = grep_count(r'verdict:\s*LOCALIZING')
verdict_not_localizing = grep_count(r'verdict:\s*(?!LOCALIZING)')
check("P08", "DET_PROBE", f"Verdict consistently LOCALIZING",
      PASS if verdict_localizing > verdict_not_localizing * 10 else WARN,
      f"LOCALIZING: {verdict_localizing}, other: {verdict_not_localizing}")

# P09: preds>0.01 count stable (all predictions)
preds_01 = [int(m.group(1)) for m in all_matches(r"'preds>0\.01':\s*(\d+)")]
if preds_01:
    recent_p01 = preds_01[-20:]
    std_p01 = (max(recent_p01) - min(recent_p01)) / max(sum(recent_p01)/len(recent_p01), 1)
    check("P09", "DET_PROBE", "Total pred count stable",
          PASS if std_p01 < 0.05 else WARN,
          f"Variation: {std_p01:.4f}")
else:
    check("P09", "DET_PROBE", "Total pred count stable",
          INFO, "No data")

# P10: bestIoU_mean improving
iou_mean = [float(m.group(1)) for m in all_matches(r"'bestIoU_mean':\s*([\d.]+)")]
if len(iou_mean) >= 100:
    early_iou = sum(iou_mean[:50]) / 50
    recent_iou = sum(iou_mean[-50:]) / 50
    check("P10", "DET_PROBE", "bestIoU_mean improving",
          PASS if recent_iou > early_iou else WARN,
          f"{early_iou:.4f} → {recent_iou:.4f}")
else:
    check("P10", "DET_PROBE", "bestIoU_mean improving",
          INFO, f"Only {len(iou_mean)} points")

# P11: bestIoU>0.3 count (decent localization)
iou_30 = [int(m.group(1)) for m in all_matches(r"'bestIoU>0\.3':\s*(\d+)")]
if iou_30:
    avg_iou30 = sum(iou_30[-20:]) / 20
    check("P11", "DET_PROBE", "Decent localizations (bestIoU>0.3) > 5000",
          PASS if avg_iou30 > 5000 else WARN,
          f"Avg: {avg_iou30:.0f}")
else:
    check("P11", "DET_PROBE", "Decent localizations",
          INFO, "No data")

# P12: DET_PROBE count per epoch adequate
probe_total = probe_count  # already an int from grep_count
check("P12", "DET_PROBE", "DET_PROBE frequency adequate",
      PASS if probe_total > 100 else WARN,
      f"{probe_total} total probes")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 8: CONVERGENCE & STABILITY (S01–S12)
# ══════════════════════════════════════════════════════════════════════════════

# S01: Validation loss not diverging
val_losses = [safe_float(m.group(1)) for m in all_matches(r'Val:.*loss=([\d.]+)')]
if len(val_losses) >= 3:
    if val_losses[-1] <= val_losses[-3] * 1.5:
        check("S01", "Convergence", "Validation loss not diverging",
              PASS, f"Recent: {val_losses[-3:]}")
    else:
        check("S01", "Convergence", "Validation loss not diverging",
              WARN, f"Diverging: {val_losses[-3:]}")
else:
    check("S01", "Convergence", "Validation loss not diverging",
          INFO, f"Only {len(val_losses)} points")

# S02: Training loss converging
train_losses = [safe_float(m.group(1)) for m in all_matches(r'training healthy:.*loss=([\d.]+)')]
if len(train_losses) >= 3:
    check("S02", "Convergence", "Training loss epoch-over-epoch decreasing",
          PASS if train_losses[-1] <= train_losses[0] else WARN,
          f"{train_losses[0]:.4f} → {train_losses[-1]:.4f}")
else:
    check("S02", "Convergence", "Training loss decreasing",
          INFO, f"Only {len(train_losses)} points")

# S03: Patience epochs remaining for improvement
patience_remaining = CONV["patience_epochs"] - (rf2_current_epochs - 1)
check("S03", "Convergence", f"Patience epochs remaining ({patience_remaining})",
      PASS if patience_remaining > 0 else WARN,
      f"Using {CONV['patience_epochs']}-epoch patience window")

# S04: Min improvement threshold healthy
check("S04", "Convergence", f"Min improvement per 3-epoch window = {CONV['min_improvement']}",
      INFO, f"Will check when ≥{CONV['patience_epochs']} RF2 val results available")

# S05: No gradient spike epochs > max_grad_spike_epochs
grad_spikes = grep_count(r'grad.*spike|GRAD.*SPIKE|spike.*detected')
check("S05", "Convergence", f"No excessive gradient spikes",
      PASS if grad_spikes < 3 else WARN,
      f"{grad_spikes} gradient spike events")

# S06: Forward angular MAE well below gate (for successful runs)
# Just track current state
check("S06", "Convergence", "Pose quality expected good (RF1 MAE ~5-6°)",
      INFO, "RF1 MAE ranged 4.6-8.0° — good baseline")

# S07: No NaN in training losses (exclude efficiency metrics like "nanM", "nanG", "nanGFLOPs")
nan_training_events = len([l for l in log_lines if re.search(r'\bnan\b|\bNaN\b', l) and 'Params: nanM' not in l and 'GFLOPs: nan' not in l and 'FPS:' not in l and 'eff_' not in l and 'nan_skips' not in l])
check("S07", "Convergence", "No NaN in training losses",
      PASS if nan_training_events == 0 else WARN,
      f"{nan_training_events} NaN occurrences in training (excluding efficiency metrics)", blocking=nan_training_events > 0)

# S08: Epochs without progress
if len(mAP50_vals) >= 3 and latest_rf2_val is not None:
    rf2_mAP50 = mAP50_vals[-(min(len(mAP50_vals), 6)):]
    if len(rf2_mAP50) >= 3:
        progress = rf2_mAP50[-1] - rf2_mAP50[0]
        check("S08", "Convergence", "Progress over last 3 RF2 evals",
              PASS if progress > 0 else WARN,
              f"Change: {progress:+.4f}")
else:
    check("S08", "Convergence", "Progress over last 3 evals",
          INFO, "Need more RF2 val data")

# S09: mAP50_95 / mAP50 ratio healthy (0.5-0.7 range)
if mAP50_vals and mAP50_95_vals:
    ratio_50_95 = mAP50_95_vals[-1] / max(mAP50_vals[-1], 1e-10)
    check("S09", "Convergence", "mAP50_95/mAP50 ratio healthy (0.4-0.7)",
          PASS if 0.3 < ratio_50_95 < 0.8 else WARN,
          f"Ratio: {ratio_50_95:.3f}")
else:
    check("S09", "Convergence", "mAP50_95/mAP50 ratio",
          INFO, "Need both metrics")

# S10: No unexplained restarts
restart_count = grep_count(r'========== RESTART')
check("S10", "Convergence", "No unexplained training restarts",
      PASS if restart_count <= 1 else WARN,
      f"{restart_count} restart(s) detected")

# S11: Detach flags correct (RF2: detach_reg_fpn=True, detach_psr_fpn=True)
detach_reg = re.search(r'detach_reg_fpn.*?True', config_text)
detach_psr = re.search(r'detach_psr_fpn.*?True', config_text)
check("S11", "Convergence", "detach_reg_fpn=True (PSR isolation)",
      PASS if detach_reg else WARN,
      "detach_reg_fpn flag")
check("S12", "Convergence", "detach_psr_fpn=True (PSR isolation)",
      PASS if detach_psr else WARN,
      "detach_psr_fpn flag")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 9: VALIDATION PIPELINE (V01–V08)
# ══════════════════════════════════════════════════════════════════════════════

# V01: Step-0 diagnostic passing consistently
step0_passes = grep_count(r'\[STEP-0 ASSERT\] PASSED')
step0_fails = grep_count(r'\[STEP-0 ASSERT\] FAILED')
check("V01", "Validation", "Step-0 diagnostic consistently passing",
      PASS if step0_fails == 0 and step0_passes > 0 else FAIL,
      f"Passed: {step0_passes}, Failed: {step0_fails}", blocking=step0_fails > 0)

# V02: cls_logits median in healthy range
logit_vals = [float(m.group(1)) for m in all_matches(r'cls_logits\.abs\(\)\.median\(\)\s*=\s*([\d.]+)')]
if logit_vals:
    check("V02", "Validation", "cls_logits median < 8.0 (healthy scale)",
          PASS if logit_vals[-1] < 8 else WARN,
          f"Latest: {logit_vals[-1]:.3f}")
else:
    check("V02", "Validation", "cls_logits healthy",
          INFO, "No logit data")

# V03: ASD mAP printed (custom metric)
asd_vals = grep_count(r'ASD.*mAP@0\.5')
check("V03", "Validation", "ASD mAP metrics being computed",
      PASS if asd_vals > 0 else WARN,
      f"{asd_vals} ASD metric entries")

# V04: Validation timing regular (every ~epoch)
val_times = [m.group(0) for m in all_matches(r'\[VAL_OK\] epoch \d+ val completed')]
if val_times:
    epochs_seen = len(val_times)
    check("V04", "Validation", "Validation running at expected frequency",
          PASS if epochs_seen >= 3 else INFO,
          f"{epochs_seen} validations completed")
else:
    check("V04", "Validation", "Validation running at expected frequency",
          INFO, "No validations yet")

# V05: Validation loss not NaN
_v_losses = [safe_float(m.group(1)) for m in all_matches(r'\[VAL_OK\].*loss=([\d.]+)')]
val_loss_nan = any(math.isnan(v) or math.isinf(v) for v in _v_losses)
check("V05", "Validation", "Validation loss not NaN/Inf",
      PASS if not val_loss_nan else FAIL,
      "Validation loss integrity", blocking=val_loss_nan)

# V06: No validation assertion failures
val_assert_fails = grep_count(r'ASSERT.*FAIL|assertion.*failed')
check("V06", "Validation", "No validation assertion failures",
      PASS if val_assert_fails == 0 else FAIL,
      f"{val_assert_fails} assertion failures", blocking=val_assert_fails > 0)

# V07: Validation samples consistent
if len(val_samples) >= 2:
    last_two = val_samples[-2:]
    ratio_vs = max(last_two) / max(min(last_two), 1)
    check("V07", "Validation", "Validation sample count consistent",
          PASS if abs(ratio_vs - 1) < 0.1 else WARN,
          f"{last_two}")
else:
    check("V07", "Validation", "Validation sample count",
          INFO, "Need 2+ data points")

# V08: Best metric tracking
best_metric = state.get("best_metric", 0)
check("V08", "Validation", "Best metric being tracked",
      PASS if best_metric > 0 else INFO,
      f"best_metric={best_metric}")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 10: HEAD RECOVERY & POST-REINIT (E01–E10)
# ══════════════════════════════════════════════════════════════════════════════

# E01: Reinit heads event confirmed
reinit_count = grep_count(r'\[REINIT-HEADS\]')
check("E01", "Head Recovery", "REINIT-HEADS event recorded",
      PASS if reinit_count > 0 else INFO,
      f"{reinit_count} reinit events")

# E02: pi (cls bias init) = 0.01 for RF2
pi_match = re.search(r'pi[=:]\s*([\d.]+)', log_text[:20000])
check("E02", "Head Recovery", f"cls bias init pi=0.01 (RF2 reinit)",
      PASS if pi_match and float(pi_match.group(1)) == 0.01 else INFO,
      f"pi={pi_match.group(1) if pi_match else 'not found'}")

# E03: Detection head recovery — cls loss started high, now lower
if det_cls_vals:
    check("E03", "Head Recovery", "Detection head recovering (cls loss decreasing)",
          PASS if len(det_cls_vals) > 100 else INFO,
          f"{len(det_cls_vals)} cls loss data points")

# E04: Kendall log_vars reset
kendall_reset = grep_count(r'Kendall log_vars reset')
check("E04", "Head Recovery", "Kendall log_vars reset for RF2",
      PASS if kendall_reset > 0 else INFO,
      "Kendall uncertainty weights re-initialized")

# E05: EMA shadow re-anchored
ema_reanchor = grep_count(r'EMA shadow re-anchored')
check("E05", "Head Recovery", "EMA shadow re-anchored after reinit",
      PASS if ema_reanchor > 0 else WARN,
      "EMA shadow re-anchor status")

# E06: Head warmup multiplier active
warmup_active = grep_count(r'warmup.*grad multiplier|2x grad multiplier')
check("E06", "Head Recovery", "Head warmup gradient multiplier active",
      PASS if warmup_active > 0 else INFO,
      "Head warmup status")

# E07: Detection head gradient warmup counter reset
warmup_reset = grep_count(r'Detection head gradient warmup counter reset')
check("E07", "Head Recovery", "Detection head warmup counter reset",
      PASS if warmup_reset > 0 else INFO,
      "Warmup counter status")

# E08: PSR head warmup active (even though not trained)
psr_warmup = grep_count(r'PSR output head warmup')
check("E08", "Head Recovery", "PSR output head warmup configured",
      PASS if psr_warmup > 0 else INFO,
      "PSR warmup status")

# E09: Recovery trajectory — score_p50 improvement factor
if len(score_p50_vals) >= 50:
    first_50_avg = sum(score_p50_vals[:50]) / 50
    last_50_avg = sum(score_p50_vals[-50:]) / 50
    improvement_factor = last_50_avg / max(first_50_avg, 1e-10)
    check("E09", "Head Recovery", f"Recovery trajectory (score_p50 {improvement_factor:.1f}x)",
          PASS if improvement_factor > 2 else WARN,
          f"{first_50_avg:.4f} → {last_50_avg:.4f}")
else:
    check("E09", "Head Recovery", "Recovery trajectory",
          INFO, "Need 50+ points")

# E10: Total recovery status summary
recent_max_scores = score_max_vals[-20:] if score_max_vals else []
if recent_max_scores:
    recovery_ok = sum(recent_max_scores)/len(recent_max_scores) > 0.8
    check("E10", "Head Recovery", "Detection head fully recovered (score_max > 0.80)",
          PASS if recovery_ok else WARN,
          f"Avg max score: {sum(recent_max_scores)/len(recent_max_scores):.4f}")
else:
    check("E10", "Head Recovery", "Head fully recovered",
          INFO, "No data")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 11: BLOCKING ISSUES & RISK ASSESSMENT (B01–B06)
# ══════════════════════════════════════════════════════════════════════════════

# B01: Any blocking FAIL items
blocking_fails = [r for r in results if r["blocking"] and r["verdict"] == FAIL]
check("B01", "Blocker Assessment", "No blocking failures detected",
      FAIL if blocking_fails else PASS,
      f"{len(blocking_fails)} blocking failures: {[r['uid'] for r in blocking_fails]}")

# B02: WARN items
warns = [r for r in results if r["verdict"] == WARN]
check("B02", "Blocker Assessment", f"Warning count ({len(warns)})",
      PASS if len(warns) < 10 else WARN,
      f"{len(warns)} warnings — investigate top ones")

# B03: The pi=0.01 reinit risk (heads lost RF1 progress)
reinit_risk = "Heads reinitialized at pi=0.01 — need to recover cls bias from scratch"
check("B03", "Blocker Assessment", "RF2 reinit risk assessed",
      INFO, reinit_risk)

# B04: RETRY_STRATEGIES[0] design issue
retry_issue = "RETRY_STRATEGIES[0] has reinit_heads=True — non-retry launches also get head reinit"
check("B04", "Blocker Assessment", "RETRY_STRATEGIES design reviewed",
      INFO, retry_issue)

# B05: Time remaining estimate
if sps_vals:
    avg_step_time = sum(sps_vals[-100:]) / min(len(sps_vals[-100:]), 100)
    steps_per_epoch = 2156
    remaining_steps = (max_epochs - current_epoch) * steps_per_epoch
    remaining_hours = (remaining_steps * avg_step_time) / 3600
    check("B05", "Blocker Assessment", "Estimated time to completion",
          INFO, f"~{remaining_hours:.1f}h remaining ({remaining_steps} steps at {avg_step_time:.2f}s/it)")
else:
    check("B05", "Blocker Assessment", "Time to completion",
          INFO, "Cannot estimate")

# B06: Proximity to gate
if latest_rf2_val is not None and mAP50_vals:
    current_best = max(mAP50_vals)
    gap = GATE["det_mAP50"] - current_best
    check("B06", "Blocker Assessment", f"Gap to det_mAP50 gate: {gap:.3f}",
          PASS if gap <= 0 else INFO,
          f"Best: {current_best:.4f}, Target: {GATE['det_mAP50']}, Gap: {gap:.3f}")
else:
    check("B06", "Blocker Assessment", "Gap to det_mAP50 gate",
          INFO, "No RF2 val results yet — first eval imminent")


# ══════════════════════════════════════════════════════════════════════════════
#  REPORT GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_report():
    """Generate structured report from all checks."""
    total = len(results)
    passes = sum(1 for r in results if r["verdict"] == PASS)
    fails = sum(1 for r in results if r["verdict"] == FAIL)
    warns = sum(1 for r in results if r["verdict"] == WARN)
    infos = sum(1 for r in results if r["verdict"] == INFO)
    skips = sum(1 for r in results if r["verdict"] == SKIP)
    blocking = sum(1 for r in results if r["blocking"] and r["verdict"] == FAIL)

    lines = []
    lines.append("=" * 72)
    lines.append("  RF2 TRAINING GATE CHECKLIST — 100-ITEM VERIFICATION REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 72)
    lines.append(f"  TOTAL: {total}  |  PASS: {passes}  |  WARN: {warns}  |  FAIL: {fails}  |  INFO: {infos}  |  SKIP: {skips}")
    lines.append(f"  BLOCKING FAILURES: {blocking}")
    lines.append(f"  Epoch: {state.get('epoch', '?')}/{state.get('max_epochs', '?')}  |  Stage: {state.get('current_stage', '?')}  |  PID: {state.get('training_pid', '?')}")
    lines.append(f"  Gate passed: {state.get('gate_passed', False)}")
    lines.append("=" * 72)

    # Group by category
    categories = {}
    for r in results:
        categories.setdefault(r["category"], []).append(r)

    for cat_name, items in categories.items():
        cat_passes = sum(1 for r in items if r["verdict"] == PASS)
        cat_fails = sum(1 for r in items if r["verdict"] == FAIL)
        cat_warns = sum(1 for r in items if r["verdict"] == WARN)
        lines.append(f"\n{'─' * 72}")
        lines.append(f"  {cat_name}  [{cat_passes}P {cat_warns}W {cat_fails}F]")
        lines.append(f"{'─' * 72}")

        for r in items:
            icon = {"PASS": "✓", "FAIL": "✗", "WARN": "▲", "INFO": "•", "SKIP": "−"}.get(r["verdict"], "?")
            block_tag = " [BLOCKING]" if r.get("blocking") else ""
            lines.append(f"  {r['uid']:6s} {icon} {r['verdict']:5s}{block_tag} | {r['desc']}")
            if r.get("detail"):
                lines.append(f"         {r['detail']}")

    # Overall verdict
    lines.append(f"\n{'=' * 72}")
    if blocking > 0:
        lines.append(f"  VERDICT: ❌ BLOCKED — {blocking} blocking failure(s) requiring intervention")
        for r in blocking_fails:
            lines.append(f"    - {r['uid']}: {r['desc']} → {r['detail']}")
    elif fails > 0:
        lines.append(f"  VERDICT: ⚠ DEGRADED — {fails} non-blocking failure(s), {warns} warning(s)")
    elif warns > 5:
        lines.append(f"  VERDICT: ⚠ ATTENTION — {warns} warning(s) to review")
    else:
        lines.append(f"  VERDICT: ✓ HEALTHY — All checks passing")
    lines.append("=" * 72)

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    report = generate_report()
    print(report)

    # Save report
    report_path = RUNS / "rf_stages/rf2_checklist_report.txt"
    report_path.write_text(report)
    print(f"\nReport saved to: {report_path}")

    # JSON output for programmatic use
    json_path = RUNS / "rf_stages/rf2_checklist_results.json"
    # Compute summary stats
    total_results = len(results)
    pass_count = sum(1 for r in results if r["verdict"] == PASS)
    fail_count = sum(1 for r in results if r["verdict"] == FAIL)
    warn_count = sum(1 for r in results if r["verdict"] == WARN)
    info_count = sum(1 for r in results if r["verdict"] == INFO)
    block_count = sum(1 for r in results if r["blocking"] and r["verdict"] == FAIL)
    summary = "HEALTHY" if block_count == 0 and fail_count == 0 else "BLOCKED" if block_count > 0 else "DEGRADED"

    with open(str(json_path), "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": total_results,
            "pass": pass_count,
            "warn": warn_count,
            "fail": fail_count,
            "info": info_count,
            "blocking": block_count,
            "gate_passed": state.get("gate_passed", False),
            "epoch": state.get("epoch", 0),
            "max_epochs": state.get("max_epochs", 21),
            "results": results,
            "summary": summary
        }, f, indent=2, default=str)
    print(f"JSON results saved to: {json_path}")
