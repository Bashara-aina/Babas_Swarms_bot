#!/usr/bin/env python3
"""CLI entry point for the RF2 monitoring swarm.

Usage:
    python -m rf2_swarm                    # continuous loop (5 min interval)
    python -m rf2_swarm --oneshot          # single cycle, print report, exit
    python -m rf2_swarm --interval 60      # 1-minute interval loop
    python -m rf2_swarm --list-agents      # list registered agents
"""

from __future__ import annotations
import argparse
import sys

from .base_agent import BaseAgent
from .runner import Runner
from .config import DEFAULT_INTERVAL
from .agents.gate_tracker import GateTrackerAgent
from .agents.probe_analyzer import ProbeAnalyzerAgent
from .agents.head_health import HeadHealthAgent
from .agents.loss_health import LossHealthAgent
from .agents.convergence import ConvergenceAgent
from .agents.data_pipeline import DataPipelineAgent
from .agents.checkpoint import CheckpointAgent
from .agents.gpu_resource import GPUResourceAgent
from .agents.validation import ValidationAgent
from .agents.head_recovery import HeadRecoveryAgent
from .agents.metrics_logger import MetricsLoggerAgent
from .agents.gate_predictor import GatePredictorAgent
from .agents.process_health import ProcessHealthAgent
from .agents.epoch_tracker import EpochTrackerAgent
from .agents.nan_detector import NanDetectorAgent
from .agents.cuda_health import CudaHealthAgent
from .agents.config_validator import ConfigValidatorAgent
from .agents.log_anomaly import LogAnomalyAgent
from .agents.blocker_assessment import BlockerAssessmentAgent
from .agents.summary import SummaryAgent
from .agents.cls_stagnation import ClsStagnationAgent
from .agents.bias_update import BiasUpdateAgent


def build_agents() -> list[BaseAgent]:
    """Instantiate all 22 monitoring agents."""
    return [
        GateTrackerAgent(),
        ProbeAnalyzerAgent(),
        HeadHealthAgent(),
        LossHealthAgent(),
        ConvergenceAgent(),
        DataPipelineAgent(),
        CheckpointAgent(),
        GPUResourceAgent(),
        ValidationAgent(),
        HeadRecoveryAgent(),
        MetricsLoggerAgent(),
        GatePredictorAgent(),
        ProcessHealthAgent(),
        EpochTrackerAgent(),
        NanDetectorAgent(),
        CudaHealthAgent(),
        ConfigValidatorAgent(),
        LogAnomalyAgent(),
        BlockerAssessmentAgent(),
        SummaryAgent(),
        ClsStagnationAgent(),
        BiasUpdateAgent(),
    ]


def list_agents():
    """Print all registered agents and their module paths."""
    agents = build_agents()
    print(f"{'Name':25s} {'Class':30s}")
    print("-" * 55)
    for a in agents:
        print(f"{a.name:25s} {a.__class__.__name__:30s}")
    print(f"\nTotal: {len(agents)} agents")


def main():
    parser = argparse.ArgumentParser(
        description="RF2 Training — 22-Agent Monitoring Swarm"
    )
    parser.add_argument("--oneshot", action="store_true",
                        help="Run a single monitoring cycle then exit")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help=f"Monitoring interval in seconds (default: {DEFAULT_INTERVAL})")
    parser.add_argument("--list-agents", action="store_true",
                        help="List all registered agents and exit")
    parser.add_argument("--log-tail", type=int, default=200_000,
                        help="Number of log lines to tail (default: 200000)")

    args = parser.parse_args()

    if args.list_agents:
        list_agents()
        sys.exit(0)

    agents = build_agents()
    runner = Runner(agents, interval=args.interval, log_tail=args.log_tail)

    if args.oneshot:
        runner.run_once()
        # Print the report to stdout
        from .config import REPORT_TXT
        if REPORT_TXT.exists():
            print(REPORT_TXT.read_text())
    else:
        runner.run_forever()


if __name__ == "__main__":
    main()
