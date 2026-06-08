from __future__ import annotations

import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from ml.detectors.vehicle_detector import (
    load_yolo_model,
    should_process_frame,
    _extract_detections,
)
from ml.detectors.ambulance_detector import (
    resolve_ambulance_model_path,
    load_ambulance_model,
    get_ambulance_class_ids,
    is_emergency_present,
    _normalize_bbox,
)


def test_should_process_frame() -> None:
    # skip_frames = 0 means process every frame
    assert should_process_frame(0, 0) is True
    assert should_process_frame(1, 0) is True
    
    # skip_frames = 2 means process 0, 3, 6, 9... (skipping 2 frames: 1 and 2)
    assert should_process_frame(0, 2) is True
    assert should_process_frame(1, 2) is False
    assert should_process_frame(2, 2) is False
    assert should_process_frame(3, 2) is True


def test_resolve_ambulance_model_path() -> None:
    # 1. Given explicit model path
    assert resolve_ambulance_model_path("custom.pt") == Path("custom.pt")
    
    # 2. Env var fallback
    with patch.dict(os.environ, {"AMBULANCE_MODEL_PATH": "env_model.pt"}):
        assert resolve_ambulance_model_path() == Path("env_model.pt")
        
    # 3. Default path fallback
    if "AMBULANCE_MODEL_PATH" in os.environ:
        del os.environ["AMBULANCE_MODEL_PATH"]
    assert resolve_ambulance_model_path() == Path("data/models/ambulance_detector.pt")


@patch("ml.detectors.ambulance_detector.YOLO")
def test_load_ambulance_model_caching(mock_yolo) -> None:
    mock_model = MagicMock()
    mock_yolo.return_value = mock_model
    
    # Load model once
    model1 = load_ambulance_model("test_model.pt")
    # Load model twice with same path
    model2 = load_ambulance_model("test_model.pt")
    
    assert model1 is model2
    mock_yolo.assert_called_once_with("test_model.pt")


def test_get_ambulance_class_ids() -> None:
    mock_model = MagicMock()
    
    # Mock model names as dict
    mock_model.names = {
        0: "car",
        1: "ambulance",
        2: "truck",
        3: "emergency_vehicle"
    }
    assert get_ambulance_class_ids(mock_model) == [1, 3]

    # Mock model names as list
    mock_model.names = ["car", "ambulance", "truck", "emergency vehicle"]
    assert get_ambulance_class_ids(mock_model) == [1, 3]

    # Case insensitive check
    mock_model.names = ["Ambulance"]
    assert get_ambulance_class_ids(mock_model) == [0]


def test_is_emergency_present() -> None:
    assert is_emergency_present([]) is False
    assert is_emergency_present([{"class_name": "ambulance", "confidence": 0.9}]) is True


def test_normalize_bbox() -> None:
    mock_box = MagicMock()
    mock_xyxy = MagicMock()
    mock_xyxy.tolist.return_value = [10.5, 20.1, 100.9, 200.4]
    mock_box.xyxy = [mock_xyxy]
    assert _normalize_bbox(mock_box) == [10, 20, 100, 200]


def test_extract_detections() -> None:
    mock_cls1 = MagicMock()
    mock_cls1.item.return_value = 2
    mock_conf1 = MagicMock()
    mock_conf1.item.return_value = 0.85
    mock_xyxy1 = MagicMock()
    mock_xyxy1.tolist.return_value = [10.0, 20.0, 30.0, 40.0]
    
    mock_box1 = MagicMock()
    mock_box1.cls = [mock_cls1]
    mock_box1.conf = [mock_conf1]
    mock_box1.xyxy = [mock_xyxy1]
    
    mock_cls2 = MagicMock()
    mock_cls2.item.return_value = 0
    mock_conf2 = MagicMock()
    mock_conf2.item.return_value = 0.9
    mock_xyxy2 = MagicMock()
    mock_xyxy2.tolist.return_value = [50.0, 60.0, 70.0, 80.0]
    
    mock_box2 = MagicMock()
    mock_box2.cls = [mock_cls2]
    mock_box2.conf = [mock_conf2]
    mock_box2.xyxy = [mock_xyxy2]

    mock_result = MagicMock()
    mock_result.boxes = [mock_box1, mock_box2]

    detections = _extract_detections([mock_result], 0, 30.0, "video.mp4")
    
    assert len(detections) == 1
    assert detections[0].class_name == "car"
    assert detections[0].confidence == 0.85
    assert detections[0].xmin == 10
    assert detections[0].ymin == 20
    assert detections[0].xmax == 30
    assert detections[0].ymax == 40
