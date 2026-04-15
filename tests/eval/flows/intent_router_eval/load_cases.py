"""Load test cases from JSONL for intent_router_eval flow."""

import json
from pathlib import Path


def load_cases(test_cases_path: str) -> list[dict]:
    """Read test cases from JSONL file. Each line: {"text": "...", "intent": "..."}"""
    path = Path(test_cases_path)
    if not path.exists():
        return []
    cases = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases
