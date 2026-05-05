#!/usr/bin/env bash
# Runs the Meta-Harness proposer to improve the harness after /goal runs
# Usage: ./scripts/evolve_harness.sh [--dry-run]
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Meta-Harness Proposer"
echo "Reading all execution traces in .goal/traces/..."
echo "This uses Claude Opus -- costs ~\$0.10-0.50 per run."
python3 tools/goal_harness_proposer.py "$@"
