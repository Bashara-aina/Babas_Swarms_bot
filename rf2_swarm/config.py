"""Central configuration — all paths, thresholds, and intervals."""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
RUNS = Path("/media/newadmin/master/POPW/working/code/industreal_improved/src/runs")
LOG = RUNS / "rf_stages/logs/train.log"
STATE = RUNS / "rf_stage_state.json"
METRICS = RUNS / "rf_stages/logs/metrics.jsonl"
CKPT_DIR = RUNS / "rf_stages/checkpoints"
CONFIG_FILE = CKPT_DIR / "config.py"

# Outputs (backward-compatible with monolithic checklist)
RESULTS_JSON = RUNS / "rf_stages/rf2_checklist_results.json"
REPORT_TXT = RUNS / "rf_stages/rf2_checklist_report.txt"
SWARM_LOG = RUNS / "rf_stages/swarm_loop.log"

# ── Gate Targets ───────────────────────────────────────────────────────────
GATE = {
    "det_mAP50": 0.40,
    "det_mAP50_95": None,  # not logged by val code — tracked as manual flag only
    "forward_angular_MAE_deg": 60.0,
}
VAL_FLOORS = {
    "det_mAP50": 0.35,
    "forward_angular_MAE_deg": 70.0,
}

# ── Health Thresholds ──────────────────────────────────────────────────────
HEALTH = {
    "min_grad_norm_det": 1e-6,
    "min_grad_norm_pose": 1e-6,
    "max_consecutive_dead": 5,
    "max_loss_spike_factor": 10.0,
}

# ── Convergence ────────────────────────────────────────────────────────────
CONV = {
    "patience_epochs": 6,
    "min_improvement": 0.003,
}

# ── Monitoring Loop ────────────────────────────────────────────────────────
DEFAULT_INTERVAL = 300  # seconds between cycles
AGENT_TIMEOUT = 60       # max seconds per agent
MAX_WORKERS = 40         # ThreadPoolExecutor workers

# ── Heartbeat ──────────────────────────────────────────────────────────────
HEARTBEAT_WARN_SEC = 180   # 3 min → WARN
HEARTBEAT_FAIL_SEC = 300   # 5 min → FAIL

# ── LR Scheduler ──────────────────────────────────────────────────────────
LR_RESTART = {
    "t_0": 10,              # CosineAnnealingWarmRestarts T_0
    "grace_epochs": 3,       # suppress gate failures for N epochs after restart
}

# ── Log scanning ───────────────────────────────────────────────────────────
LOG_TAIL_SIZE = 20_000    # lines to tail from subprocess.log (reduced from 200K for perf; log anomalies are in event-based agents)
