from __future__ import annotations

import csv
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from ml.detectors.ambulance_detector import (
    detect_emergency_lights,
    evaluate_ambulance_confidence,
    detect_ambulances,
    summarize_ambulance_detection,
    build_ambulance_detection_log_record,
    write_ambulance_detection_log,
    AmbulanceDetections,
    AmbulanceDetectionLogRecord,
)

# 1. Invalid frame handling
def test_invalid_frame_handling() -> None:
    # None frame
    res_none = detect_emergency_lights(None)
    assert res_none["red_regions"] == 0
    assert res_none["blue_regions"] == 0
    assert res_none["emergency_light_score"] == 0.0

    # Frame with zero size
    empty_frame = np.zeros((0, 0, 3), dtype=np.uint8)
    res_empty = detect_emergency_lights(empty_frame)
    assert res_empty["red_regions"] == 0
    assert res_empty["blue_regions"] == 0
    assert res_empty["emergency_light_score"] == 0.0


# 2. Emergency lights detected
def test_emergency_lights_detected() -> None:
    # Create a dummy image (100x100)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Paint red region (BGR: Red is [0, 0, 255])
    # In HSV, Red is H ~ 0 or 180, S ~ 255, V ~ 255
    frame[10:20, 10:20] = [0, 0, 255]
    
    # Paint blue region (BGR: Blue is [255, 0, 0])
    # In HSV, Blue is H ~ 120, S ~ 255, V ~ 255
    frame[50:60, 50:60] = [255, 0, 0]

    res = detect_emergency_lights(frame)
    assert res["red_regions"] > 0
    assert res["blue_regions"] > 0
    assert res["emergency_light_score"] > 0.5


# 3. Confidence calculation
def test_confidence_calculation() -> None:
    # High confidence scenario (van class + lights)
    res_high = evaluate_ambulance_confidence(
        vehicle_confidence=0.85,
        emergency_light_score=0.9,
        visual_heuristic_score=0.8,
    )
    assert res_high["ambulance_detected"] is True
    assert res_high["confidence"] > 0.6
    assert any("Ambulance verified" in r for r in res_high["reason"])

    # Low confidence scenario (normal car + no lights)
    res_low = evaluate_ambulance_confidence(
        vehicle_confidence=0.4,
        emergency_light_score=0.0,
        visual_heuristic_score=0.1,
    )
    assert res_low["ambulance_detected"] is False
    assert res_low["confidence"] < 0.4
    assert any("Not an ambulance" in r for r in res_low["reason"])


# 4. Empty detections
@patch("ml.detectors.ambulance_detector.load_yolo_model")
def test_empty_detections(mock_load_yolo) -> None:
    mock_model = MagicMock()
    mock_load_yolo.return_value = mock_model
    
    # Mock predict to return no boxes
    mock_result = MagicMock()
    mock_result.boxes = []
    mock_model.predict.return_value = [mock_result]
    
    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    
    annotated, detections = detect_ambulances(dummy_frame, model=mock_model)
    
    assert len(detections) == 0
    assert isinstance(detections, AmbulanceDetections)
    assert detections.frame_summary["ambulance_detected"] is False
    assert detections.frame_summary["confidence"] == 0.0


# 5. Output schema validation
@patch("ml.detectors.ambulance_detector.load_yolo_model")
def test_output_schema_validation(mock_load_yolo) -> None:
    mock_model = MagicMock()
    mock_load_yolo.return_value = mock_model
    
    # Mock predict to return a vehicle candidate (car)
    mock_box = MagicMock()
    mock_box.cls = [2] # class index 2 (car)
    mock_box.conf = [0.8]
    mock_box.xyxy = [[10.0, 20.0, 30.0, 40.0]]
    
    mock_result = MagicMock()
    mock_result.boxes = [mock_box]
    mock_model.predict.return_value = [mock_result]
    mock_model.names = {2: "car"}

    # Paint red/blue lights on the frame in the bbox region to trigger detection
    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    dummy_frame[20:30, 15:25] = [0, 0, 255] # Red
    dummy_frame[30:40, 15:25] = [255, 0, 0] # Blue

    annotated, detections = detect_ambulances(dummy_frame, model=mock_model)
    
    assert isinstance(detections, AmbulanceDetections)
    assert hasattr(detections, "frame_summary")
    
    summary = detections.frame_summary
    assert "ambulance_detected" in summary
    assert "confidence" in summary
    assert "emergency_light_score" in summary
    assert "reason" in summary
    
    if len(detections) > 0:
        det = detections[0]
        assert "class_name" in det
        assert "confidence" in det
        assert "bbox" in det
        assert "emergency_light_score" in det
        assert "reason" in det


# 6. Logging behavior
def test_logging_behavior(tmp_path) -> None:
    log_file = tmp_path / "test_ambulance_log.csv"
    
    # Write a test record
    record = AmbulanceDetectionLogRecord(
        timestamp="2026-06-10T12:00:00",
        ambulance_detected=True,
        confidence=0.8543,
        emergency_light_score=0.75,
        reason="Test reason 1; Test reason 2",
    )
    
    success = write_ambulance_detection_log(record, log_path=log_file)
    assert success is True
    assert log_file.exists()
    
    # Read the written file and verify fields
    with open(log_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 1
    assert rows[0]["timestamp"] == "2026-06-10T12:00:00"
    assert rows[0]["ambulance_detected"] == "True"
    assert float(rows[0]["confidence"]) == 0.8543
    assert float(rows[0]["emergency_light_score"]) == 0.75
    assert rows[0]["reason"] == "Test reason 1; Test reason 2"

    # Test that invalid path fails gracefully and doesn't raise exception
    invalid_path = Path("invalid_dir_?/log.csv")
    success_invalid = write_ambulance_detection_log(record, log_path=invalid_path)
    assert success_invalid is False # Safe fail
