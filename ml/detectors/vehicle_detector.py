"""Phase 3 YOLOv8n vehicle detection pipeline.

This module detects COCO vehicle classes only:
car, bus, truck, and motorcycle. Ambulance-specific logic is intentionally
left for Phase 4.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.cv_pipeline import get_video_metadata, iter_frames, validate_video_path


VEHICLE_CLASS_IDS = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

BOX_COLORS = {
    "car": (40, 180, 255),
    "motorcycle": (255, 180, 40),
    "bus": (80, 220, 80),
    "truck": (220, 120, 255),
}

LOG_COLUMNS = [
    "source_video",
    "frame_index",
    "timestamp_seconds",
    "class_id",
    "class_name",
    "confidence",
    "xmin",
    "ymin",
    "xmax",
    "ymax",
    "box_width",
    "box_height",
]

_MODEL_CACHE: dict[str, YOLO] = {}


@dataclass(frozen=True)
class Detection:
    """Single vehicle detection result for one frame."""

    source_video: str
    frame_index: int
    timestamp_seconds: float
    class_id: int
    class_name: str
    confidence: float
    xmin: int
    ymin: int
    xmax: int
    ymax: int
    box_width: int
    box_height: int


@dataclass(frozen=True)
class DetectionSummary:
    """Summary returned after YOLO vehicle detection finishes."""

    input_path: str
    output_path: str
    log_path: str
    model_path: str
    confidence_threshold: float
    skip_frames: int
    total_frames: int
    processed_frames: int
    total_detections: int
    car_count: int
    motorcycle_count: int
    bus_count: int
    truck_count: int


def load_yolo_model(model_path: str | Path = "yolov8n.pt") -> YOLO:
    """Load and cache a YOLO model.

    The default `yolov8n.pt` baseline is CPU-friendly. Ultralytics will use a
    local file when present, or download the file on first use when networking
    is available.
    """

    key = str(model_path)
    if key not in _MODEL_CACHE:
        _MODEL_CACHE[key] = YOLO(key)
    return _MODEL_CACHE[key]


def _extract_detections(
    results: list[Any],
    frame_index: int,
    fps: float,
    source_video: str,
) -> list[Detection]:
    """Convert raw YOLO results into project detection records."""

    detections: list[Detection] = []
    timestamp_seconds = frame_index / fps if fps > 0 else 0.0

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            class_name = VEHICLE_CLASS_IDS.get(class_id)
            if class_name is None:
                continue

            confidence = float(box.conf[0].item())
            xmin, ymin, xmax, ymax = [int(value) for value in box.xyxy[0].tolist()]

            detections.append(
                Detection(
                    source_video=source_video,
                    frame_index=frame_index,
                    timestamp_seconds=round(timestamp_seconds, 3),
                    class_id=class_id,
                    class_name=class_name,
                    confidence=round(confidence, 4),
                    xmin=xmin,
                    ymin=ymin,
                    xmax=xmax,
                    ymax=ymax,
                    box_width=max(0, xmax - xmin),
                    box_height=max(0, ymax - ymin),
                )
            )

    return detections


def draw_vehicle_detections(frame: Any, detections: list[Detection]) -> Any:
    """Draw bounding boxes and confidence labels for vehicle detections."""

    annotated = frame.copy()

    for detection in detections:
        color = BOX_COLORS.get(detection.class_name, (255, 255, 255))
        label = f"{detection.class_name} {detection.confidence:.2f}"

        cv2.rectangle(
            annotated,
            (detection.xmin, detection.ymin),
            (detection.xmax, detection.ymax),
            color,
            2,
        )

        label_y = max(24, detection.ymin - 8)
        cv2.rectangle(
            annotated,
            (detection.xmin, label_y - 22),
            (detection.xmin + max(120, len(label) * 11), label_y + 4),
            color,
            -1,
        )
        cv2.putText(
            annotated,
            label,
            (detection.xmin + 6, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (20, 20, 20),
            2,
            cv2.LINE_AA,
        )

    return annotated


def draw_frame_summary(
    frame: Any,
    frame_index: int,
    total_frames: int,
    fps: float,
    detections: list[Detection],
) -> Any:
    """Add frame-level metadata and vehicle counts to the annotated frame."""

    annotated = frame.copy()
    class_counts = Counter(detection.class_name for detection in detections)
    timestamp_seconds = frame_index / fps if fps > 0 else 0.0

    lines = [
        f"Frame: {frame_index + 1}/{total_frames if total_frames else '?'}",
        f"FPS: {fps:.2f} | Time: {timestamp_seconds:.2f}s",
        "Vehicles: "
        + ", ".join(f"{name}: {class_counts.get(name, 0)}" for name in ["car", "motorcycle", "bus", "truck"]),
    ]

    x, y = 16, 32
    for line in lines:
        cv2.putText(
            annotated,
            line,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            annotated,
            line,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (20, 20, 20),
            1,
            cv2.LINE_AA,
        )
        y += 27

    return annotated


def detect_vehicles(
    frame: Any,
    model: YOLO | None = None,
    confidence_threshold: float = 0.35,
    frame_index: int = 0,
    fps: float = 0.0,
    source_video: str = "",
) -> tuple[Any, list[Detection]]:
    """Detect vehicles in one frame and return annotated frame plus detections."""

    detector = model if model is not None else load_yolo_model()
    results = detector.predict(
        source=frame,
        conf=confidence_threshold,
        classes=list(VEHICLE_CLASS_IDS.keys()),
        verbose=False,
    )
    detections = _extract_detections(
        results=results,
        frame_index=frame_index,
        fps=fps,
        source_video=source_video,
    )
    annotated = draw_vehicle_detections(frame, detections)
    return annotated, detections


def write_detection_log(log_path: str | Path, detections: list[Detection]) -> None:
    """Write vehicle detections to a CSV log."""

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=LOG_COLUMNS)
        writer.writeheader()
        for detection in detections:
            writer.writerow(asdict(detection))


def should_process_frame(frame_index: int, skip_frames: int) -> bool:
    """Return True when a frame should be processed after skip-frame thinning."""

    if skip_frames < 0:
        raise ValueError("skip_frames must be 0 or greater")
    return frame_index % (skip_frames + 1) == 0


def process_video_with_vehicle_detection(
    input_path: str | Path,
    output_path: str | Path = "data/processed/vehicle_detection_output.mp4",
    log_path: str | Path = "data/logs/vehicle_detections.csv",
    model_path: str | Path = "yolov8n.pt",
    confidence_threshold: float = 0.35,
    display: bool = False,
    skip_frames: int = 0,
    max_frames: int | None = None,
) -> DetectionSummary:
    """Detect vehicles in a video, write an annotated video, and save CSV logs."""

    if skip_frames < 0:
        raise ValueError("skip_frames must be 0 or greater")
    if max_frames is not None and max_frames < 1:
        raise ValueError("max_frames must be None or 1 or greater")

    source = validate_video_path(input_path)
    metadata = get_video_metadata(source)
    model = load_yolo_model(model_path)

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

    all_detections: list[Detection] = []
    processed_frames = 0

    try:
        for frame_index, frame in iter_frames(source):
            if not should_process_frame(frame_index, skip_frames):
                continue
            if max_frames is not None and processed_frames >= max_frames:
                break

            annotated, detections = detect_vehicles(
                frame=frame,
                model=model,
                confidence_threshold=confidence_threshold,
                frame_index=frame_index,
                fps=metadata.fps,
                source_video=str(source),
            )
            all_detections.extend(detections)

            annotated = draw_frame_summary(
                annotated,
                frame_index=frame_index,
                total_frames=metadata.frame_count,
                fps=metadata.fps,
                detections=detections,
            )
            writer.write(annotated)
            processed_frames += 1

            if display:
                cv2.imshow("YOLOv8n Vehicle Detection", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        writer.release()
        if display:
            cv2.destroyAllWindows()

    write_detection_log(log_path, all_detections)

    class_counts = Counter(detection.class_name for detection in all_detections)
    return DetectionSummary(
        input_path=str(source),
        output_path=str(output),
        log_path=str(log_path),
        model_path=str(model_path),
        confidence_threshold=confidence_threshold,
        skip_frames=skip_frames,
        total_frames=metadata.frame_count,
        processed_frames=processed_frames,
        total_detections=len(all_detections),
        car_count=class_counts.get("car", 0),
        motorcycle_count=class_counts.get("motorcycle", 0),
        bus_count=class_counts.get("bus", 0),
        truck_count=class_counts.get("truck", 0),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for Phase 3 testing."""

    parser = argparse.ArgumentParser(description="Run YOLOv8n vehicle detection on a video.")
    parser.add_argument("--input", required=True, help="Path to the source video file.")
    parser.add_argument(
        "--output",
        default="data/processed/vehicle_detection_output.mp4",
        help="Path where the annotated output video will be saved.",
    )
    parser.add_argument(
        "--log",
        default="data/logs/vehicle_detections.csv",
        help="Path where the detection CSV log will be saved.",
    )
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="YOLO model path. Use yolov8n.pt for the baseline detector.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.35,
        help="Minimum confidence threshold for detections.",
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
    """Run YOLOv8n vehicle detection from the command line."""

    args = build_arg_parser().parse_args()
    summary = process_video_with_vehicle_detection(
        input_path=args.input,
        output_path=args.output,
        log_path=args.log,
        model_path=args.model,
        confidence_threshold=args.confidence,
        display=args.display,
        skip_frames=args.skip_frames,
        max_frames=args.max_frames,
    )

    print("Phase 3 YOLOv8n vehicle detection complete")
    for key, value in asdict(summary).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
