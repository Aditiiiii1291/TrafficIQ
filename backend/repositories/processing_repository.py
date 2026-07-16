"""Repository class for ProcessingResult and VehicleDetection CRUD operations."""

from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from backend.models.processing import ProcessingResult
from backend.models.detection import VehicleDetection

class ProcessingRepository:
    """Manages database operations for processing runs and detection records."""

    @staticmethod
    def create_processing_result(
        db: Session,
        video_id: int,
        emergency_detected: bool,
        congestion_level: str,
        signal_recommendation: str
    ) -> ProcessingResult:
        """Create a new processing run result entry."""
        result = ProcessingResult(
            video_id=video_id,
            emergency_detected=emergency_detected,
            congestion_level=congestion_level,
            signal_recommendation=signal_recommendation
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result

    @staticmethod
    def create_detections(db: Session, processing_id: int, detections: list[dict]) -> None:
        """Bulk save vehicle detection records for a processing run."""
        db_detections = [
            VehicleDetection(
                processing_id=processing_id,
                class_name=det.get("class_name", "car"),
                confidence=float(det.get("confidence", 0.0)),
                frame_number=int(det.get("frame_index", 0)),
                timestamp=str(det.get("timestamp", ""))
            )
            for det in detections
        ]
        db.bulk_save_objects(db_detections)
        db.commit()

    @staticmethod
    def get_processing_result(db: Session, result_id: int) -> ProcessingResult | None:
        """Retrieve a processing result entry by ID."""
        return db.query(ProcessingResult).filter(ProcessingResult.id == result_id).first()

    @staticmethod
    def get_all_processing_results(
        db: Session,
        date_filter: str | None = None,
        congestion_level: str = "ALL",
        recommendation: str = "ALL"
    ) -> list[ProcessingResult]:
        """Query and filter historical processing runs."""
        query = db.query(ProcessingResult)
        
        if congestion_level != "ALL":
            query = query.filter(ProcessingResult.congestion_level == congestion_level)
            
        if recommendation != "ALL":
            query = query.filter(ProcessingResult.signal_recommendation == recommendation)
            
        results = query.all()
        
        # Apply date prefix filter locally for max compatibility across SQLite & Postgres cast conversions
        if date_filter:
            results = [
                res for res in results 
                if res.created_at.isoformat().startswith(date_filter) 
                or str(res.created_at).startswith(date_filter)
            ]
            
        return results
