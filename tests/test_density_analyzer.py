from __future__ import annotations

from pathlib import Path
import pytest

from ml.analytics.density_analyzer import (
    analyze_density,
    count_vehicle_detections,
    normalize_vehicle_counts,
    classify_density,
    build_density_log_record,
    write_density_log,
    read_detection_log,
    analyze_density_from_detection_log,
    build_arg_parser,
    VehicleCounts,
)


def test_analyze_density_low_result() -> None:
    result = analyze_density({"car_count": 5, "motorcycle_count": 2})
    assert result["density"] == "LOW"
    assert result["total_vehicles"] == 7


def test_analyze_density_medium_result() -> None:
    result = analyze_density(
        {
            "car_count": 10,
            "motorcycle_count": 4,
            "bus_count": 2,
            "truck_count": 2,
        }
    )

    assert result == {
        "total_vehicles": 18,
        "car_count": 10,
        "motorcycle_count": 4,
        "bus_count": 2,
        "truck_count": 2,
        "density": "MEDIUM",
    }


def test_analyze_density_high_result() -> None:
    result = analyze_density({"car_count": 20, "bus_count": 10})
    assert result["density"] == "HIGH"
    assert result["total_vehicles"] == 30


def test_count_vehicle_detections_ignores_non_vehicle_classes() -> None:
    counts = count_vehicle_detections(
        [
            {"class_name": "car"},
            {"class_name": "car"},
            {"class_name": "bus"},
            {"class_name": "ambulance"},
        ]
    )

    assert counts.total_vehicles == 3
    assert counts.car_count == 2
    assert counts.bus_count == 1


def test_normalize_vehicle_counts() -> None:
    counts_obj = VehicleCounts(5, 3, 1, 1, 0)
    # 1. Input as VehicleCounts object
    assert normalize_vehicle_counts(counts_obj) == counts_obj

    # 2. Input as dict
    counts_dict = {
        "car_count": 3,
        "motorcycle_count": 1,
        "bus_count": 1,
        "truck_count": 0,
        "total_vehicles": 5,
    }
    assert normalize_vehicle_counts(counts_dict) == counts_obj


def test_classify_density() -> None:
    assert classify_density(0) == "LOW"
    assert classify_density(9) == "LOW"
    assert classify_density(10) == "MEDIUM"
    assert classify_density(24) == "MEDIUM"
    assert classify_density(25) == "HIGH"
    assert classify_density(100) == "HIGH"


def test_density_csv_logging_lifecycle(tmp_path) -> None:
    log_path = tmp_path / "density_analysis.csv"
    
    density_result = {
        "total_vehicles": 5,
        "car_count": 3,
        "motorcycle_count": 2,
        "bus_count": 0,
        "truck_count": 0,
        "density": "LOW",
    }
    
    record = build_density_log_record(
        density_result=density_result,
        source_video="traffic.mp4",
        frame_index=15,
        timestamp_seconds=0.5,
    )
    
    write_density_log(log_path, [record])
    assert log_path.exists()
    
    # Verify read operation throws on missing file
    with pytest.raises(FileNotFoundError):
        read_detection_log(tmp_path / "missing.csv")


def test_analyze_density_from_detection_log(tmp_path) -> None:
    detection_log = tmp_path / "vehicle_detections.csv"
    density_log = tmp_path / "density_analysis.csv"
    
    # Write a dummy detection log
    detection_log.write_text(
        "source_video,frame_index,timestamp_seconds,class_id,class_name,confidence,xmin,ymin,xmax,ymax,box_width,box_height\n"
        "traffic.mp4,0,0.0,2,car,0.9,10,10,20,20,10,10\n"
        "traffic.mp4,0,0.0,2,car,0.85,30,30,40,40,10,10\n"
        "traffic.mp4,0,0.0,5,bus,0.8,50,50,70,70,20,20\n"
    )
    
    records = analyze_density_from_detection_log(detection_log, density_log)
    
    assert len(records) == 1
    assert records[0].total_vehicles == 3
    assert records[0].car_count == 2
    assert records[0].bus_count == 1
    assert records[0].density == "LOW"
    assert density_log.exists()


def test_build_arg_parser() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(["--detections-log", "detections.csv", "--output-log", "output.csv"])
    assert args.detections_log == "detections.csv"
    assert args.output_log == "output.csv"
