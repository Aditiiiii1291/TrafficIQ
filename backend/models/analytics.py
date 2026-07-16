"""SQLAlchemy model for aggregated traffic run analytics."""

from sqlalchemy import Column, Integer, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from backend.database.database import Base

class AnalyticsSummary(Base):
    __tablename__ = "analytics_summaries"

    id = Column(Integer, primary_key=True, index=True)
    processing_id = Column(Integer, ForeignKey("processing_results.id", ondelete="CASCADE"), nullable=False)
    vehicle_count = Column(Integer, default=0, nullable=False)
    emergency_count = Column(Integer, default=0, nullable=False)
    lane_statistics = Column(JSON, nullable=True)  # Stores lane-specific stats list/dict
    congestion_score = Column(Float, default=0.0, nullable=False)

    processing = relationship("ProcessingResult", back_populates="analytics_summaries")
