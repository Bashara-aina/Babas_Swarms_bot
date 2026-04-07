from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SwarmCommandArgs:
    use_sdk: bool
    topology: str
    task: str


def parse_swarm_args(raw: str) -> SwarmCommandArgs:
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
