"""Score intent_router predictions against ground truth."""

from typing import Any


def score(predictions: list[str], ground_truth: list[dict]) -> dict[str, Any]:
    """Compute precision, recall, F1 for intent classification."""
    if not predictions or not ground_truth:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "accuracy": 0.0}

    tp = sum(
        1 for pred, gt in zip(predictions, ground_truth, strict=False) if pred.strip().lower() == gt["intent"].lower()
    )
    total = len(predictions)
    correct = tp

    precision = correct / total if total > 0 else 0.0
    recall = correct / len(ground_truth) if ground_truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = correct / total if total > 0 else 0.0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "accuracy": round(accuracy, 3),
    }
