"""Log writing service for TrafficIQ."""

from typing import Any, Iterable
from backend.core.config import (
    VEHICLE_DETECTIONS_PATH,
    EMERGENCY_DETECTIONS_PATH,
    DENSITY_ANALYSIS_PATH,
    CONGESTION_ANALYSIS_PATH,
    PRIORITY_ACTIONS_PATH,
)
from backend.utils.csv_helper import append_rows_to_csv

# Schema definitions
VEHICLE_DET_FIELDS = [
    "source_video", "frame_index", "timestamp_seconds", "class_id",
    "class_name", "confidence", "xmin", "ymin", "xmax", "ymax",
    "box_width", "box_height", "timestamp"
]

DENSITY_FIELDS = [
    "source_video", "frame_index", "timestamp_seconds", "total_vehicles",
    "car_count", "motorcycle_count", "bus_count", "truck_count", "density", "timestamp"
]

CONGESTION_FIELDS = ["timestamp", "total_vehicles", "density", "congestion"]

PRIORITY_FIELDS = ["timestamp", "emergency_present", "density", "congestion", "recommended_action"]

def log_vehicle_detections(rows: Iterable[dict[str, Any]]) -> None:
    """Log vehicle detection records to CSV."""
    append_rows_to_csv(VEHICLE_DETECTIONS_PATH, VEHICLE_DET_FIELDS, rows)

def log_emergency_detections(rows: Iterable[dict[str, Any]]) -> None:
    """Log emergency vehicle detection records to CSV."""
    append_rows_to_csv(EMERGENCY_DETECTIONS_PATH, VEHICLE_DET_FIELDS, rows)

def log_density_analysis(rows: Iterable[dict[str, Any]]) -> None:
    """Log traffic density analysis records to CSV."""
    append_rows_to_csv(DENSITY_ANALYSIS_PATH, DENSITY_FIELDS, rows)

def log_congestion_analysis(rows: Iterable[dict[str, Any]]) -> None:
    """Log congestion classification records to CSV."""
    append_rows_to_csv(CONGESTION_ANALYSIS_PATH, CONGESTION_FIELDS, rows)

def log_priority_actions(rows: Iterable[dict[str, Any]]) -> None:
    """Log priority recommendation records to CSV."""
    append_rows_to_csv(PRIORITY_ACTIONS_PATH, PRIORITY_FIELDS, rows)
