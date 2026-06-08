from __future__ import annotations

from pathlib import Path
import pytest

from ml.analytics.history_analytics import (
    load_historical_records,
    filter_records,
    generate_summary,
    generate_trend_data,
    generate_event_statistics,
    export_history_summary,
    build_arg_parser,
    HistoricalRecord,
)


def test_history_analytics_handles_missing_logs(tmp_path) -> None:
    records = load_historical_records(tmp_path)
    summary = generate_summary(records)
    event_stats = generate_event_statistics(records)

    assert summary["total_analyzed_records"] == 0
    assert summary["most_common_congestion_level"] == "N/A"
    assert event_stats["emergency_rate"] == 0.0


def test_load_and_filter_historical_records(tmp_path) -> None:
    # 1. Write mock logs
    (tmp_path / "density_analysis.csv").write_text(
        "source_video,frame_index,timestamp_seconds,total_vehicles,car_count,motorcycle_count,bus_count,truck_count,density\n"
        "video1.mp4,0,10.0,5,3,2,0,0,LOW\n"
        "video1.mp4,1,20.0,26,15,5,3,3,HIGH\n"
    )
    (tmp_path / "congestion_analysis.csv").write_text(
        "timestamp,total_vehicles,density,congestion\n"
        "10.0,5,LOW,LOW_CONGESTION\n"
        "20.0,26,HIGH,HIGH_CONGESTION\n"
    )
    (tmp_path / "priority_actions.csv").write_text(
        "timestamp,emergency_present,density,congestion,recommended_action\n"
        "10.0,False,LOW,LOW_CONGESTION,NORMAL_OPERATION\n"
        "20.0,True,HIGH,HIGH_CONGESTION,EMERGENCY_PRIORITY\n"
    )

    records = load_historical_records(tmp_path)
    assert len(records) == 2
    assert records[0].total_vehicles == 5
    assert records[0].congestion == "LOW_CONGESTION"
    assert records[1].emergency_present is True
    assert records[1].recommended_action == "EMERGENCY_PRIORITY"

    # 2. Test filtering
    low_records = filter_records(records, congestion_level="LOW_CONGESTION")
    assert len(low_records) == 1
    assert low_records[0].congestion == "LOW_CONGESTION"

    emergency_records = filter_records(records, recommendation="EMERGENCY_PRIORITY")
    assert len(emergency_records) == 1
    assert emergency_records[0].recommended_action == "EMERGENCY_PRIORITY"

    filtered_by_time = filter_records(records, date_filter="10")
    assert len(filtered_by_time) == 1
    assert filtered_by_time[0].timestamp == "10.0"


def test_generate_trend_and_stats() -> None:
    records = [
        HistoricalRecord("10", 5, "LOW", "LOW_CONGESTION", False, "NORMAL_OPERATION"),
        HistoricalRecord("20", 25, "HIGH", "HIGH_CONGESTION", True, "EMERGENCY_PRIORITY"),
    ]

    trends = generate_trend_data(records)
    assert len(trends["vehicle_count_over_time"]) == 2
    assert trends["density_distribution"]["LOW"] == 1
    assert trends["density_distribution"]["HIGH"] == 1

    stats = generate_event_statistics(records)
    assert stats["emergency_event_frequency"] == 1
    assert stats["emergency_rate"] == 0.5


def test_export_history_summary(tmp_path) -> None:
    records = [
        HistoricalRecord("10", 5, "LOW", "LOW_CONGESTION", False, "NORMAL_OPERATION"),
    ]
    out_csv = tmp_path / "summary.csv"
    export_history_summary(records, out_csv)
    
    assert out_csv.exists()
    content = out_csv.read_text()
    assert "timestamp,total_vehicles,density,congestion,emergency_present,recommended_action" in content


def test_build_arg_parser() -> None:
    parser = build_arg_parser()
    args = parser.parse_args([
        "--logs", "logs_path", 
        "--date", "2026-06-08", 
        "--congestion", "HIGH_CONGESTION",
        "--recommendation", "EMERGENCY_PRIORITY",
        "--export", "export.csv"
    ])
    assert args.logs == "logs_path"
    assert args.date == "2026-06-08"
    assert args.congestion == "HIGH_CONGESTION"
    assert args.recommendation == "EMERGENCY_PRIORITY"
    assert args.export == "export.csv"
