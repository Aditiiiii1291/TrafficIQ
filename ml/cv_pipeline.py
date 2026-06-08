"""Phase 2 OpenCV video processing foundation.

This module intentionally does not include YOLO or ML logic yet. It handles
video loading, frame iteration, basic frame annotation, optional frame export,
preview display, and annotated output video writing.
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import BinaryIO, Iterator

import cv2


SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VideoMetadata:
    """Basic metadata reported by OpenCV for a video file."""

    source_path: str
    fps: float
    frame_count: int
    width: int
    height: int
    duration_seconds: float


@dataclass(frozen=True)
class ProcessingSummary:
    """Summary returned after a video has been processed."""

    input_path: str
    output_path: str
    frames_dir: str | None
    source_fps: float
    total_frames: int
    processed_frames: int
    saved_frames: int
    width: int
    height: int


def validate_video_path(video_path: str | Path) -> Path:
    """Validate that a local video path exists and has a supported extension."""

    path = Path(video_path)
    if not path.exists():
        logger.error(f"Video file not found: {path}")
        raise FileNotFoundError(f"Video file not found: {path}")
    if not path.is_file():
        logger.error(f"Video path is not a file: {path}")
        raise ValueError(f"Video path is not a file: {path}")
    if path.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_VIDEO_EXTENSIONS))
        logger.error(f"Unsupported video format '{path.suffix}'. Use one of: {supported}")
        raise ValueError(f"Unsupported video format '{path.suffix}'. Use one of: {supported}")
    return path


def save_uploaded_video(uploaded_file: BinaryIO, destination_dir: str | Path) -> Path:
    """Save a Streamlit-style uploaded video file to disk for OpenCV processing."""

    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)

    filename = Path(getattr(uploaded_file, "name", "uploaded_video.mp4")).name
    output_path = destination / filename

    logger.info(f"Saving uploaded video stream to: {output_path}")
    try:
        with output_path.open("wb") as file:
            file.write(uploaded_file.read())
    except Exception as error:
        logger.error(f"Failed to write uploaded video file to {output_path}: {error}")
        raise

    return output_path


def open_video_capture(video_path: str | Path) -> cv2.VideoCapture:
    """Open a validated video file with OpenCV."""

    path = validate_video_path(video_path)
    logger.info(f"Opening video capture for: {path}")
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        logger.error(f"OpenCV could not open video: {path}")
        raise RuntimeError(f"OpenCV could not open video: {path}")
    return capture


def get_video_metadata(video_path: str | Path) -> VideoMetadata:
    """Read FPS, dimensions, frame count, and duration from a video."""

    path = validate_video_path(video_path)
    capture = open_video_capture(path)

    try:
        fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        duration_seconds = frame_count / fps if fps > 0 else 0.0

        metadata = VideoMetadata(
            source_path=str(path),
            fps=fps,
            frame_count=frame_count,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
        )
        logger.info(f"Video metadata read successfully: {fps} FPS, {frame_count} frames, {width}x{height}")
        return metadata
    except Exception as error:
        logger.error(f"Failed to retrieve video metadata for {path}: {error}")
        raise
    finally:
        capture.release()


def iter_frames(video_path: str | Path) -> Iterator[tuple[int, object]]:
    """Yield frame index and frame arrays from a video file."""

    capture = open_video_capture(video_path)
    frame_index = 0

    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            yield frame_index, frame
            frame_index += 1
    finally:
        capture.release()
        logger.info(f"Released video capture for: {video_path}")


def annotate_frame(frame: object, frame_index: int, fps: float, total_frames: int) -> object:
    """Add simple Phase 2 diagnostics to a frame."""

    annotated = frame.copy()
    timestamp_seconds = frame_index / fps if fps > 0 else 0.0

    lines = [
        f"Frame: {frame_index + 1}/{total_frames if total_frames else '?'}",
        f"FPS: {fps:.2f}",
        f"Time: {timestamp_seconds:.2f}s",
    ]

    x, y = 16, 32
    for line in lines:
        cv2.putText(
            annotated,
            line,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            annotated,
            line,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (20, 20, 20),
            1,
            cv2.LINE_AA,
        )
        y += 28

    return annotated


def process_video(
    input_path: str | Path,
    output_path: str | Path = "data/processed/annotated_output.mp4",
    frames_dir: str | Path | None = None,
    display: bool = False,
    frame_step: int = 1,
    max_frames: int | None = None,
) -> ProcessingSummary:
    """Process a video and save an annotated output video.

    Args:
        input_path: Local source video path.
        output_path: Path where the annotated video should be written.
        frames_dir: Optional directory for exported annotated JPG frames.
        display: Show each processed frame with cv2.imshow.
        frame_step: Process every Nth frame. Use 1 for every frame.
        max_frames: Optional cap for quick test runs.
    """

    if frame_step < 1:
        raise ValueError("frame_step must be 1 or greater")
    if max_frames is not None and max_frames < 1:
        raise ValueError("max_frames must be None or 1 or greater")

    logger.info(f"Starting video processing: {input_path} -> {output_path}")
    metadata = get_video_metadata(input_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    frame_export_dir = Path(frames_dir) if frames_dir is not None else None
    if frame_export_dir is not None:
        frame_export_dir.mkdir(parents=True, exist_ok=True)

    source_fps = metadata.fps if metadata.fps > 0 else 30.0
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        source_fps,
        (metadata.width, metadata.height),
    )
    if not writer.isOpened():
        logger.error(f"OpenCV could not create output video: {output}")
        raise RuntimeError(f"OpenCV could not create output video: {output}")

    processed_frames = 0
    saved_frames = 0

    try:
        for frame_index, frame in iter_frames(input_path):
            if frame_index % frame_step != 0:
                continue
            if max_frames is not None and processed_frames >= max_frames:
                break

            annotated = annotate_frame(frame, frame_index, metadata.fps, metadata.frame_count)
            writer.write(annotated)
            processed_frames += 1

            if frame_export_dir is not None:
                frame_path = frame_export_dir / f"frame_{frame_index + 1:06d}.jpg"
                cv2.imwrite(str(frame_path), annotated)
                saved_frames += 1

            if display:
                cv2.imshow("Processed Frame", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        writer.release()
        if display:
            cv2.destroyAllWindows()

    return ProcessingSummary(
        input_path=str(validate_video_path(input_path)),
        output_path=str(output),
        frames_dir=str(frame_export_dir) if frame_export_dir is not None else None,
        source_fps=metadata.fps,
        total_frames=metadata.frame_count,
        processed_frames=processed_frames,
        saved_frames=saved_frames,
        width=metadata.width,
        height=metadata.height,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the command-line interface for local Phase 2 testing."""

    parser = argparse.ArgumentParser(description="Process a video with the Phase 2 OpenCV pipeline.")
    parser.add_argument("--input", required=True, help="Path to the source video file.")
    parser.add_argument(
        "--output",
        default="data/processed/annotated_output.mp4",
        help="Path where the annotated output video will be saved.",
    )
    parser.add_argument(
        "--frames-dir",
        default=None,
        help="Optional directory where annotated frames will be exported as JPG files.",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Display processed frames in an OpenCV window. Press q to stop.",
    )
    parser.add_argument(
        "--frame-step",
        type=int,
        default=1,
        help="Process every Nth frame. Use 1 to process every frame.",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Optional maximum number of frames to process for quick tests.",
    )
    return parser


def main() -> None:
    """Run the pipeline from the command line."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    args = build_arg_parser().parse_args()
    summary = process_video(
        input_path=args.input,
        output_path=args.output,
        frames_dir=args.frames_dir,
        display=args.display,
        frame_step=args.frame_step,
        max_frames=args.max_frames,
    )

    print("Phase 2 OpenCV processing complete")
    for key, value in asdict(summary).items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
