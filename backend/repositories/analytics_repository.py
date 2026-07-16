"""Repository class for AnalyticsSummary CRUD operations."""

from sqlalchemy.orm import Session
from backend.models.analytics import AnalyticsSummary

class AnalyticsRepository:
    """Manages database operations for traffic analytics summaries."""

    @staticmethod
    def create_analytics_summary(
        db: Session,
        processing_id: int,
        vehicle_count: int,
        emergency_count: int,
        lane_statistics: list | dict | None = None,
        congestion_score: float = 0.0
    ) -> AnalyticsSummary:
        """Create a new analytics summary entry."""
        summary = AnalyticsSummary(
            processing_id=processing_id,
            vehicle_count=vehicle_count,
            emergency_count=emergency_count,
            lane_statistics=lane_statistics,
            congestion_score=congestion_score
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary

    @staticmethod
    def get_analytics_summaries(db: Session) -> list[AnalyticsSummary]:
        """Retrieve all analytics summaries."""
        return db.query(AnalyticsSummary).all()
