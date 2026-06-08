"""Multi-lane traffic analysis helpers.

This module handles lane geometry, detection-to-lane assignment, lane-level
aggregation, lightweight overlay rendering, and CSV logging. It intentionally
does not call density, congestion, priority, or signal timing modules.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import cv2

logger = logging.getLogger(__name__)


DEFAULT_LANE_COUNT = 3
DEFAULT_LOG_PATH = Path("data/logs/lane_analysis_log.csv")
VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck"}
LANE_COLORS = [(80, 180, 80), (40, 180, 255), (220, 120, 255), (80, 160, 255)]

LANE_LOG_COLUMNS = [
    "timestamp",
    "source_video",
    "frame_index",
    "timestamp_seconds",
    "lane_id",
    "lane_name",
    "total_vehicles",
    "car_count",
    "motorcycle_count",
    "bus_count",
    "truck_count",
    "emergency_present",
    "lane_utilization_percent",
]


@dataclass(frozen=True)
class LaneRegion:
    """Rectangular lane region in frame coordinates."""

    lane_id: str
    lane_name: str
    x_min: int
    y_min: int
    x_max: int
    y_max: int


@dataclass(frozen=True)
class LaneAnalysisResult:
    """Aggregated lane-level traffic counts."""

    lane_id: str
    lane_name: str
    total_vehicles: int
    car_count: int
    motorcycle_count: int
    bus_count: int
    truck_count: int
    emergency_present: bool
    lane_utilization_percent: float


@dataclass(frozen=True)
class LaneAnalysisLogRecord:
    """CSV-compatible lane analysis log record."""

    timestamp: str
    source_video: str
    frame_index: int
    timestamp_seconds: float
    lane_id: str
    lane_name: str
    total_vehicles: int
    car_count: int
    motorcycle_count: int
    bus_count: int
    truck_count: int
    emergency_present: bool
    lane_utilization_percent: float


def default_lane_config(frame_width: int, frame_height: int, lane_count: int = DEFAULT_LANE_COUNT) -> list[LaneRegion]:
    """Generate a simple vertical lane split for a frame."""

    width = max(1, int(frame_width or 1))
    height = max(1, int(frame_height or 1))
    lanes = max(1, int(lane_count or DEFAULT_LANE_COUNT))
    lane_width = width / lanes

    regions: list[LaneRegion] = []
    for index in range(lanes):
        x_min = int(round(index * lane_width))
        x_max = width if index == lanes - 1 else int(round((index + 1) * lane_width))
        lane_number = index + 1
        regions.append(
            LaneRegion(
                lane_id=f"LANE_{lane_number}",
                lane_name=f"Lane {lane_number}",
                x_min=x_min,
                y_min=0,
                x_max=x_max,
                y_max=height,
            )
        )
    return regions


def _read_attr_or_key(value: Any, name: str, default: Any = None) -> Any:
    """Read a field from a dictionary or object."""

    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _extract_bbox(detection: Any) -> tuple[int, int, int, int] | None:
    """Extract a bbox from project vehicle or ambulance detection records."""

    try:
        bbox = _read_attr_or_key(detection, "bbox")
        if bbox is not None and len(bbox) == 4:
            xmin, ymin, xmax, ymax = bbox
        else:
            xmin = _read_attr_or_key(detection, "xmin")
            ymin = _read_attr_or_key(detection, "ymin")
            xmax = _read_attr_or_key(detection, "xmax")
            ymax = _read_attr_or_key(detection, "ymax")
        return int(xmin), int(ymin), int(xmax), int(ymax)
    except (TypeError, ValueError):
        logger.warning("Skipping detection with malformed bounding box: %s", detection)
        return None


def detection_center(detection: Any) -> tuple[float, float] | None:
    """Return the center point of a detection bbox."""

    bbox = _extract_bbox(detection)
    if bbox is None:
        return None
    xmin, ymin, xmax, ymax = bbox
    return ((xmin + xmax) / 2, (ymin + ymax) / 2)


def assign_detection_to_lane(detection: Any, lane_regions: Iterable[LaneRegion]) -> str | None:
    """Assign one detection to a lane by bbox center point."""

    center = detection_center(detection)
    if center is None:
        return None
    center_x, center_y = center

    for lane in lane_regions:
        if lane.x_min <= center_x < lane.x_max and lane.y_min <= center_y < lane.y_max:
            return lane.lane_id
    return None


def _class_name(detection: Any) -> str:
    """Return normalized class name from a detection."""

    return str(_read_attr_or_key(detection, "class_name", "")).strip().lower()


def _empty_lane_counts(lane: LaneRegion) -> dict[str, Any]:
    """Create an empty mutable lane aggregate."""

    return {
        "lane_id": lane.lane_id,
        "lane_name": lane.lane_name,
        "total_vehicles": 0,
        "car_count": 0,
        "motorcycle_count": 0,
        "bus_count": 0,
        "truck_count": 0,
        "emergency_present": False,
    }


def analyze_lanes(
    vehicle_detections: Iterable[Any],
    ambulance_detections: Iterable[Any] | None = None,
    frame_width: int = 1,
    frame_height: int = 1,
    lane_regions: list[LaneRegion] | None = None,
) -> list[dict[str, Any]]:
    """Aggregate vehicle and emergency detections by lane."""

    regions = lane_regions or default_lane_config(frame_width, frame_height)
    lane_map = {lane.lane_id: _empty_lane_counts(lane) for lane in regions}
    total_detected_vehicles = 0

    for detection in vehicle_detections or []:
        class_name = _class_name(detection)
        if class_name not in VEHICLE_CLASSES:
            continue
        lane_id = assign_detection_to_lane(detection, regions)
        if lane_id is None or lane_id not in lane_map:
            continue
        lane_map[lane_id][f"{class_name}_count"] += 1
        lane_map[lane_id]["total_vehicles"] += 1
        total_detected_vehicles += 1

    for detection in ambulance_detections or []:
        lane_id = assign_detection_to_lane(detection, regions)
        if lane_id is not None and lane_id in lane_map:
            lane_map[lane_id]["emergency_present"] = True

    results: list[dict[str, Any]] = []
    for lane in regions:
        lane_result = lane_map[lane.lane_id]
        utilization = (
            round((lane_result["total_vehicles"] / total_detected_vehicles) * 100, 2)
            if total_detected_vehicles > 0
            else 0.0
        )
        results.append(
            asdict(
                LaneAnalysisResult(
                    lane_id=str(lane_result["lane_id"]),
                    lane_name=str(lane_result["lane_name"]),
                    total_vehicles=int(lane_result["total_vehicles"]),
                    car_count=int(lane_result["car_count"]),
                    motorcycle_count=int(lane_result["motorcycle_count"]),
                    bus_count=int(lane_result["bus_count"]),
                    truck_count=int(lane_result["truck_count"]),
                    emergency_present=bool(lane_result["emergency_present"]),
                    lane_utilization_percent=utilization,
                )
            )
        )
    logger.info("Generated lane analysis for %s lane(s).", len(results))
    return results


def draw_lane_overlay(frame: Any, lane_regions: Iterable[LaneRegion], lane_results: Iterable[dict[str, Any]] | None = None) -> Any:
    """Draw lane regions and compact lane labels on an annotated frame."""

    annotated = frame.copy()
    results_by_lane = {
        str(result.get("lane_id")): result
        for result in (lane_results or [])
        if isinstance(result, dict)
    }

    for index, lane in enumerate(lane_regions):
        color = LANE_COLORS[index % len(LANE_COLORS)]
        cv2.rectangle(annotated, (lane.x_min, lane.y_min), (lane.x_max, lane.y_max), color, 2)
        result = results_by_lane.get(lane.lane_id, {})
        total = int(result.get("total_vehicles", 0) or 0)
        label = f"{lane.lane_name}: {total}"
        label_x = lane.x_min + 8
        label_y = max(24, lane.y_min + 28)
        cv2.putText(
            annotated,
            label,
            (label_x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            color,
            2,
            cv2.LINE_AA,
        )
    return annotated


def build_lane_analysis_log_records(
    lane_results: Iterable[dict[str, Any]],
    source_video: str = "",
    frame_index: int = 0,
    timestamp_seconds: float = 0.0,
    timestamp: str | None = None,
) -> list[LaneAnalysisLogRecord]:
    """Build CSV log records from lane analysis results."""

    record_timestamp = timestamp or datetime.now().isoformat(timespec="seconds")
    records: list[LaneAnalysisLogRecord] = []
    for result in lane_results:
        try:
            records.append(
                LaneAnalysisLogRecord(
                    timestamp=record_timestamp,
                    source_video=source_video,
                    frame_index=int(frame_index),
                    timestamp_seconds=round(float(timestamp_seconds), 3),
                    lane_id=str(result.get("lane_id", "")),
                    lane_name=str(result.get("lane_name", "")),
                    total_vehicles=int(result.get("total_vehicles", 0) or 0),
                    car_count=int(result.get("car_count", 0) or 0),
                    motorcycle_count=int(result.get("motorcycle_count", 0) or 0),
                    bus_count=int(result.get("bus_count", 0) or 0),
                    truck_count=int(result.get("truck_count", 0) or 0),
                    emergency_present=bool(result.get("emergency_present", False)),
                    lane_utilization_percent=round(float(result.get("lane_utilization_percent", 0.0) or 0.0), 2),
                )
            )
        except (TypeError, ValueError) as error:
            logger.warning("Skipping malformed lane result for logging: %s, error: %s", result, error)
    return records


def write_lane_analysis_log(records: Iterable[LaneAnalysisLogRecord], log_path: str | Path = DEFAULT_LOG_PATH) -> None:
    """Write lane analysis records to CSV."""

    path = Path(log_path)
    logger.info("Writing lane analysis log to: %s", path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=LANE_LOG_COLUMNS)
            writer.writeheader()
            for record in records:
                writer.writerow(asdict(record))
    except Exception as error:
        logger.error("Failed to write lane analysis log to %s: %s", path, error)
        raise
