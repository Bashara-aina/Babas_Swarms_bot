"""Swarm command argument parsing — used by handlers/ai.py for /swarm command."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SwarmCommandArgs:
    use_sdk: bool
    topology: str
    task: str


def parse_swarm_args(raw: str) -> SwarmCommandArgs:
    """Parse raw /swarm command arguments.

    Supports:
      --sdk           Enable OpenAI Agents SDK path
      --topology X    Override topology (auto, spreadsheet, mixture, graph, sequential, concurrent, debate)
      <task>          The actual task description

    Examples:
      /swarm --sdk design a REST API
      /swarm --topology sequential analyze this code
      /swarm write unit tests for auth module
    """
    use_sdk = "--sdk" in raw
    topology = "auto"
    tokens = [t for t in raw.split() if t]
    clean_tokens: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--sdk":
            i += 1
            continue
        if tok == "--topology" and i + 1 < len(tokens):
            topology = tokens[i + 1].strip().lower()
            i += 2
            continue
        if tok.startswith("--topology="):
            topology = tok.split("=", 1)[1].strip().lower()
            i += 1
            continue
        clean_tokens.append(tok)
        i += 1
    return SwarmCommandArgs(use_sdk=use_sdk, topology=topology, task=" ".join(clean_tokens).strip())
