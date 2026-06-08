"""Rule-based smart signal timing recommendations.

This module consumes existing density, congestion, and priority outputs and
produces simulated green-time recommendations. It does not control traffic
signals or hardware.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)


MIN_GREEN_SECONDS = 20
MAX_GREEN_SECONDS = 90
NORMAL_GREEN_SECONDS = 35
MEDIUM_GREEN_SECONDS = 55
HIGH_GREEN_SECONDS = 75
EMERGENCY_GREEN_SECONDS = 100

DEFAULT_TARGET_LANE = "ALL"
CONFIDENCE_NOTE = "Rule-based recommendation"
DEFAULT_LOG_PATH = Path("data/logs/signal_timing_log.csv")

NORMAL_OPERATION = "NORMAL_OPERATION"
EXTEND_GREEN = "EXTEND_GREEN"
HIGH_TRAFFIC_WARNING = "HIGH_TRAFFIC_WARNING"
EMERGENCY_PRIORITY = "EMERGENCY_PRIORITY"

NORMAL = "NORMAL"
MEDIUM = "MEDIUM"
HIGH = "HIGH"
EMERGENCY = "EMERGENCY"

SIGNAL_TIMING_LOG_COLUMNS = [
    "timestamp",
    "congestion",
    "priority_action",
    "recommended_green_seconds",
]


@dataclass(frozen=True)
class SignalTimingRecommendation:
    """Structured signal timing recommendation for one analysis result."""

    recommended_green_seconds: int
    min_green_seconds: int
    max_green_seconds: int
    priority_action: str
    severity: str
    target_lane: str
    reason: str
    confidence_note: str


@dataclass(frozen=True)
class SignalTimingLogRecord:
    """CSV-compatible signal timing log record."""

    timestamp: str
    congestion: str
    priority_action: str
    recommended_green_seconds: int


def _to_bool(value: Any) -> bool:
    """Normalize bool-like values from dictionaries or CSV-style strings."""

    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "detected"}


def _safe_text(value: Any, default: str = "") -> str:
    """Return normalized uppercase text without raising on odd inputs."""

    if value is None:
        return default
    try:
        text = str(value).strip().upper()
    except Exception:
        logger.warning("Could not normalize text value for signal timing input.")
        return default
    return text or default


def _safe_int(value: Any, default: int = 0) -> int:
    """Return an integer value without raising on malformed input."""

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clamp_green_time(
    seconds: int,
    min_green_seconds: int = MIN_GREEN_SECONDS,
    max_green_seconds: int = MAX_GREEN_SECONDS,
) -> int:
    """Clamp a green-time recommendation inside configured safety bounds."""

    minimum = max(0, _safe_int(min_green_seconds, MIN_GREEN_SECONDS))
    maximum = max(minimum, _safe_int(max_green_seconds, MAX_GREEN_SECONDS))
    return max(minimum, min(_safe_int(seconds, NORMAL_GREEN_SECONDS), maximum))


def _read_congestion(density_result: dict[str, Any], congestion_result: dict[str, Any]) -> str:
    """Resolve congestion from Phase 5/6 results with a safe fallback."""

    congestion = _safe_text(congestion_result.get("congestion"), "")
    if congestion in {"LOW_CONGESTION", "MEDIUM_CONGESTION", "HIGH_CONGESTION"}:
        return congestion

    density = _safe_text(congestion_result.get("density"), "") or _safe_text(density_result.get("density"), "")
    density_to_congestion = {
        "LOW": "LOW_CONGESTION",
        "MEDIUM": "MEDIUM_CONGESTION",
        "HIGH": "HIGH_CONGESTION",
    }
    if density in density_to_congestion:
        return density_to_congestion[density]

    total_vehicles = _safe_int(density_result.get("total_vehicles"), 0)
    if total_vehicles >= 25:
        return "HIGH_CONGESTION"
    if total_vehicles >= 10:
        return "MEDIUM_CONGESTION"
    return "LOW_CONGESTION"


def _read_priority_action(priority_result: dict[str, Any], congestion: str) -> str:
    """Resolve priority action with a congestion-based fallback."""

    priority_action = _safe_text(priority_result.get("recommended_action"), "")
    if priority_action in {NORMAL_OPERATION, EXTEND_GREEN, HIGH_TRAFFIC_WARNING, EMERGENCY_PRIORITY}:
        return priority_action

    return {
        "LOW_CONGESTION": NORMAL_OPERATION,
        "MEDIUM_CONGESTION": EXTEND_GREEN,
        "HIGH_CONGESTION": HIGH_TRAFFIC_WARNING,
    }.get(congestion, NORMAL_OPERATION)


def _is_emergency(priority_result: dict[str, Any], priority_action: str) -> bool:
    """Return True when priority inputs indicate emergency priority."""

    return priority_action == EMERGENCY_PRIORITY or _to_bool(priority_result.get("emergency_present"))


def _build_recommendation(congestion: str, priority_action: str, emergency_present: bool) -> SignalTimingRecommendation:
    """Apply rule-based timing logic to normalized inputs."""

    if emergency_present:
        seconds = EMERGENCY_GREEN_SECONDS
        severity = EMERGENCY
        priority_action = EMERGENCY_PRIORITY
        reason = "Emergency vehicle priority detected"
    elif congestion == "HIGH_CONGESTION":
        seconds = HIGH_GREEN_SECONDS
        severity = HIGH
        reason = "High congestion detected"
    elif congestion == "MEDIUM_CONGESTION":
        seconds = MEDIUM_GREEN_SECONDS
        severity = MEDIUM
        reason = "Medium congestion detected"
    else:
        seconds = NORMAL_GREEN_SECONDS
        severity = NORMAL
        reason = "Low congestion detected"

    return SignalTimingRecommendation(
        recommended_green_seconds=clamp_green_time(seconds),
        min_green_seconds=MIN_GREEN_SECONDS,
        max_green_seconds=MAX_GREEN_SECONDS,
        priority_action=priority_action,
        severity=severity,
        target_lane=DEFAULT_TARGET_LANE,
        reason=reason,
        confidence_note=CONFIDENCE_NOTE,
    )


def generate_signal_timing_recommendation(
    density_result: dict[str, Any] | None,
    congestion_result: dict[str, Any] | None,
    priority_result: dict[str, Any] | None,
) -> dict[str, int | str]:
    """Generate a safe rule-based signal timing recommendation.

    Malformed or incomplete inputs fall back to normal operation instead of
    raising exceptions. This keeps dashboard and demo flows resilient.
    """

    try:
        density = density_result if isinstance(density_result, dict) else {}
        congestion_data = congestion_result if isinstance(congestion_result, dict) else {}
        priority = priority_result if isinstance(priority_result, dict) else {}

        congestion = _read_congestion(density, congestion_data)
        priority_action = _read_priority_action(priority, congestion)
        emergency_present = _is_emergency(priority, priority_action)
        recommendation = _build_recommendation(congestion, priority_action, emergency_present)
        logger.info(
            "Generated signal timing recommendation: %s seconds, action=%s, severity=%s",
            recommendation.recommended_green_seconds,
            recommendation.priority_action,
            recommendation.severity,
        )
        return asdict(recommendation)
    except Exception as error:  # Defensive fallback; public API should not crash dashboard use.
        logger.warning("Signal timing recommendation fell back to normal operation: %s", error)
        return asdict(
            SignalTimingRecommendation(
                recommended_green_seconds=clamp_green_time(NORMAL_GREEN_SECONDS),
                min_green_seconds=MIN_GREEN_SECONDS,
                max_green_seconds=MAX_GREEN_SECONDS,
                priority_action=NORMAL_OPERATION,
                severity=NORMAL,
                target_lane=DEFAULT_TARGET_LANE,
                reason="Fallback normal timing due to malformed input",
                confidence_note=CONFIDENCE_NOTE,
            )
        )


def build_signal_timing_log_record(
    signal_timing_result: dict[str, Any],
    congestion: str = "",
    timestamp: str | None = None,
) -> SignalTimingLogRecord:
    """Build one signal timing CSV log record."""

    return SignalTimingLogRecord(
        timestamp=timestamp or datetime.now().isoformat(timespec="seconds"),
        congestion=_safe_text(congestion, "LOW_CONGESTION"),
        priority_action=_safe_text(signal_timing_result.get("priority_action"), NORMAL_OPERATION),
        recommended_green_seconds=clamp_green_time(
            _safe_int(signal_timing_result.get("recommended_green_seconds"), NORMAL_GREEN_SECONDS)
        ),
    )


def write_signal_timing_log(
    records: Iterable[SignalTimingLogRecord],
    log_path: str | Path = DEFAULT_LOG_PATH,
) -> None:
    """Write signal timing recommendation records to CSV."""

    path = Path(log_path)
    logger.info("Writing signal timing log to: %s", path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=SIGNAL_TIMING_LOG_COLUMNS)
            writer.writeheader()
            for record in records:
                writer.writerow(asdict(record))
    except Exception as error:
        logger.error("Failed to write signal timing log to %s: %s", path, error)
        raise
