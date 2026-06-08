from __future__ import annotations

import csv

import numpy as np

from ml.analytics.lane_analyzer import (
    LaneAnalysisLogRecord,
    LaneRegion,
    analyze_lanes,
    assign_detection_to_lane,
    build_lane_analysis_log_records,
    default_lane_config,
    draw_lane_overlay,
    write_lane_analysis_log,
)


def test_default_lane_creation() -> None:
    lanes = default_lane_config(frame_width=300, frame_height=100, lane_count=3)

    assert len(lanes) == 3
    assert lanes[0] == LaneRegion("LANE_1", "Lane 1", 0, 0, 100, 100)
    assert lanes[1].x_min == 100
    assert lanes[2].x_max == 300


def test_lane_assignment_by_detection_center() -> None:
    lanes = default_lane_config(300, 100, 3)

    assert assign_detection_to_lane({"xmin": 120, "ymin": 10, "xmax": 150, "ymax": 30}, lanes) == "LANE_2"
    assert assign_detection_to_lane({"bbox": [230, 10, 260, 30]}, lanes) == "LANE_3"


def test_empty_detections_return_zero_counts() -> None:
    results = analyze_lanes([], [], frame_width=300, frame_height=100)

    assert len(results) == 3
    assert all(result["total_vehicles"] == 0 for result in results)
    assert all(result["lane_utilization_percent"] == 0.0 for result in results)


def test_malformed_detections_are_ignored() -> None:
    results = analyze_lanes(
        [
            {"class_name": "car", "xmin": "bad", "ymin": 0, "xmax": 10, "ymax": 10},
            {"class_name": "truck", "xmin": 10, "ymin": 0, "xmax": 20, "ymax": 10},
        ],
        frame_width=300,
        frame_height=100,
    )

    assert sum(result["total_vehicles"] for result in results) == 1


def test_utilization_calculation() -> None:
    lanes = default_lane_config(300, 100, 3)
    detections = [
        {"class_name": "car", "xmin": 10, "ymin": 0, "xmax": 20, "ymax": 10},
        {"class_name": "bus", "xmin": 30, "ymin": 0, "xmax": 40, "ymax": 10},
        {"class_name": "truck", "xmin": 120, "ymin": 0, "xmax": 130, "ymax": 10},
        {"class_name": "motorcycle", "xmin": 240, "ymin": 0, "xmax": 250, "ymax": 10},
    ]

    results = analyze_lanes(detections, frame_width=300, frame_height=100, lane_regions=lanes)

    assert results[0]["total_vehicles"] == 2
    assert results[0]["lane_utilization_percent"] == 50.0
    assert results[1]["lane_utilization_percent"] == 25.0
    assert results[2]["lane_utilization_percent"] == 25.0


def test_ambulance_detection_marks_lane_emergency() -> None:
    results = analyze_lanes(
        vehicle_detections=[],
        ambulance_detections=[{"class_name": "ambulance", "bbox": [120, 0, 140, 20]}],
        frame_width=300,
        frame_height=100,
    )

    assert results[1]["emergency_present"] is True
    assert results[0]["emergency_present"] is False


def test_overlay_rendering_returns_frame_copy() -> None:
    frame = np.zeros((100, 300, 3), dtype=np.uint8)
    lanes = default_lane_config(300, 100, 3)
    results = analyze_lanes([], [], frame_width=300, frame_height=100, lane_regions=lanes)

    annotated = draw_lane_overlay(frame, lanes, results)

    assert annotated is not frame
    assert annotated.shape == frame.shape


def test_output_structure_validation() -> None:
    result = analyze_lanes(
        [{"class_name": "car", "xmin": 10, "ymin": 0, "xmax": 20, "ymax": 10}],
        frame_width=300,
        frame_height=100,
    )[0]

    assert set(result) == {
        "lane_id",
        "lane_name",
        "total_vehicles",
        "car_count",
        "motorcycle_count",
        "bus_count",
        "truck_count",
        "emergency_present",
        "lane_utilization_percent",
    }
    assert result["lane_id"] == "LANE_1"
    assert result["lane_name"] == "Lane 1"


def test_csv_logging(tmp_path) -> None:
    log_path = tmp_path / "lane_analysis_log.csv"
    lane_results = analyze_lanes(
        [{"class_name": "car", "xmin": 10, "ymin": 0, "xmax": 20, "ymax": 10}],
        frame_width=300,
        frame_height=100,
    )
    records = build_lane_analysis_log_records(
        lane_results,
        source_video="traffic.mp4",
        frame_index=5,
        timestamp_seconds=0.25,
        timestamp="2026-06-08T12:00:00",
    )

    write_lane_analysis_log(records, log_path)

    assert log_path.exists()
    assert isinstance(records[0], LaneAnalysisLogRecord)
    with log_path.open("r", newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 3
    assert rows[0]["timestamp"] == "2026-06-08T12:00:00"
    assert rows[0]["source_video"] == "traffic.mp4"
    assert rows[0]["lane_id"] == "LANE_1"
    assert rows[0]["total_vehicles"] == "1"
