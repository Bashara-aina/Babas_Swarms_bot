#!/usr/bin/env python3
"""Claude Code swarm CLI — Multi-agent orchestration via subprocess."""

import argparse
import sys
from pathlib import Path

# Add skills path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills"))

import itertools

from swarm import (
    CAPABILITY_TOKENS,
    estimate_complexity,
    get_capability_description,
    select_capabilities,
)


def main():
    parser = argparse.ArgumentParser(description="Claude Code Swarm — Multi-Agent Orchestration")
    parser.add_argument("task", nargs="+", help="Task description")
    parser.add_argument("--max-agents", "-k", type=int, default=4, help="Max agents to select (default: 4)")
    parser.add_argument("--explain", "-e", action="store_true", help="Explain capability selection")
    args = parser.parse_args()

    task = " ".join(args.task)

    print(f"\n## Swarm Analysis: {task[:80]}{'...' if len(task) > 80 else ''}")
    print(f"**Complexity**: {estimate_complexity(task)} sub-agents\n")

    capabilities = select_capabilities(task)

    if not capabilities:
        print("No matching capabilities found. Try with more specific keywords.")
        return 1

    print(f"**Selected Capabilities** (top {min(args.max_agents, len(capabilities))}):")
    for cap, score in capabilities[:args.max_agents]:
        print(f"  • {cap}: {score:.1f} — {get_capability_description(cap)}")

    if args.explain:
        print("\n**Full Capability Scores:**")
        task_tokens = set()
        import re
        text = task.lower()
        task_tokens |= set(re.findall(r"[a-z][a-z0-9]{1,}", text))
        words = text.split()
        task_tokens |= {f"{a}_{b}" for a, b in itertools.pairwise(words)}

        for cap_name, cap_keywords in CAPABILITY_TOKENS.items():
            cap_tokens = set(re.findall(r"[a-z][a-z0-9]{1,}", " ".join(cap_keywords).lower()))
            overlap = task_tokens & cap_tokens
            if overlap:
                print(f"  {cap_name}: matched tokens = {overlap}")

    print(f"\n**Sub-agents to spawn**: ~{estimate_complexity(task)}")
    print("\nTo execute with Agent tool, use the swarm skill in Claude Code:")
    print(f"  /swarm {task}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
