"""Pydantic schemas for TrafficIQ REST API."""

from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional

# Upload schemas
class UploadResponse(BaseModel):
    filename: str = Field(..., description="Name of the uploaded file")
    file_path: str = Field(..., description="Absolute file path on the server")
    size_bytes: int = Field(..., description="Size of the uploaded file in bytes")

# Process schemas
class ProcessRequest(BaseModel):
    video_name: str = Field(..., description="Name of the uploaded video file in raw folder")
    max_frames: int = Field(10, ge=1, le=500, description="Maximum frames to analyze")
    skip_frames: int = Field(2, ge=0, le=10, description="Frames to skip between analyses")
    vehicle_confidence: float = Field(0.35, ge=0.1, le=0.9, description="Confidence threshold for YOLO vehicle detector")
    ambulance_confidence: float = Field(0.35, ge=0.1, le=0.9, description="Confidence threshold for custom ambulance detector")

class LaneResult(BaseModel):
    lane_id: int
    lane_name: str
    total_vehicles: int
    car_count: int
    motorcycle_count: int
    bus_count: int
    truck_count: int
    emergency_present: bool
    lane_utilization_percent: float
    density: str
    congestion: str
    recommended_action: str
    recommended_green_seconds: int

class GreenCorridorSequenceItem(BaseModel):
    lane_id: int
    lane_name: str
    action: str
    green_seconds: int
    reason: str

class GreenCorridorResult(BaseModel):
    corridor_active: bool
    emergency_lane_id: str
    emergency_lane_name: str
    corridor_status: str
    recommended_sequence: List[GreenCorridorSequenceItem]
    estimated_clearance_window_seconds: int
    reason: str
    confidence_note: str

class ProcessingResult(BaseModel):
    total_vehicles: int
    car_count: int
    motorcycle_count: int
    bus_count: int
    truck_count: int
    density: str
    congestion: str
    predicted_congestion: str
    emergency_present: bool
    recommended_action: str
    recommended_green_seconds: int
    signal_priority_action: str
    signal_severity: str
    signal_reason: str
    signal_confidence_note: str
    lane_results: List[LaneResult]
    green_corridor_result: GreenCorridorResult
    processed_frames: int
    ambulance_message: str
    ambulance_detected: bool
    ambulance_confidence: float
    emergency_light_score: float
    ambulance_reason: str
    processed_video_location: Optional[str] = None
    latest_frame_b64: Optional[str] = None
    timestamp: Optional[str] = None

# Analytics schemas
class TrafficStats(BaseModel):
    total_analyzed_records: int
    total_emergency_events: int
    most_common_congestion_level: str
    most_common_recommendation: str

class TrendData(BaseModel):
    vehicle_count_over_time: List[Dict[str, Any]]
    density_distribution: Dict[str, int]
    congestion_distribution: Dict[str, int]
    recommendation_distribution: Dict[str, int]

class EventStats(BaseModel):
    total_emergency_events: int
    emergency_rate: str

class AnalyticsResponse(BaseModel):
    summary: TrafficStats
    trends: TrendData
    event_statistics: EventStats

# History schemas
class HistoricalRecordModel(BaseModel):
    timestamp: str
    total_vehicles: int
    density: str
    congestion: str
    emergency_present: bool
    recommended_action: str

class HistoryResponse(BaseModel):
    records: List[HistoricalRecordModel]
    total_records: int
