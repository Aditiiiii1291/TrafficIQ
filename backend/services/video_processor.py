"""Video processing service for TrafficIQ.

This service encapsulates all core computer vision, object detection, and 
analytics pipeline logic, decoupling the UI from execution.
"""

from datetime import datetime, timedelta
from dataclasses import asdict
from pathlib import Path
from typing import Any

import cv2

from backend.core.config import CONGESTION_PREDICTOR_PATH
from backend.services.prediction_service import CongestionPredictionService
import backend.services.log_service as log_service

# Direct imports from ML modules
from ml.cv_pipeline import get_video_metadata, iter_frames
from ml.detectors.vehicle_detector import detect_vehicles, load_yolo_model, should_process_frame
from ml.detectors.ambulance_detector import (
    detect_ambulances,
    is_emergency_present,
    load_ambulance_model,
    resolve_ambulance_model_path,
)
from ml.analytics.density_analyzer import analyze_density, count_vehicle_detections, draw_density_overlay
from ml.analytics.congestion_classifier import classify_congestion, draw_congestion_overlay
from ml.analytics.priority_engine import draw_priority_overlay, generate_priority_action
from ml.analytics.signal_timing_engine import generate_signal_timing_recommendation
from ml.analytics.lane_analyzer import analyze_lanes, default_lane_config, draw_lane_overlay
from ml.analytics.green_corridor import simulate_green_corridor

def initial_results() -> dict[str, Any]:
    """Return default dashboard results before analysis runs."""
    return {
        "total_vehicles": 0,
        "car_count": 0,
        "motorcycle_count": 0,
        "bus_count": 0,
        "truck_count": 0,
        "density": "LOW",
        "congestion": "LOW_CONGESTION",
        "predicted_congestion": "Model not trained",
        "emergency_present": False,
        "recommended_action": "NORMAL_OPERATION",
        "recommended_green_seconds": 35,
        "signal_priority_action": "NORMAL_OPERATION",
        "signal_severity": "NORMAL",
        "signal_reason": "Low congestion detected",
        "signal_confidence_note": "Rule-based recommendation",
        "lane_results": [],
        "green_corridor_result": {
            "corridor_active": False,
            "emergency_lane_id": "N/A",
            "emergency_lane_name": "N/A",
            "corridor_status": "INACTIVE",
            "recommended_sequence": [],
            "estimated_clearance_window_seconds": 0,
            "reason": "No emergency vehicle detected",
            "confidence_note": "Rule-based corridor simulation",
        },
        "processed_frames": 0,
        "latest_frame": None,
        "ambulance_message": "Multi-Signal Ambulance Detection Pipeline Active.",
        "ambulance_detected": False,
        "ambulance_confidence": 0.0,
        "emergency_light_score": 0.0,
        "ambulance_reason": "No analysis run",
    }

def analyze_video(
    video_path: Path,
    max_frames: int,
    skip_frames: int,
    vehicle_confidence: float,
    ambulance_confidence: float,
) -> dict[str, Any]:
    """Run a bounded computer vision and analytics pipeline pass over a video file."""
    metadata = get_video_metadata(video_path)
    vehicle_model = load_yolo_model()
    prediction_service = CongestionPredictionService(CONGESTION_PREDICTOR_PATH)
    prediction_service.load_predictor()

    ambulance_model = None
    ambulance_model_path = resolve_ambulance_model_path()
    if ambulance_model_path.exists():
        try:
            ambulance_model = load_ambulance_model(ambulance_model_path)
            ambulance_message = f"Ambulance model loaded: {ambulance_model_path}"
        except Exception as error:
            ambulance_message = f"Error loading custom ambulance model: {error}. Using fallback."
    else:
        ambulance_message = "Multi-Signal Pipeline Active (using generic vehicle detections + HSV light detection)."

    results = initial_results()

    # Containers for logs
    run_start_time = datetime.now()
    vehicle_det_rows = []
    emergency_det_rows = []
    density_rows = []
    congestion_rows = []
    priority_rows = []

    for frame_index, frame in iter_frames(video_path):
        if not should_process_frame(frame_index, skip_frames):
            continue
        if results["processed_frames"] >= max_frames:
            break

        annotated, vehicle_detections = detect_vehicles(
            frame=frame,
            model=vehicle_model,
            confidence_threshold=vehicle_confidence,
            frame_index=frame_index,
            fps=metadata.fps,
            source_video=str(video_path),
        )

        annotated, ambulance_detections = detect_ambulances(
            frame=frame,
            model=ambulance_model,
            confidence_threshold=ambulance_confidence,
            base_frame=annotated,
            vehicle_detections=vehicle_detections,
        )

        vehicle_counts = count_vehicle_detections(vehicle_detections)
        density_result = analyze_density(vehicle_counts)
        congestion_result = classify_congestion(density_result)
        emergency_present = is_emergency_present(ambulance_detections)
        action_result = generate_priority_action(
            emergency_present=emergency_present,
            density_result=density_result,
            congestion_result=congestion_result,
        )
        signal_timing_result = generate_signal_timing_recommendation(
            density_result=density_result,
            congestion_result=congestion_result,
            priority_result=action_result,
        )
        predicted_congestion = prediction_service.predict(
            {
                **density_result,
                "emergency_present": emergency_present,
            }
        )

        frame_height, frame_width = frame.shape[:2]
        lane_regions = default_lane_config(frame_width=frame_width, frame_height=frame_height)
        lane_results = analyze_lanes(
            vehicle_detections=vehicle_detections,
            ambulance_detections=ambulance_detections,
            frame_width=frame_width,
            frame_height=frame_height,
            lane_regions=lane_regions,
        )
        enriched_lane_results = []
        for lane_result in lane_results:
            lane_density_result = analyze_density(
                {
                    "total_vehicles": lane_result["total_vehicles"],
                    "car_count": lane_result["car_count"],
                    "motorcycle_count": lane_result["motorcycle_count"],
                    "bus_count": lane_result["bus_count"],
                    "truck_count": lane_result["truck_count"],
                }
            )
            lane_congestion_result = classify_congestion(lane_density_result)
            lane_action_result = generate_priority_action(
                emergency_present=lane_result["emergency_present"],
                density_result=lane_density_result,
                congestion_result=lane_congestion_result,
            )
            lane_signal_result = generate_signal_timing_recommendation(
                density_result=lane_density_result,
                congestion_result=lane_congestion_result,
                priority_result=lane_action_result,
            )
            enriched_lane_results.append(
                {
                    **lane_result,
                    "density": lane_density_result["density"],
                    "congestion": lane_congestion_result["congestion"],
                    "recommended_action": lane_action_result["recommended_action"],
                    "recommended_green_seconds": lane_signal_result["recommended_green_seconds"],
                }
            )
        green_corridor_result = simulate_green_corridor(
            enriched_lane_results,
            action_result,
            signal_timing_result,
        )

        annotated = draw_density_overlay(annotated, density_result)
        annotated = draw_congestion_overlay(annotated, congestion_result)
        annotated = draw_priority_overlay(annotated, action_result)
        annotated = draw_lane_overlay(annotated, lane_regions, enriched_lane_results)
        latest_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        frame_summary = getattr(ambulance_detections, "frame_summary", {})
        results = {
            **density_result,
            **congestion_result,
            **action_result,
            "recommended_green_seconds": signal_timing_result["recommended_green_seconds"],
            "signal_priority_action": signal_timing_result["priority_action"],
            "signal_severity": signal_timing_result["severity"],
            "signal_reason": signal_timing_result["reason"],
            "signal_confidence_note": signal_timing_result["confidence_note"],
            "lane_results": enriched_lane_results,
            "green_corridor_result": green_corridor_result,
            "predicted_congestion": predicted_congestion,
            "processed_frames": results["processed_frames"] + 1,
            "latest_frame": latest_frame,
            "ambulance_message": ambulance_message,
            "ambulance_detected": frame_summary.get("ambulance_detected", False),
            "ambulance_confidence": frame_summary.get("confidence", 0.0),
            "emergency_light_score": frame_summary.get("emergency_light_score", 0.0),
            "ambulance_reason": "; ".join(frame_summary.get("reason", [])) if frame_summary.get("reason") else "No vehicle candidates detected",
        }

        # Collect log rows
        fps = metadata.fps if metadata.fps > 0 else 30.0
        frame_offset_seconds = frame_index / fps
        frame_timestamp = (run_start_time + timedelta(seconds=frame_offset_seconds)).isoformat(timespec="milliseconds")

        for det in vehicle_detections:
            det_dict = asdict(det)
            det_dict["timestamp"] = frame_timestamp
            vehicle_det_rows.append(det_dict)

        for det in ambulance_detections:
            xmin, ymin, xmax, ymax = [int(value) for value in det["bbox"]]
            emergency_det_rows.append({
                "source_video": str(video_path),
                "frame_index": frame_index,
                "timestamp_seconds": round(frame_offset_seconds, 3),
                "class_id": 0,
                "class_name": "ambulance",
                "confidence": det["confidence"],
                "xmin": xmin,
                "ymin": ymin,
                "xmax": xmax,
                "ymax": ymax,
                "box_width": max(0, xmax - xmin),
                "box_height": max(0, ymax - ymin),
                "timestamp": frame_timestamp,
            })

        density_rows.append({
            "source_video": str(video_path),
            "frame_index": frame_index,
            "timestamp_seconds": round(frame_offset_seconds, 3),
            "total_vehicles": density_result["total_vehicles"],
            "car_count": density_result["car_count"],
            "motorcycle_count": density_result["motorcycle_count"],
            "bus_count": density_result["bus_count"],
            "truck_count": density_result["truck_count"],
            "density": density_result["density"],
            "timestamp": frame_timestamp,
        })

        congestion_rows.append({
            "timestamp": frame_timestamp,
            "total_vehicles": congestion_result["total_vehicles"],
            "density": congestion_result["density"],
            "congestion": congestion_result["congestion"],
        })

        priority_rows.append({
            "timestamp": frame_timestamp,
            "emergency_present": action_result["emergency_present"],
            "density": action_result["density"],
            "congestion": action_result["congestion"],
            "recommended_action": action_result["recommended_action"],
        })

    # Save log collections to disk via log_service
    log_service.log_vehicle_detections(vehicle_det_rows)
    log_service.log_emergency_detections(emergency_det_rows)
    log_service.log_density_analysis(density_rows)
    log_service.log_congestion_analysis(congestion_rows)
    log_service.log_priority_actions(priority_rows)

    return results
