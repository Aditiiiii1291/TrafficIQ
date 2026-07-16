"""FastAPI router for video file uploads."""

import shutil
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from backend.core.config import UPLOAD_DIR
from backend.core.logger import logger
from backend.schemas.schemas import UploadResponse

router = APIRouter(prefix="/upload", tags=["Upload"])

SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file to the server for analysis."""
    filename = Path(file.filename).name
    file_extension = Path(filename).suffix.lower()
    
    if file_extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        logger.error(f"Upload failed: Unsupported file extension {file_extension}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format. Use one of: {supported}"
        )
        
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination_path = UPLOAD_DIR / filename
    
    logger.info(f"Saving uploaded file: {filename} to {destination_path}")
    try:
        with destination_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as error:
        logger.error(f"Failed to write uploaded file to disk: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {error}"
        )
        
    # Get file size
    size_bytes = destination_path.stat().st_size
    
    return UploadResponse(
        filename=filename,
        file_path=str(destination_path.resolve()),
        size_bytes=size_bytes
    )
