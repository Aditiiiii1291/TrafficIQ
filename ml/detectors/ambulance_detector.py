"""Phase 4 ambulance detection infrastructure.

This module keeps ambulance detection separate from the generic vehicle
detector. It expects a future custom YOLO model trained for ambulance detection
and does not claim real-world accuracy.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.cv_pipeline import get_video_metadata, iter_frames, validate_video_path
from ml.detectors.vehicle_detector import (
    Detection,
    LOG_COLUMNS,
    detect_vehicles,
    load_yolo_model,
    should_process_frame,
)


DEFAULT_AMBULANCE_MODEL_PATH = Path("data/models/ambulance_detector.pt")
AMBULANCE_CLASS_NAMES = {"ambulance", "emergency vehicle", "emergency_vehicle"}
AMBULANCE_COLOR = (40, 40, 255)
AMBULANCE_MODEL_ENV_VAR = "AMBULANCE_MODEL_PATH"

_AMBULANCE_MODEL_CACHE: dict[str, YOLO] = {}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmergencyDetectionSummary:
    """Summary returned after combined vehicle and ambulance detection."""

    input_path: str
    output_path: str
    log_path: str
    vehicle_model_path: str
    ambulance_model_path: str
    vehicle_confidence_threshold: float
    ambulance_confidence_threshold: float
    skip_frames: int
    total_frames: int
    processed_frames: int
    total_vehicle_detections: int
    total_ambulance_detections: int
    emergency_detected: bool


def resolve_ambulance_model_path(model_path: str | Path | None = None) -> Path:
    """Resolve the ambulance model path from an argument, env var, or default."""

    if model_path is not None:
        return Path(model_path)

    configured_path = os.getenv(AMBULANCE_MODEL_ENV_VAR)
    if configured_path:
        return Path(configured_path)

    return DEFAULT_AMBULANCE_MODEL_PATH


def load_ambulance_model(model_path: str | Path | None = None) -> YOLO:
    """Load and cache the ambulance detector model.

    The default path is `data/models/ambulance_detector.pt`, but callers can
    pass a different path or set AMBULANCE_MODEL_PATH. This keeps model loading
    isolated for future fine-tuned weights.
    """

    resolved_path = resolve_ambulance_model_path(model_path)
    key = str(resolved_path)
    if key not in _AMBULANCE_MODEL_CACHE:
        logger.info(f"Loading YOLO ambulance model from: {key}")
        try:
            _AMBULANCE_MODEL_CACHE[key] = YOLO(key)
        except Exception as error:
            logger.error(f"Failed to load ambulance model from {key}: {error}")
            raise RuntimeError(f"Failed to load ambulance model from {key}: {error}") from error
    return _AMBULANCE_MODEL_CACHE[key]


def get_ambulance_class_ids(model: YOLO) -> list[int]:
    """Find ambulance class IDs from a YOLO model's class-name metadata."""

    names = getattr(model, "names", {})
    if isinstance(names, dict):
        matches = [
            int(class_id)
            for class_id, class_name in names.items()
            if str(class_name).strip().lower() in AMBULANCE_CLASS_NAMES
        ]
    else:
        matches = [
            class_id
            for class_id, class_name in enumerate(names)
            if str(class_name).strip().lower() in AMBULANCE_CLASS_NAMES
        ]

    return matches or [0]


def _normalize_bbox(box: Any) -> list[int]:
    """Convert a YOLO box into [xmin, ymin, xmax, ymax]."""

    return [int(value) for value in box.xyxy[0].tolist()]


def _extract_ambulance_detections(results: list[Any]) -> list[dict[str, object]]:
    """Convert raw YOLO results into the public ambulance detection format."""

    detections: list[dict[str, object]] = []

    for result in results:
        for box in result.boxes:
            detections.append(
                {
                    "class_name": "ambulance",
                    "confidence": round(float(box.conf[0].item()), 4),
                    "bbox": _normalize_bbox(box),
                }
            )

    return detections


def draw_ambulance_detections(frame: Any, detections: list[dict[str, object]]) -> Any:
    """Draw ambulance boxes with visually distinct emergency annotations."""

    annotated = frame.copy()

    for detection in detections:
        xmin, ymin, xmax, ymax = [int(value) for value in detection["bbox"]]
        confidence = float(detection["confidence"])
        label = f"AMBULANCE {confidence:.2f}"

        cv2.rectangle(annotated, (xmin, ymin), (xmax, ymax), AMBULANCE_COLOR, 3)

        label_y = max(28, ymin - 10)
        cv2.rectangle(
            annotated,
            (xmin, label_y - 26),
            (xmin + max(165, len(label) * 13), label_y + 6),
            AMBULANCE_COLOR,
            -1,
        )
        cv2.putText(
            annotated,
            label,
            (xmin + 8, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    return annotated


def draw_emergency_status(frame: Any, detections: list[dict[str, object]]) -> Any:
    """Add frame-level emergency status overlay."""

    annotated = frame.copy()
    status = "DETECTED" if is_emergency_present(detections) else "NONE"
    label = f"Emergency Vehicle: {status}"
    color = AMBULANCE_COLOR if status == "DETECTED" else (80, 180, 80)

    cv2.rectangle(annotated, (16, 108), (430, 148), color, -1)
    cv2.putText(
        annotated,
        label,
        (28, 136),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    return annotated


def detect_ambulances(
    frame: Any,
    model: YOLO | None = None,
    confidence_threshold: float = 0.35,
    base_frame: Any | None = None,
) -> tuple[Any, list[dict[str, object]]]:
    """Detect ambulances in one frame and return annotated frame plus detections."""

    detector = model if model is not None else load_ambulance_model()
    results = detector.predict(
        source=frame,
        conf=confidence_threshold,
        classes=get_ambulance_class_ids(detector),
        verbose=False,
    )
    detections = _extract_ambulance_detections(results)

    annotated = base_frame.copy() if base_frame is not None else frame.copy()
    annotated = draw_ambulance_detections(annotated, detections)
    annotated = draw_emergency_status(annotated, detections)
    return annotated, detections


def is_emergency_present(detections: list[dict[str, object]]) -> bool:
    """Return True when at least one ambulance detection is present."""

    return len(detections) > 0


def _ambulance_log_rows(
    detections: list[dict[str, object]],
    source_video: str,
    frame_index: int,
    fps: float,
) -> list[dict[str, object]]:
    """Convert public ambulance detections into CSV-compatible log rows."""

    timestamp_seconds = frame_index / fps if fps > 0 else 0.0
    rows: list[dict[str, object]] = []

    for detection in detections:
        xmin, ymin, xmax, ymax = [int(value) for value in detection["bbox"]]
        rows.append(
            {
                "source_video": source_video,
                "frame_index": frame_index,
                "timestamp_seconds": round(timestamp_seconds, 3),
                "class_id": 0,
                "class_name": "ambulance",
                "confidence": detection["confidence"],
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmax,
                "ymax": ymax,
                "box_width": max(0, xmax - xmin),
                "box_height": max(0, ymax - ymin),
            }
        )

    return rows


def write_combined_detection_log(log_path: str | Path, rows: list[dict[str, object]]) -> None:
    """Write vehicle and ambulance detections using the shared CSV format."""

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=LOG_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def process_video_with_emergency_detection(
    input_path: str | Path,
    output_path: str | Path = "data/processed/emergency_detection_output.mp4",
    log_path: str | Path = "data/logs/emergency_detections.csv",
    vehicle_model_path: str | Path = "yolov8n.pt",
    ambulance_model_path: str | Path | None = None,
    vehicle_confidence_threshold: float = 0.35,
    ambulance_confidence_threshold: float = 0.35,
    display: bool = False,
    skip_frames: int = 0,
    max_frames: int | None = None,
) -> EmergencyDetectionSummary:
    """Run vehicle detection followed by ambulance detection on a video."""

    if skip_frames < 0:
        raise ValueError("skip_frames must be 0 or greater")
    if max_frames is not None and max_frames < 1:
        raise ValueError("max_frames must be None or 1 or greater")

    source = validate_video_path(input_path)
    metadata = get_video_metadata(source)
    vehicle_model = load_yolo_model(vehicle_model_path)
    ambulance_model = load_ambulance_model(ambulance_model_path)
    resolved_ambulance_model_path = resolve_ambulance_model_path(ambulance_model_path)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    source_fps = metadata.fps if metadata.fps > 0 else 30.0
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        source_fps,
        (metadata.width, metadata.height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"OpenCV could not create output video: {output}")

    log_rows: list[dict[str, object]] = []
    processed_frames = 0
    total_vehicle_detections = 0
    total_ambulance_detections = 0

    try:
        for frame_index, frame in iter_frames(source):
            if not should_process_frame(frame_index, skip_frames):
                continue
            if max_frames is not None and processed_frames >= max_frames:
                break

            vehicle_annotated, vehicle_detections = detect_vehicles(
                frame=frame,
                model=vehicle_model,
                confidence_threshold=vehicle_confidence_threshold,
                frame_index=frame_index,
                fps=metadata.fps,
                source_video=str(source),
            )
            annotated, ambulance_detections = detect_ambulances(
                frame=frame,
                model=ambulance_model,
                confidence_threshold=ambulance_confidence_threshold,
                base_frame=vehicle_annotated,
            )

            log_rows.extend(asdict(detection) for detection in vehicle_detections)
            log_rows.extend(
                _ambulance_log_rows(
                    detections=ambulance_detections,
                    source_video=str(source),
                    frame_index=frame_index,
                    fps=metadata.fps,
                )
            )

            total_vehicle_detections += len(vehicle_detections)
            total_ambulance_detections += len(ambulance_detections)

            writer.write(annotated)
            processed_frames += 1

            if display:
                cv2.imshow("Emergency Vehicle Detection", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        writer.release()
        if display:
            cv2.destroyAllWindows()

    write_combined_detection_log(log_path, log_rows)

    return EmergencyDetectionSummary(
        input_path=str(source),
        output_path=str(output),
        log_path=str(log_path),
        vehicle_model_path=str(vehicle_model_path),
        ambulance_model_path=str(resolved_ambulance_model_path),
        vehicle_confidence_threshold=vehicle_confidence_threshold,
        ambulance_confidence_threshold=ambulance_confidence_threshold,
        skip_frames=skip_frames,
        total_frames=metadata.frame_count,
        processed_frames=processed_frames,
        total_vehicle_detections=total_vehicle_detections,
        total_ambulance_detections=total_ambulance_detections,
        emergency_detected=total_ambulance_detections > 0,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for Phase 4 testing."""

    parser = argparse.ArgumentParser(description="Run vehicle plus ambulance detection on a video.")
    parser.add_argument("--input", required=True, help="Path to the source video file.")
    parser.add_argument(
        "--output",
        default="data/processed/emergency_detection_output.mp4",
        help="Path where the annotated output video will be saved.",
    )
    parser.add_argument(
        "--log",
        default="data/logs/emergency_detections.csv",
        help="Path where the combined detection CSV log will be saved.",
    )
    parser.add_argument(
        "--vehicle-model",
        default="yolov8n.pt",
        help="YOLO model path for generic vehicle detection.",
    )
    parser.add_argument(
        "--ambulance-model",
        default=None,
        help="Custom ambulance YOLO model path. Defaults to data/models/ambulance_detector.pt.",
    )
    parser.add_argument(
        "--vehicle-confidence",
        type=float,
        default=0.35,
        help="Minimum confidence threshold for vehicle detections.",
    )
    parser.add_argument(
        "--ambulance-confidence",
        type=float,
        default=0.35,
        help="Minimum confidence threshold for ambulance detections.",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Display annotated frames in an OpenCV window. Press q to stop.",
    )
    parser.add_argument(
        "--skip-frames",
        type=int,
        default=0,
        help="Skip N frames after each processed frame. Example: 2 processes every third frame.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Optional maximum number of processed frames for quick tests.",
    )
    return parser


def main() -> None:
    """Run combined vehicle and ambulance detection from the command line."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    args = build_arg_parser().parse_args()
    summary = process_video_with_emergency_detection(
        input_path=args.input,
        output_path=args.output,
        log_path=args.log,
        vehicle_model_path=args.vehicle_model,
        ambulance_model_path=args.ambulance_model,
        vehicle_confidence_threshold=args.vehicle_confidence,
        ambulance_confidence_threshold=args.ambulance_confidence,
        display=args.display,
        skip_frames=args.skip_frames,
        max_frames=args.max_frames,
    )

    print("Phase 4 emergency vehicle detection infrastructure complete")
    for key, value in asdict(summary).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
