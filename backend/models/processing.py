"""SQLAlchemy model for processing runs results."""

import datetime
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.database.database import Base

class ProcessingResult(Base):
    __tablename__ = "processing_results"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    emergency_detected = Column(Boolean, default=False, nullable=False)
    congestion_level = Column(String, nullable=False)
    signal_recommendation = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    video = relationship("Video", back_populates="processing_results")
    detections = relationship("VehicleDetection", back_populates="processing", cascade="all, delete-orphan")
    analytics_summaries = relationship("AnalyticsSummary", back_populates="processing", cascade="all, delete-orphan")
