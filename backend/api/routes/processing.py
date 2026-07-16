"""FastAPI router for video processing engine."""

import base64
import cv2
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from backend.core.config import UPLOAD_DIR
from backend.core.logger import logger
from backend.services.video_processor import analyze_video
from backend.schemas.schemas import ProcessRequest, ProcessingResult

router = APIRouter(prefix="/process", tags=["Processing"])

@router.post("", response_model=ProcessingResult)
async def process_video(request: ProcessRequest):
    """Analyze an uploaded video and return traffic flow, congestion, and priority recommendations."""
    video_path = UPLOAD_DIR / request.video_name
    
    if not video_path.exists():
        logger.error(f"Processing failed: Video file not found at {video_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video file '{request.video_name}' not found. Upload it first."
        )
        
    logger.info(f"Starting analysis on video: {request.video_name} (max_frames={request.max_frames})")
    try:
        results = analyze_video(
            video_path=video_path,
            max_frames=request.max_frames,
            skip_frames=request.skip_frames,
            vehicle_confidence=request.vehicle_confidence,
            ambulance_confidence=request.ambulance_confidence
        )
        
        # Base64 encode the latest frame if it exists
        latest_frame_b64 = None
        latest_frame = results.get("latest_frame")
        if latest_frame is not None:
            try:
                # convert RGB back to BGR for cv2 encoding
                latest_frame_bgr = cv2.cvtColor(latest_frame, cv2.COLOR_RGB2BGR)
                _, buffer = cv2.imencode(".jpg", latest_frame_bgr)
                latest_frame_b64 = base64.b64encode(buffer).decode("utf-8")
            except Exception as encode_error:
                logger.warning(f"Could not base64 encode latest frame: {encode_error}")
        
        # Make a copy of results to return
        response_data = dict(results)
        
        # Remove numpy arrays and non-serializable objects from output
        response_data.pop("latest_frame", None)
        response_data["latest_frame_b64"] = latest_frame_b64
        response_data["processed_video_location"] = str(video_path)
        
        return response_data
        
    except Exception as error:
        logger.error(f"Failed to process video: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video processing failed: {error}"
        )
