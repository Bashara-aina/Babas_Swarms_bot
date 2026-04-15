"""
Supervision CV annotation tool for screen annotations.
Used for bounding box overlays on screenshots when Legion needs to
highlight UI elements for Bashara.

This is a P4/niche tool — only used when annotated screenshots become frequent.
Requires: supervision, torch, supervision (roboflow)
"""

from __future__ import annotations

# Supervision is optional
_supervision_installed: bool | None = None


def _check_supervision() -> bool:
    global _supervision_installed
    if _supervision_installed is None:
        try:
            import supervision as sv  # noqa: F401

            _supervision_installed = True
        except ImportError:
            _supervision_installed = False
    return _supervision_installed


async def annotate_screenshot(
    image_path: str,
    detections: list[dict],
    labels: list[str] | None = None,
    output_path: str | None = None,
) -> str:
    """
    Annotate a screenshot with bounding boxes and labels.
    detections: list of {x_min, y_min, x_max, y_max, confidence, class}
    labels: optional display labels per detection
    Returns path to annotated image.
    """
    if not _check_supervision():
        return image_path  # return original if supervision not installed

    import cv2
    import supervision as sv
    import numpy as np

    image = cv2.imread(image_path)
    if image is None:
        return image_path

    # Build supervision Detections object
    if detections:
        boxes = np.array(
            [[d["x_min"], d["y_min"], d["x_max"], d["y_max"]] for d in detections],
            dtype=np.float32,
        )
        confidences = np.array([d.get("confidence", 1.0) for d in detections], dtype=np.float32)
        class_ids = np.array([d.get("class", 0) for d in detections], dtype=np.int64)

        det = sv.Detections(
            xyxy=boxes,
            confidence=confidences,
            class_id=class_ids,
        )

        # LabelAnnotator or BoxAnnotator
        annotator = sv.BoxAnnotator()
        annotated = annotator.annotate(scene=image, detections=det)

        if labels:
            label_annotator = sv.LabelAnnotator()
            annotated = label_annotator.annotate(
                scene=annotated, detections=det, labels=labels
            )
    else:
        annotated = image

    out = output_path or image_path.replace(".png", "_annotated.png")
    cv2.imwrite(out, annotated)
    return out


async def detect_objects_in_screenshot(
    image_path: str, model: str = "yolov8n.pt"
) -> list[dict]:
    """
    Run object detection on a screenshot.
    Returns list of {x_min, y_min, x_max, y_max, confidence, class}.
    """
    if not _check_supervision():
        return []

    import torch
    import supervision as sv

    model_obj = torch.hub.load("ultralytics/yolov8", model.replace(".pt", ""))
    result = model_obj(image_path)
    detections = result.pandas().xyxy[0]

    return [
        {
            "x_min": float(row["xmin"]),
            "y_min": float(row["ymin"]),
            "x_max": float(row["xmax"]),
            "y_max": float(row["ymax"]),
            "confidence": float(row["confidence"]),
            "class": row["name"],
        }
        for _, row in detections.iterrows()
    ]
