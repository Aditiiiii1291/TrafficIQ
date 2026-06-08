from __future__ import annotations

from pathlib import Path
import pytest

from ml.analytics.congestion_classifier import (
    classify_congestion,
    normalize_density,
    build_congestion_log_record,
    write_congestion_log,
    read_density_log,
    classify_congestion_from_density_log,
    build_arg_parser,
)


def test_classify_congestion_low_density() -> None:
    result = classify_congestion({"total_vehicles": 5, "density": "LOW"})
    assert result == {
        "total_vehicles": 5,
        "density": "LOW",
        "congestion": "LOW_CONGESTION",
    }


def test_classify_congestion_medium_density() -> None:
    result = classify_congestion({"total_vehicles": 18, "density": "MEDIUM"})

    assert result == {
        "total_vehicles": 18,
        "density": "MEDIUM",
        "congestion": "MEDIUM_CONGESTION",
    }


def test_classify_congestion_high_density() -> None:
    result = classify_congestion({"total_vehicles": 30, "density": "HIGH"})
    assert result == {
        "total_vehicles": 30,
        "density": "HIGH",
        "congestion": "HIGH_CONGESTION",
    }


def test_classify_congestion_rejects_unknown_density() -> None:
    with pytest.raises(ValueError, match="Unsupported density"):
        classify_congestion({"total_vehicles": 1, "density": "UNKNOWN"})


def test_normalize_density() -> None:
    assert normalize_density("low ") == "LOW"
    assert normalize_density("Medium") == "MEDIUM"
    with pytest.raises(ValueError):
        normalize_density("INVALID")


def test_congestion_csv_logging_lifecycle(tmp_path) -> None:
    log_path = tmp_path / "congestion_analysis.csv"
    
    congestion_result = {
        "total_vehicles": 18,
        "density": "MEDIUM",
        "congestion": "MEDIUM_CONGESTION",
    }
    
    record = build_congestion_log_record(congestion_result, timestamp="2026-06-08T12:00:00")
    write_congestion_log(log_path, [record])
    assert log_path.exists()
    
    with pytest.raises(FileNotFoundError):
        read_density_log(tmp_path / "missing.csv")


def test_classify_congestion_from_density_log(tmp_path) -> None:
    density_log = tmp_path / "density_analysis.csv"
    congestion_log = tmp_path / "congestion_analysis.csv"
    
    # Write a dummy density log
    density_log.write_text(
        "source_video,frame_index,timestamp_seconds,total_vehicles,car_count,motorcycle_count,bus_count,truck_count,density\n"
        "traffic.mp4,0,0.0,18,10,4,2,2,MEDIUM\n"
    )
    
    records = classify_congestion_from_density_log(density_log, congestion_log)
    
    assert len(records) == 1
    assert records[0].total_vehicles == 18
    assert records[0].density == "MEDIUM"
    assert records[0].congestion == "MEDIUM_CONGESTION"
    assert congestion_log.exists()


def test_build_arg_parser() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(["--density-log", "density.csv", "--output-log", "output.csv"])
    assert args.density_log == "density.csv"
    assert args.output_log == "output.csv"
