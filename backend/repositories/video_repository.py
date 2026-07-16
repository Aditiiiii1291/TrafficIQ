"""Repository class for Video model CRUD operations."""

from sqlalchemy.orm import Session
from backend.models.video import Video

class VideoRepository:
    """Manages database operations for the Video table."""

    @staticmethod
    def create_video(db: Session, filename: str) -> Video:
        """Create a new video log entry."""
        video = Video(filename=filename, status="uploaded")
        db.add(video)
        db.commit()
        db.refresh(video)
        return video

    @staticmethod
    def get_video(db: Session, video_id: int) -> Video | None:
        """Retrieve a video entry by ID."""
        return db.query(Video).filter(Video.id == video_id).first()

    @staticmethod
    def get_video_by_filename(db: Session, filename: str) -> Video | None:
        """Retrieve a video entry by filename."""
        return db.query(Video).filter(Video.filename == filename).first()

    @staticmethod
    def update_video_status(
        db: Session,
        video_id: int,
        status: str,
        duration: float | None = None,
        processing_time: float | None = None
    ) -> Video | None:
        """Update the processing status and performance metrics of a video."""
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.status = status
            if duration is not None:
                video.duration = duration
            if processing_time is not None:
                video.processing_time = processing_time
            db.commit()
            db.refresh(video)
        return video
