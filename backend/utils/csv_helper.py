"""CSV helper utilities for TrafficIQ."""

import csv
from pathlib import Path
from typing import Any, Iterable
from backend.core.logger import logger

def append_rows_to_csv(file_path: str | Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    """Safely append rows to a CSV file. Creates the header if the file does not exist."""
    if not rows:
        return
        
    path = Path(file_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = path.exists()
        
        with path.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows)
    except Exception as error:
        logger.error(f"Failed to write rows to CSV at {path}: {error}")
        raise error
