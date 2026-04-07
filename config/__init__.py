"""Configuration package for LegionSwarm."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_character_config() -> dict[str, Any]:
	"""Load the Legion character card JSON."""
	path = Path(__file__).resolve().parent / "legion_character.json"
	return json.loads(path.read_text(encoding="utf-8"))


__all__ = ["load_character_config"]
