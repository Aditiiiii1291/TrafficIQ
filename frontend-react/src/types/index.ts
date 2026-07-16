export interface UploadResponse {
  filename: string;
  file_path: string;
  size_bytes: number;
}

export interface ProcessRequest {
  video_name: string;
  max_frames: number;
  skip_frames: number;
  vehicle_confidence: number;
  ambulance_confidence: number;
}

export interface LaneResult {
  lane_id: number;
  lane_name: string;
  total_vehicles: number;
  car_count: number;
  motorcycle_count: number;
  bus_count: number;
  truck_count: number;
  emergency_present: boolean;
  density: string;
  congestion: string;
  recommended_action: string;
  recommended_green_seconds: number;
}

export interface GreenCorridorSequenceItem {
  lane_id: number;
  lane_name: string;
  action: string;
  duration_seconds: number;
}

export interface GreenCorridorResult {
  corridor_active: boolean;
  emergency_lane_id: string;
  emergency_lane_name: string;
  corridor_status: string;
  recommended_sequence: GreenCorridorSequenceItem[];
  estimated_clearance_window_seconds: number;
  reason: string;
  confidence_note: string;
}

export interface ProcessingResult {
  total_vehicles: number;
  car_count: number;
  motorcycle_count: number;
  bus_count: number;
  truck_count: number;
  density: string;
  congestion: string;
  predicted_congestion: string;
  emergency_present: boolean;
  recommended_action: string;
  recommended_green_seconds: number;
  signal_priority_action: string;
  signal_severity: string;
  signal_reason: string;
  signal_confidence_note: string;
  lane_results: LaneResult[];
  green_corridor_result: GreenCorridorResult;
  processed_frames: number;
  ambulance_message: string;
  ambulance_detected: boolean;
  ambulance_confidence: number;
  emergency_light_score: number;
  ambulance_reason: string;
  processed_video_location?: string;
  latest_frame_b64?: string;
  timestamp?: string;
}

export interface TrafficStats {
  total_analyzed_records: number;
  total_emergency_events: number;
  most_common_congestion_level: string;
  most_common_recommendation: string;
}

export interface VehicleTrendItem {
  timestamp: string;
  total_vehicles: number;
}

export interface TrendData {
  vehicle_count_over_time: VehicleTrendItem[];
  density_distribution: Record<string, number>;
  congestion_distribution: Record<string, number>;
  recommendation_distribution: Record<string, number>;
}

export interface EventStats {
  total_emergency_events: number;
  emergency_rate: string;
}

export interface AnalyticsResponse {
  summary: TrafficStats;
  trends: TrendData;
  event_statistics: EventStats;
}

export interface HistoricalRecordModel {
  timestamp: string;
  total_vehicles: number;
  density: string;
  congestion: string;
  emergency_present: boolean;
  recommended_action: string;
}

export interface HistoryResponse {
  records: HistoricalRecordModel[];
  total_records: number;
}
