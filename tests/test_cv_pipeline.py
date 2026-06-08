from __future__ import annotations

import io
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from ml.cv_pipeline import (
    validate_video_path,
    save_uploaded_video,
    open_video_capture,
    get_video_metadata,
    iter_frames,
    process_video,
    VideoMetadata,
    ProcessingSummary,
)


def test_validate_video_path_checks_existence(tmp_path) -> None:
    non_existent = tmp_path / "does_not_exist.mp4"
    with pytest.raises(FileNotFoundError, match="Video file not found"):
        validate_video_path(non_existent)


def test_validate_video_path_checks_is_file(tmp_path) -> None:
    directory = tmp_path / "sub_dir"
    directory.mkdir()
    with pytest.raises(ValueError, match="Video path is not a file"):
        validate_video_path(directory)


def test_validate_video_path_checks_extension(tmp_path) -> None:
    bad_file = tmp_path / "test.txt"
    bad_file.write_text("dummy content")
    with pytest.raises(ValueError, match="Unsupported video format"):
        validate_video_path(bad_file)


def test_validate_video_path_success(tmp_path) -> None:
    good_file = tmp_path / "video.mp4"
    good_file.write_text("mock video stream")
    validated = validate_video_path(good_file)
    assert validated == good_file


def test_save_uploaded_video(tmp_path) -> None:
    mock_file = io.BytesIO(b"dummy video bytes")
    mock_file.name = "sample_traffic.avi"
    
    destination = tmp_path / "uploads"
    saved_path = save_uploaded_video(mock_file, destination)
    
    assert saved_path == destination / "sample_traffic.avi"
    assert saved_path.exists()
    assert saved_path.read_bytes() == b"dummy video bytes"


@patch("cv2.VideoCapture")
def test_open_video_capture_failure(mock_capture_class, tmp_path) -> None:
    video_file = tmp_path / "mock.mp4"
    video_file.write_text("video")
    
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_capture_class.return_value = mock_cap
    
    with pytest.raises(RuntimeError, match="OpenCV could not open video"):
        open_video_capture(video_file)


@patch("cv2.VideoCapture")
def test_get_video_metadata(mock_capture_class, tmp_path) -> None:
    video_file = tmp_path / "mock.mp4"
    video_file.write_text("video")
    
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.side_effect = lambda prop: {
        5: 30.0,    # CAP_PROP_FPS
        7: 120,    # CAP_PROP_FRAME_COUNT
        3: 1920,   # CAP_PROP_FRAME_WIDTH
        4: 1080,   # CAP_PROP_FRAME_HEIGHT
    }.get(prop, 0.0)
    mock_capture_class.return_value = mock_cap
    
    metadata = get_video_metadata(video_file)
    
    assert metadata.fps == 30.0
    assert metadata.frame_count == 120
    assert metadata.width == 1920
    assert metadata.height == 1080
    assert metadata.duration_seconds == 4.0
    mock_cap.release.assert_called_once()
