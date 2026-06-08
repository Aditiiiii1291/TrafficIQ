from __future__ import annotations

import csv

from ml.analytics.signal_timing_engine import (
    CONFIDENCE_NOTE,
    DEFAULT_TARGET_LANE,
    EMERGENCY,
    EMERGENCY_PRIORITY,
    EXTEND_GREEN,
    HIGH,
    HIGH_TRAFFIC_WARNING,
    MAX_GREEN_SECONDS,
    MEDIUM,
    MIN_GREEN_SECONDS,
    NORMAL,
    NORMAL_GREEN_SECONDS,
    NORMAL_OPERATION,
    SignalTimingLogRecord,
    build_signal_timing_log_record,
    clamp_green_time,
    generate_signal_timing_recommendation,
    write_signal_timing_log,
)


def test_low_congestion_returns_normal_timing() -> None:
    result = generate_signal_timing_recommendation(
        {"total_vehicles": 5, "density": "LOW"},
        {"congestion": "LOW_CONGESTION"},
        {"recommended_action": NORMAL_OPERATION},
    )

    assert result["recommended_green_seconds"] == NORMAL_GREEN_SECONDS
    assert result["priority_action"] == NORMAL_OPERATION
    assert result["severity"] == NORMAL
    assert result["reason"] == "Low congestion detected"


def test_medium_congestion_extends_green() -> None:
    result = generate_signal_timing_recommendation(
        {"total_vehicles": 18, "density": "MEDIUM"},
        {"congestion": "MEDIUM_CONGESTION"},
        {"recommended_action": EXTEND_GREEN},
    )

    assert result["recommended_green_seconds"] > NORMAL_GREEN_SECONDS
    assert result["priority_action"] == EXTEND_GREEN
    assert result["severity"] == MEDIUM


def test_high_congestion_aggressively_extends_green() -> None:
    result = generate_signal_timing_recommendation(
        {"total_vehicles": 30, "density": "HIGH"},
        {"congestion": "HIGH_CONGESTION"},
        {"recommended_action": HIGH_TRAFFIC_WARNING},
    )

    assert result["recommended_green_seconds"] > 55
    assert result["priority_action"] == HIGH_TRAFFIC_WARNING
    assert result["severity"] == HIGH
    assert result["reason"] == "High congestion detected"


def test_emergency_override_takes_priority_over_congestion() -> None:
    result = generate_signal_timing_recommendation(
        {"total_vehicles": 5, "density": "LOW"},
        {"congestion": "LOW_CONGESTION"},
        {"emergency_present": True, "recommended_action": NORMAL_OPERATION},
    )

    assert result["recommended_green_seconds"] == MAX_GREEN_SECONDS
    assert result["priority_action"] == EMERGENCY_PRIORITY
    assert result["severity"] == EMERGENCY
    assert result["reason"] == "Emergency vehicle priority detected"


def test_invalid_input_falls_back_safely() -> None:
    result = generate_signal_timing_recommendation(None, "bad input", {"recommended_action": "INVALID"})

    assert result["recommended_green_seconds"] == NORMAL_GREEN_SECONDS
    assert result["priority_action"] == NORMAL_OPERATION
    assert result["severity"] == NORMAL
    assert result["target_lane"] == DEFAULT_TARGET_LANE


def test_timing_bounds_are_enforced() -> None:
    assert clamp_green_time(-100) == MIN_GREEN_SECONDS
    assert clamp_green_time(10_000) == MAX_GREEN_SECONDS

    emergency_result = generate_signal_timing_recommendation(
        {"density": "HIGH"},
        {"congestion": "HIGH_CONGESTION"},
        {"recommended_action": EMERGENCY_PRIORITY},
    )
    assert emergency_result["recommended_green_seconds"] == MAX_GREEN_SECONDS


def test_required_output_structure() -> None:
    result = generate_signal_timing_recommendation(
        {"total_vehicles": 18, "density": "MEDIUM"},
        {"congestion": "MEDIUM_CONGESTION"},
        {"recommended_action": EXTEND_GREEN},
    )

    assert set(result) == {
        "recommended_green_seconds",
        "min_green_seconds",
        "max_green_seconds",
        "priority_action",
        "severity",
        "target_lane",
        "reason",
        "confidence_note",
    }
    assert isinstance(result["recommended_green_seconds"], int)
    assert result["min_green_seconds"] == MIN_GREEN_SECONDS
    assert result["max_green_seconds"] == MAX_GREEN_SECONDS
    assert result["target_lane"] == DEFAULT_TARGET_LANE
    assert result["confidence_note"] == CONFIDENCE_NOTE


def test_csv_logging_behavior(tmp_path) -> None:
    log_path = tmp_path / "signal_timing_log.csv"
    result = generate_signal_timing_recommendation(
        {"total_vehicles": 30, "density": "HIGH"},
        {"congestion": "HIGH_CONGESTION"},
        {"recommended_action": HIGH_TRAFFIC_WARNING},
    )
    record = build_signal_timing_log_record(
        result,
        congestion="HIGH_CONGESTION",
        timestamp="2026-06-08T12:00:00",
    )

    write_signal_timing_log([record], log_path)

    assert log_path.exists()
    with log_path.open("r", newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows == [
        {
            "timestamp": "2026-06-08T12:00:00",
            "congestion": "HIGH_CONGESTION",
            "priority_action": HIGH_TRAFFIC_WARNING,
            "recommended_green_seconds": str(result["recommended_green_seconds"]),
        }
    ]
    assert isinstance(record, SignalTimingLogRecord)
