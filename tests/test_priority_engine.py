from __future__ import annotations

from pathlib import Path
import pytest

from ml.analytics.priority_engine import (
    generate_priority_action,
    _normalize_bool,
    normalize_congestion,
    build_priority_log_record,
    write_priority_log,
    read_congestion_log,
    generate_actions_from_congestion_log,
    build_arg_parser,
)


def test_emergency_overrides_congestion_warning() -> None:
    result = generate_priority_action(
        True,
        {"density": "HIGH"},
        {"congestion": "HIGH_CONGESTION"},
    )

    assert result["recommended_action"] == "EMERGENCY_PRIORITY"
    assert result["emergency_present"] is True


def test_non_emergency_high_congestion_warns() -> None:
    result = generate_priority_action(
        False,
        {"density": "HIGH"},
        {"congestion": "HIGH_CONGESTION"},
    )

    assert result["recommended_action"] == "HIGH_TRAFFIC_WARNING"


def test_non_emergency_medium_congestion_extends_green() -> None:
    result = generate_priority_action(
        False,
        {"density": "MEDIUM"},
        {"congestion": "MEDIUM_CONGESTION"},
    )
    assert result["recommended_action"] == "EXTEND_GREEN"


def test_non_emergency_low_congestion_normal_op() -> None:
    result = generate_priority_action(
        False,
        {"density": "LOW"},
        {"congestion": "LOW_CONGESTION"},
    )
    assert result["recommended_action"] == "NORMAL_OPERATION"


def test_normalize_bool() -> None:
    # Booleans
    assert _normalize_bool(True) is True
    assert _normalize_bool(False) is False
    
    # Integers
    assert _normalize_bool(1) is True
    assert _normalize_bool(0) is False
    
    # Strings
    assert _normalize_bool("true") is True
    assert _normalize_bool("YES") is True
    assert _normalize_bool("detected") is True
    assert _normalize_bool("0") is False
    assert _normalize_bool("no") is False


def test_normalize_congestion() -> None:
    assert normalize_congestion("low_congestion ") == "LOW_CONGESTION"
    assert normalize_congestion("HIGH_CONGESTION") == "HIGH_CONGESTION"
    with pytest.raises(ValueError, match="Unsupported congestion"):
        normalize_congestion("UNKNOWN_CONGESTION")


def test_priority_csv_logging_lifecycle(tmp_path) -> None:
    log_path = tmp_path / "priority_actions.csv"
    
    action_result = {
        "emergency_present": True,
        "density": "MEDIUM",
        "congestion": "MEDIUM_CONGESTION",
        "recommended_action": "EMERGENCY_PRIORITY",
    }
    
    record = build_priority_log_record(action_result, timestamp="2026-06-08T12:00:00")
    write_priority_log(log_path, [record])
    assert log_path.exists()
    
    with pytest.raises(FileNotFoundError):
        read_congestion_log(tmp_path / "missing.csv")


def test_generate_actions_from_congestion_log(tmp_path) -> None:
    congestion_log = tmp_path / "congestion_analysis.csv"
    priority_log = tmp_path / "priority_actions.csv"
    
    # Write dummy congestion log
    congestion_log.write_text(
        "timestamp,total_vehicles,density,congestion\n"
        "2026-06-08T12:00:00,18,MEDIUM,MEDIUM_CONGESTION\n"
    )
    
    records = generate_actions_from_congestion_log(
        congestion_log, 
        priority_log, 
        emergency_present="true"
    )
    
    assert len(records) == 1
    assert records[0].emergency_present is True
    assert records[0].recommended_action == "EMERGENCY_PRIORITY"
    assert priority_log.exists()


def test_build_arg_parser() -> None:
    parser = build_arg_parser()
    args = parser.parse_args([
        "--congestion-log", "congestion.csv", 
        "--output-log", "output.csv",
        "--emergency-present"
    ])
    assert args.congestion_log == "congestion.csv"
    assert args.output_log == "output.csv"
    assert args.emergency_present is True
