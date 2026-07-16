"""SQLAlchemy model for vehicle detection records."""

from sqlalchemy import Column, Integer, ForeignKey, String, Float
from sqlalchemy.orm import relationship
from backend.database.database import Base

class VehicleDetection(Base):
    __tablename__ = "vehicle_detections"

    id = Column(Integer, primary_key=True, index=True)
    processing_id = Column(Integer, ForeignKey("processing_results.id", ondelete="CASCADE"), nullable=False)
    class_name = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(String, nullable=False)  # ISO string matching logging formats

    processing = relationship("ProcessingResult", back_populates="detections")
