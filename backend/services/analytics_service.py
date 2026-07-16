"""Analytics service for TrafficIQ."""

from pathlib import Path
from typing import Any
from backend.core.config import LOGS_DIR
from ml.analytics.history_analytics import (
    load_historical_records as ml_load_historical_records,
    filter_records as ml_filter_records,
    generate_summary as ml_generate_summary,
    generate_trend_data as ml_generate_trend_data,
    generate_event_statistics as ml_generate_event_statistics,
    HistoricalRecord,
)

def load_historical_records(logs_dir: Path = LOGS_DIR) -> list[HistoricalRecord]:
    """Load historical records from log directory."""
    return ml_load_historical_records(logs_dir)

def filter_records(
    records: list[HistoricalRecord],
    date_filter: str | None = None,
    congestion_level: str = "ALL",
    recommendation: str = "ALL",
) -> list[HistoricalRecord]:
    """Filter historical records based on user queries."""
    return ml_filter_records(
        records,
        date_filter=date_filter,
        congestion_level=congestion_level,
        recommendation=recommendation,
    )

def generate_summary(records: list[HistoricalRecord]) -> dict[str, Any]:
    """Generate summary metrics for historical records."""
    return ml_generate_summary(records)

def generate_trend_data(records: list[HistoricalRecord]) -> dict[str, Any]:
    """Generate trend distributions and vehicle count timelines."""
    return ml_generate_trend_data(records)

def generate_event_statistics(records: list[HistoricalRecord]) -> dict[str, Any]:
    """Generate event-level metrics such as emergency event rate."""
    return ml_generate_event_statistics(records)
