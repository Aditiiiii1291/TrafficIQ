"""Phase 6 congestion classification.

This module consumes Phase 5 density results and maps them to congestion
levels. It does not implement machine learning prediction, dashboard logic, or
emergency priority decisions.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import cv2


CONGESTION_RULES = {
    "LOW": "LOW_CONGESTION",
    "MEDIUM": "MEDIUM_CONGESTION",
    "HIGH": "HIGH_CONGESTION",
}

CONGESTION_COLORS = {
    "LOW_CONGESTION": (80, 180, 80),
    "MEDIUM_CONGESTION": (40, 180, 255),
    "HIGH_CONGESTION": (40, 40, 255),
}

CONGESTION_LOG_COLUMNS = [
    "timestamp",
    "total_vehicles",
    "density",
    "congestion",
]


@dataclass(frozen=True)
class CongestionLogRecord:
    """CSV-compatible congestion log record."""

    timestamp: str
    total_vehicles: int
    density: str
    congestion: str


def normalize_density(density: str) -> str:
    """Normalize density labels before applying congestion rules."""

    normalized = str(density).strip().upper()
    if normalized not in CONGESTION_RULES:
        allowed = ", ".join(CONGESTION_RULES)
        raise ValueError(f"Unsupported density '{density}'. Expected one of: {allowed}")
    return normalized


def classify_congestion(density_result: dict[str, Any]) -> dict[str, int | str]:
    """Classify congestion from a Phase 5 density result."""

    total_vehicles = int(density_result.get("total_vehicles", 0))
    density = normalize_density(str(density_result.get("density", "")))

    return {
        "total_vehicles": total_vehicles,
        "density": density,
        "congestion": CONGESTION_RULES[density],
    }


def draw_congestion_overlay(
    frame: Any,
    congestion_result: dict[str, int | str],
    position: tuple[int, int] = (16, 244),
) -> Any:
    """Draw congestion status on an annotated frame."""

    annotated = frame.copy()
    congestion = str(congestion_result["congestion"])
    color = CONGESTION_COLORS.get(congestion, (255, 255, 255))
    x, y = position
    label = f"Congestion: {congestion}"

    cv2.rectangle(annotated, (x, y), (x + 465, y + 44), color, -1)
    cv2.putText(
        annotated,
        label,
        (x + 12, y + 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    return annotated


def build_congestion_log_record(
    congestion_result: dict[str, int | str],
    timestamp: str | None = None,
) -> CongestionLogRecord:
    """Build one congestion log record from a congestion result."""

    return CongestionLogRecord(
        timestamp=timestamp or datetime.now().isoformat(timespec="seconds"),
        total_vehicles=int(congestion_result["total_vehicles"]),
        density=str(congestion_result["density"]),
        congestion=str(congestion_result["congestion"]),
    )


def write_congestion_log(log_path: str | Path, records: Iterable[CongestionLogRecord]) -> None:
    """Write congestion analysis records to CSV."""

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CONGESTION_LOG_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def read_density_log(log_path: str | Path) -> list[dict[str, str]]:
    """Read Phase 5 density CSV records."""

    with Path(log_path).open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def classify_congestion_from_density_log(
    density_log_path: str | Path,
    output_log_path: str | Path = "data/logs/congestion_analysis.csv",
) -> list[CongestionLogRecord]:
    """Create congestion records from a Phase 5 density analysis CSV."""

    density_rows = read_density_log(density_log_path)
    congestion_records: list[CongestionLogRecord] = []

    for row in density_rows:
        congestion_result = classify_congestion(
            {
                "total_vehicles": row.get("total_vehicles", 0),
                "density": row.get("density", ""),
            }
        )
        timestamp = row.get("timestamp_seconds") or row.get("timestamp") or None
        congestion_records.append(
            build_congestion_log_record(
                congestion_result=congestion_result,
                timestamp=str(timestamp) if timestamp is not None else None,
            )
        )

    write_congestion_log(output_log_path, congestion_records)
    return congestion_records


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for Phase 6 congestion classification."""

    parser = argparse.ArgumentParser(description="Classify congestion from a density CSV log.")
    parser.add_argument(
        "--density-log",
        required=True,
        help="Path to a Phase 5 density analysis CSV log.",
    )
    parser.add_argument(
        "--output-log",
        default="data/logs/congestion_analysis.csv",
        help="Path where the congestion analysis CSV log will be saved.",
    )
    return parser


def main() -> None:
    """Run congestion classification from a density CSV log."""

    args = build_arg_parser().parse_args()
    records = classify_congestion_from_density_log(
        density_log_path=args.density_log,
        output_log_path=args.output_log,
    )

    print("Phase 6 congestion classification complete")
    print(f"records_written: {len(records)}")
    print(f"output_log: {args.output_log}")


if __name__ == "__main__":
    main()
