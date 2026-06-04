"""core/memory/bridges — fire-and-forget fan-out from observation_store.

Bridges are registered at import time and invoked from observation_store._fanout().
Each bridge owns its own idempotency state via BridgeState.
"""
from __future__ import annotations

from ._base import ObservationBridge, BridgeState, init_state
from .six_layer import SixLayerBridge
from .hermes import HermesBridge
from .gitnexus import GitNexusBridge

_BUILTIN: list[ObservationBridge] = [
    SixLayerBridge(),
    HermesBridge(),
    GitNexusBridge(),
]


def get_bridges() -> list[ObservationBridge]:
    return list(_BUILTIN)


__all__ = [
    "ObservationBridge",
    "BridgeState",
    "init_state",
    "SixLayerBridge",
    "HermesBridge",
    "GitNexusBridge",
    "get_bridges",
]
