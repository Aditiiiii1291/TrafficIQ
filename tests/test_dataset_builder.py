from __future__ import annotations

import csv
from pathlib import Path
import pytest

from ml.prediction.dataset_builder import (
    build_training_dataset,
    _to_bool,
    generate_sample_training_records,
    build_arg_parser,
)


def test_dataset_builder_creates_sample_when_logs_are_missing(tmp_path) -> None:
    output = tmp_path / "dataset.csv"
    records = build_training_dataset(tmp_path / "missing_logs", output)

    assert len(records) >= 9
    assert output.exists()

    with output.open("r", newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows[0]["congestion"] in {"LOW_CONGESTION", "MEDIUM_CONGESTION", "HIGH_CONGESTION"}
    assert "recommended_action" in rows[0]


def test_to_bool() -> None:
    assert _to_bool(True) is True
    assert _to_bool(False) is False
    assert _to_bool(1) is True
    assert _to_bool(0) is False
    assert _to_bool("detected") is True
    assert _to_bool("yes") is True
    assert _to_bool("no") is False
    assert _to_bool(None) is False


def test_dataset_builder_from_detection_logs(tmp_path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    # Write only a detections log file
    detections_log = logs_dir / "vehicle_detections.csv"
    detections_log.write_text(
        "source_video,frame_index,timestamp_seconds,class_id,class_name,confidence,xmin,ymin,xmax,ymax,box_width,box_height\n"
        "traffic.mp4,0,0.0,2,car,0.9,10,10,20,20,10,10\n"
        "traffic.mp4,0,0.0,5,bus,0.85,30,30,50,50,20,20\n"
        "traffic.mp4,0,0.0,0,ambulance,0.8,60,60,80,80,20,20\n"
    )
    
    output = tmp_path / "dataset.csv"
    records = build_training_dataset(logs_dir, output, allow_sample_fallback=False)
    
    assert len(records) == 1
    assert records[0].total_vehicles == 2  # car + bus
    assert records[0].emergency_present is True
    assert records[0].recommended_action == "EMERGENCY_PRIORITY"


def test_dataset_builder_from_merged_logs(tmp_path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    # Write density, congestion, and priority logs
    (logs_dir / "density_analysis.csv").write_text(
        "source_video,frame_index,timestamp_seconds,total_vehicles,car_count,motorcycle_count,bus_count,truck_count,density\n"
        "traffic.mp4,0,10.0,15,8,4,2,1,MEDIUM\n"
    )
    (logs_dir / "congestion_analysis.csv").write_text(
        "timestamp,total_vehicles,density,congestion\n"
        "10.0,15,MEDIUM,MEDIUM_CONGESTION\n"
    )
    (logs_dir / "priority_actions.csv").write_text(
        "timestamp,emergency_present,density,congestion,recommended_action\n"
        "10.0,True,MEDIUM,MEDIUM_CONGESTION,EMERGENCY_PRIORITY\n"
    )
    
    output = tmp_path / "dataset.csv"
    records = build_training_dataset(logs_dir, output, allow_sample_fallback=False)
    
    assert len(records) == 1
    assert records[0].timestamp == "10.0"
    assert records[0].total_vehicles == 15
    assert records[0].density == "MEDIUM"
    assert records[0].congestion == "MEDIUM_CONGESTION"
    assert records[0].emergency_present is True
    assert records[0].recommended_action == "EMERGENCY_PRIORITY"


def test_build_arg_parser() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(["--logs", "logs_path", "--output", "out.csv", "--no-sample-fallback"])
    assert args.logs == "logs_path"
    assert args.output == "out.csv"
    assert args.no_sample_fallback is True
