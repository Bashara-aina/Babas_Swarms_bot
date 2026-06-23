#!/usr/bin/env python3
"""
RF2 Training Monitoring Loop — continuously runs the 100-item checklist.
Tracks changes between runs and alerts on new failures.
"""
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

RUNS = Path("/media/newadmin/master/POPW/working/code/industreal_improved/src/runs")
CHECKLIST_SCRIPT = Path("/home/newadmin/swarm-bot/rf2_checklist.py")
RESULTS_FILE = RUNS / "rf_stages/rf2_checklist_results.json"
REPORT_FILE = RUNS / "rf_stages/rf2_checklist_report.txt"
LOG_FILE = RUNS / "rf_stages/monitor_loop.log"

INTERVAL = 300  # 5 minutes between checks

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run_checklist() -> dict | None:
    """Run the checklist and return parsed results."""
    log("Running RF2 checklist...")
    result = subprocess.run(
        ["python3", str(CHECKLIST_SCRIPT)],
        capture_output=True, text=True, timeout=300
    )
    # Save full output
    with open(REPORT_FILE, "w") as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n--- STDERR ---\n")
            f.write(result.stderr)

    if result.returncode != 0:
        log(f"Checklist failed: {result.stderr[:500]}")
        return None

    if RESULTS_FILE.exists():
        try:
            return json.loads(RESULTS_FILE.read_text())
        except Exception as e:
            log(f"Parse error: {e}")
            return None
    return None

def check_alerting(old: dict | None, new: dict):
    """Compare with previous run and alert on new/delta failures."""
    if old is None:
        return

    old_map = {r["uid"]: r for r in old.get("results", [])}
    new_map = {r["uid"]: r for r in new.get("results", [])}

    for uid, nr in new_map.items():
        if nr["verdict"] == "FAIL" and nr.get("blocking"):
            or_ = old_map.get(uid)
            if or_ and or_["verdict"] != "FAIL":
                log(f"⚠ NEW BLOCKING: {uid}: {nr['desc']} — {nr.get('detail','')}")

    old_blocking = sum(1 for r in old.get("results", []) if r["verdict"] == "FAIL" and r.get("blocking"))
    new_blocking = sum(1 for r in new.get("results", []) if r["verdict"] == "FAIL" and r.get("blocking"))
    if new_blocking > old_blocking:
        log(f"⚠ BLOCKING COUNT INCREASED: {old_blocking} → {new_blocking}")

def main():
    log("=" * 60)
    log("RF2 MONITOR LOOP STARTED")
    log(f"Interval: {INTERVAL}s")
    log("=" * 60)

    previous_results = None
    cycle = 0

    while True:
        cycle += 1
        start = time.time()

        results = run_checklist()
        if results:
            p, w, f, b = results["pass"], results["warn"], results["fail"], results["blocking"]
            log(f"Cycle {cycle}: {results['total']} checks — {p}P {w}W {f}F {b}B | Verdict: {results['summary']}")
            check_alerting(previous_results, results)
            previous_results = results
        else:
            log(f"Cycle {cycle}: CHECKLIST FAILED TO RUN")

        elapsed = time.time() - start
        sleep = max(INTERVAL - elapsed, 60)
        log(f"Sleeping {sleep:.0f}s...")
        time.sleep(sleep)

if __name__ == "__main__":
    main()
