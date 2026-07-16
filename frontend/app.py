"""Streamlit dashboard for the TrafficIQ demo."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import UPLOAD_DIR, LOGS_DIR, CONGESTION_PREDICTOR_PATH, API_BASE_URL
from backend.core.logger import setup_logger
from backend.services.prediction_service import CongestionPredictionService
from backend.services.video_processor import analyze_video
import requests
import base64
import numpy as np
import cv2


@dataclass(frozen=True)
class DashboardImports:
    """Project modules needed by the dashboard."""

    cv2: Any
    analyze_density: Any
    classify_congestion: Any
    count_vehicle_detections: Any
    detect_ambulances: Any
    detect_vehicles: Any
    draw_congestion_overlay: Any
    draw_density_overlay: Any
    draw_priority_overlay: Any
    generate_signal_timing_recommendation: Any
    generate_priority_action: Any
    generate_event_statistics: Any
    generate_summary: Any
    generate_trend_data: Any
    analyze_lanes: Any
    default_lane_config: Any
    draw_lane_overlay: Any
    simulate_green_corridor: Any
    get_video_metadata: Any
    is_emergency_present: Any
    iter_frames: Any
    load_congestion_model: Any
    load_historical_records: Any
    load_ambulance_model: Any
    load_yolo_model: Any
    predict_congestion: Any
    resolve_ambulance_model_path: Any
    save_uploaded_video: Any
    should_process_frame: Any
    filter_records: Any
    congestion_levels: list[str]
    recommendation_actions: list[str]


def load_dashboard_imports() -> DashboardImports | None:
    """Import project modules lazily so missing dependencies can be reported cleanly."""

    try:
        import cv2

        from ml.analytics.congestion_classifier import classify_congestion, draw_congestion_overlay
        from ml.analytics.density_analyzer import (
            analyze_density,
            count_vehicle_detections,
            draw_density_overlay,
        )
        from ml.analytics.priority_engine import draw_priority_overlay, generate_priority_action
        from ml.analytics.signal_timing_engine import generate_signal_timing_recommendation
        from ml.analytics.lane_analyzer import analyze_lanes, default_lane_config, draw_lane_overlay
        from ml.analytics.green_corridor import simulate_green_corridor
        from ml.analytics.history_analytics import (
            CONGESTION_LEVELS,
            RECOMMENDATION_ACTIONS,
            filter_records,
            generate_event_statistics,
            generate_summary,
            generate_trend_data,
            load_historical_records,
        )
        from ml.cv_pipeline import get_video_metadata, iter_frames, save_uploaded_video
        from ml.detectors.ambulance_detector import (
            detect_ambulances,
            is_emergency_present,
            load_ambulance_model,
            resolve_ambulance_model_path,
        )
        from ml.detectors.vehicle_detector import detect_vehicles, load_yolo_model, should_process_frame
        from ml.prediction.congestion_predictor import (
            load_model as load_congestion_model,
            predict_congestion,
        )
    except ModuleNotFoundError as error:
        st.error(f"Missing dependency: {error.name}. Install dependencies with pip install -r requirements.txt.")
        return None
    except Exception as error:  # pragma: no cover - Streamlit displays this path interactively.
        st.error(f"Dashboard modules could not be loaded: {error}")
        return None

    return DashboardImports(
        cv2=cv2,
        analyze_density=analyze_density,
        classify_congestion=classify_congestion,
        count_vehicle_detections=count_vehicle_detections,
        detect_ambulances=detect_ambulances,
        detect_vehicles=detect_vehicles,
        draw_congestion_overlay=draw_congestion_overlay,
        draw_density_overlay=draw_density_overlay,
        draw_priority_overlay=draw_priority_overlay,
        generate_signal_timing_recommendation=generate_signal_timing_recommendation,
        generate_priority_action=generate_priority_action,
        generate_event_statistics=generate_event_statistics,
        generate_summary=generate_summary,
        generate_trend_data=generate_trend_data,
        analyze_lanes=analyze_lanes,
        default_lane_config=default_lane_config,
        draw_lane_overlay=draw_lane_overlay,
        simulate_green_corridor=simulate_green_corridor,
        get_video_metadata=get_video_metadata,
        is_emergency_present=is_emergency_present,
        iter_frames=iter_frames,
        load_congestion_model=load_congestion_model,
        load_historical_records=load_historical_records,
        load_ambulance_model=load_ambulance_model,
        load_yolo_model=load_yolo_model,
        predict_congestion=predict_congestion,
        resolve_ambulance_model_path=resolve_ambulance_model_path,
        save_uploaded_video=save_uploaded_video,
        should_process_frame=should_process_frame,
        filter_records=filter_records,
        congestion_levels=CONGESTION_LEVELS,
        recommendation_actions=RECOMMENDATION_ACTIONS,
    )


def render_status_card(label: str, value: str | int | bool) -> None:
    """Render a compact metric-style status card."""

    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-label">{label}</div>
            <div class="status-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def configure_page() -> None:
    """Apply page configuration and lightweight dashboard styling."""

    st.set_page_config(
        page_title="TrafficIQ - AI-Powered Intelligent Traffic Management System",
        page_icon="🚦",
        layout="wide",
    )

    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@600&display=swap');

            html, body, [class*="css"], .stApp {
                font-family: 'Calibri', 'Carlito', 'Trebuchet MS', sans-serif !important;
            }

            h1, h2, h3, h4,
            .stApp h1, .stApp h2, .stApp h3, .stApp h4,
            [data-testid="stHeading"],
            div[data-testid="stMarkdownContainer"] h1,
            div[data-testid="stMarkdownContainer"] h2,
            div[data-testid="stMarkdownContainer"] h3 {
                font-family: 'Franklin Gothic Demi Cond', 'Franklin Gothic Medium Cond',
                             'Oswald', 'Arial Narrow', sans-serif !important;
            }

            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
            }
            .status-card {
                border: 1px solid #d8dee9;
                border-radius: 8px;
                padding: 14px 16px;
                min-height: 92px;
                background: #ffffff;
                margin-bottom: 12px;
            }
            .status-label {
                font-family: 'Franklin Gothic Demi Cond', 'Franklin Gothic Medium Cond',
                             'Oswald', 'Arial Narrow', sans-serif !important;
                color: #4b5563;
                font-size: 0.82rem;
                font-weight: 600;
                text-transform: uppercase;
            }
            .status-value {
                font-family: 'Calibri', 'Carlito', 'Trebuchet MS', sans-serif !important;
                color: #111827;
                font-size: 1.35rem;
                font-weight: 700;
                margin-top: 10px;
                overflow-wrap: anywhere;
            }
            .section-note {
                font-family: 'Calibri', 'Carlito', 'Trebuchet MS', sans-serif !important;
                color: #4b5563;
                font-size: 0.95rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def analyze_uploaded_video(
    imports: DashboardImports,
    video_path: Path,
    max_frames: int,
    skip_frames: int,
    vehicle_confidence: float,
    ambulance_confidence: float,
) -> dict[str, Any]:
    """Delegate to backend video processing service via FastAPI REST API with local fallback."""
    with st.spinner("Analyzing uploaded video..."):
        try:
            payload = {
                "video_name": video_path.name,
                "max_frames": max_frames,
                "skip_frames": skip_frames,
                "vehicle_confidence": vehicle_confidence,
                "ambulance_confidence": ambulance_confidence,
            }
            response = requests.post(f"{API_BASE_URL}/process", json=payload, timeout=120)
            if response.status_code == 200:
                res_data = response.json()
                latest_frame = None
                b64_str = res_data.get("latest_frame_b64")
                if b64_str:
                    try:
                        img_data = base64.b64decode(b64_str)
                        nparr = np.frombuffer(img_data, np.uint8)
                        latest_frame_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        latest_frame = cv2.cvtColor(latest_frame_bgr, cv2.COLOR_BGR2RGB)
                    except Exception as decode_err:
                        setup_logger().warning(f"Failed to decode base64 latest_frame: {decode_err}")
                
                res_data["latest_frame"] = latest_frame
                return res_data
            else:
                setup_logger().warning(f"API processing returned status code {response.status_code}. Falling back to local processor.")
        except Exception as error:
            setup_logger().warning(f"FastAPI connection failed ({error}). Falling back to local processor.")
            
        return analyze_video(
            video_path=video_path,
            max_frames=max_frames,
            skip_frames=skip_frames,
            vehicle_confidence=vehicle_confidence,
            ambulance_confidence=ambulance_confidence,
        )


def render_dashboard(results: dict[str, Any]) -> None:
    """Render dashboard sections and status cards."""

    st.subheader("Traffic Overview")
    traffic_cols = st.columns(5)
    with traffic_cols[0]:
        render_status_card("Vehicle Count", results["total_vehicles"])
    with traffic_cols[1]:
        render_status_card("Cars", results["car_count"])
    with traffic_cols[2]:
        render_status_card("Motorcycles", results["motorcycle_count"])
    with traffic_cols[3]:
        render_status_card("Buses", results["bus_count"])
    with traffic_cols[4]:
        render_status_card("Trucks", results["truck_count"])

    st.subheader("Emergency Status")
    emergency_cols = st.columns(2)
    with emergency_cols[0]:
        render_status_card("Emergency Status", "DETECTED" if results["emergency_present"] else "NONE")
    with emergency_cols[1]:
        st.info(results["ambulance_message"])

    st.subheader("Ambulance Detection Details")
    detail_cols = st.columns(4)
    with detail_cols[0]:
        render_status_card("Ambulance Detected", "True" if results.get("ambulance_detected", False) else "False")
    with detail_cols[1]:
        render_status_card("Confidence", f"{results.get('ambulance_confidence', 0.0):.4f}")
    with detail_cols[2]:
        render_status_card("Emergency Light Score", f"{results.get('emergency_light_score', 0.0):.4f}")
    with detail_cols[3]:
        render_status_card("Detection Reason", results.get("ambulance_reason", "N/A"))

    st.subheader("Congestion Analysis")
    congestion_cols = st.columns(2)
    with congestion_cols[0]:
        render_status_card("Density", results["density"])
    with congestion_cols[1]:
        render_status_card("Congestion", results["congestion"])
    render_status_card("Predicted Congestion", results["predicted_congestion"])

    st.subheader("Priority Recommendation")
    render_status_card("Recommended Action", results["recommended_action"])

    st.subheader("Smart Signal Timing")
    signal_cols = st.columns(3)
    with signal_cols[0]:
        render_status_card("Recommended Green Time", f"{results['recommended_green_seconds']} sec")
    with signal_cols[1]:
        render_status_card("Priority Action", results["signal_priority_action"])
    with signal_cols[2]:
        render_status_card("Severity", results["signal_severity"])
    signal_cols = st.columns(2)
    with signal_cols[0]:
        render_status_card("Reason", results["signal_reason"])
    with signal_cols[1]:
        render_status_card("Confidence Note", results["signal_confidence_note"])

    st.subheader("Multi-Lane Traffic Analysis")
    lane_results = results.get("lane_results", [])
    if lane_results:
        st.dataframe(
            [
                {
                    "Lane": lane["lane_name"],
                    "Vehicles": lane["total_vehicles"],
                    "Utilization": f"{lane['lane_utilization_percent']:.2f}%",
                    "Density": lane["density"],
                    "Congestion": lane["congestion"],
                    "Emergency": "DETECTED" if lane["emergency_present"] else "NONE",
                    "Action": lane["recommended_action"],
                    "Green Time": f"{lane['recommended_green_seconds']} sec",
                }
                for lane in lane_results
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.markdown('<p class="section-note">Run analysis to display lane-level traffic results.</p>', unsafe_allow_html=True)

    st.subheader("Emergency Green Corridor Simulation")
    corridor_result = results.get("green_corridor_result", {})
    corridor_cols = st.columns(3)
    with corridor_cols[0]:
        render_status_card("Corridor Status", corridor_result.get("corridor_status", "INACTIVE"))
    with corridor_cols[1]:
        render_status_card("Emergency Lane", corridor_result.get("emergency_lane_name", "N/A"))
    with corridor_cols[2]:
        render_status_card(
            "Clearance Window",
            f"{corridor_result.get('estimated_clearance_window_seconds', 0)} sec",
        )
    corridor_cols = st.columns(2)
    with corridor_cols[0]:
        render_status_card("Reason", corridor_result.get("reason", "No emergency vehicle detected"))
    with corridor_cols[1]:
        render_status_card("Confidence Note", corridor_result.get("confidence_note", "Rule-based corridor simulation"))

    sequence = corridor_result.get("recommended_sequence", [])
    if sequence:
        st.dataframe(
            [
                {
                    "Lane": item["lane_name"],
                    "Action": item["action"],
                    "Green Time": f"{item['green_seconds']} sec",
                    "Reason": item["reason"],
                }
                for item in sequence
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.markdown('<p class="section-note">No emergency corridor sequence is active.</p>', unsafe_allow_html=True)

    if results["latest_frame"] is not None:
        st.image(results["latest_frame"], caption="Latest analyzed frame", use_container_width=True)
    else:
        st.markdown('<p class="section-note">Run analysis to display the latest processed frame.</p>', unsafe_allow_html=True)


def _distribution_chart(distribution: dict[str, int]) -> Any:
    """Build a small dataframe for Streamlit bar charts."""

    import pandas as pd

    if not distribution:
        return pd.DataFrame({"count": []})
    return pd.DataFrame(
        [{"label": label, "count": count} for label, count in distribution.items()]
    ).set_index("label")


def render_historical_analytics(
    imports: DashboardImports,
    date_filter: str | None,
    congestion_filter: str,
    recommendation_filter: str,
) -> None:
    """Render historical analytics filters, metrics, and charts."""

    import pandas as pd

    st.subheader("Historical Analytics")
    import backend.services.analytics_service as analytics_service
    from ml.analytics.history_analytics import HistoricalRecord
    
    records = []
    filtered_records = []
    
    try:
        all_hist_resp = requests.get(f"{API_BASE_URL}/history", params={"congestion_level": "ALL", "recommendation": "ALL"}, timeout=10)
        if all_hist_resp.status_code == 200:
            records = [
                HistoricalRecord(
                    timestamp=r["timestamp"],
                    total_vehicles=r["total_vehicles"],
                    density=r["density"],
                    congestion=r["congestion"],
                    emergency_present=r["emergency_present"],
                    recommended_action=r["recommended_action"]
                )
                for r in all_hist_resp.json()["records"]
            ]
            
            filt_hist_resp = requests.get(
                f"{API_BASE_URL}/history",
                params={
                    "date_filter": date_filter or None,
                    "congestion_level": congestion_filter,
                    "recommendation": recommendation_filter
                },
                timeout=10
            )
            if filt_hist_resp.status_code == 200:
                filtered_records = [
                    HistoricalRecord(
                        timestamp=r["timestamp"],
                        total_vehicles=r["total_vehicles"],
                        density=r["density"],
                        congestion=r["congestion"],
                        emergency_present=r["emergency_present"],
                        recommended_action=r["recommended_action"]
                    )
                    for r in filt_hist_resp.json()["records"]
                ]
            else:
                raise Exception("Filtered history API request failed")
        else:
            raise Exception("All history API request failed")
    except Exception as error:
        setup_logger().warning(f"FastAPI connection failed for historical data ({error}). Falling back to local services.")
        records = analytics_service.load_historical_records(LOGS_DIR)
        filtered_records = analytics_service.filter_records(
            records,
            date_filter=date_filter or None,
            congestion_level=congestion_filter,
            recommendation=recommendation_filter,
        )

    if not records:
        st.info("No historical logs found yet. Run the detection, density, congestion, and priority pipelines to generate analytics.")
        return

    summary = analytics_service.generate_summary(filtered_records)
    trend_data = analytics_service.generate_trend_data(filtered_records)
    event_stats = analytics_service.generate_event_statistics(filtered_records)

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_status_card("Analyzed Records", summary["total_analyzed_records"])
    with metric_cols[1]:
        render_status_card("Emergency Events", summary["total_emergency_events"])
    with metric_cols[2]:
        render_status_card("Common Congestion", summary["most_common_congestion_level"])
    with metric_cols[3]:
        render_status_card("Common Recommendation", summary["most_common_recommendation"])

    st.caption(f"Emergency event rate: {event_stats['emergency_rate']}")

    vehicle_trend = pd.DataFrame(trend_data["vehicle_count_over_time"])
    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.markdown("Vehicle Count Over Time")
        if vehicle_trend.empty:
            st.info("No vehicle trend records match the selected filters.")
        else:
            st.line_chart(vehicle_trend.set_index("timestamp")["total_vehicles"])

    with chart_cols[1]:
        st.markdown("Density Distribution")
        st.bar_chart(_distribution_chart(trend_data["density_distribution"]))

    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.markdown("Congestion Distribution")
        st.bar_chart(_distribution_chart(trend_data["congestion_distribution"]))

    with chart_cols[1]:
        st.markdown("Recommendation Distribution")
        st.bar_chart(_distribution_chart(trend_data["recommendation_distribution"]))


def main() -> None:
    """Run the Streamlit dashboard."""

    setup_logger("trafficiq_frontend")
    configure_page()

    st.title("TrafficIQ Dashboard")
    st.caption("AI-Powered Intelligent Traffic Management System")

    imports = load_dashboard_imports()

    with st.sidebar:
        st.header("Analysis Settings")
        max_frames = st.slider("Frames to analyze", min_value=1, max_value=100, value=10, step=1)
        skip_frames = st.slider("Skip frames", min_value=0, max_value=10, value=2, step=1)
        vehicle_confidence = st.slider("Vehicle confidence", min_value=0.10, max_value=0.90, value=0.35, step=0.05)
        ambulance_confidence = st.slider("Ambulance confidence", min_value=0.10, max_value=0.90, value=0.35, step=0.05)
        st.header("Historical Filters")
        history_date_filter = st.text_input("Date/timestamp prefix", value="")
        history_congestion_filter = st.selectbox("Congestion level", ["ALL", "LOW_CONGESTION", "MEDIUM_CONGESTION", "HIGH_CONGESTION"])
        history_recommendation_filter = st.selectbox(
            "Recommendation",
            ["ALL", "NORMAL_OPERATION", "EXTEND_GREEN", "HIGH_TRAFFIC_WARNING", "EMERGENCY_PRIORITY"],
        )

    uploaded_file = st.file_uploader("Upload a traffic video", type=["mp4", "avi", "mov"])
    results = initial_results()

    if uploaded_file is not None:
        st.video(uploaded_file.getvalue())

        if imports is not None:
            uploaded_file.seek(0)
            video_path = imports.save_uploaded_video(uploaded_file, UPLOAD_DIR)
            st.caption(f"Uploaded file saved for analysis: {video_path.name}")

            if st.button("Analyze Video", type="primary"):
                try:
                    results = analyze_uploaded_video(
                        imports=imports,
                        video_path=video_path,
                        max_frames=max_frames,
                        skip_frames=skip_frames,
                        vehicle_confidence=vehicle_confidence,
                        ambulance_confidence=ambulance_confidence,
                    )
                    st.success(f"Analyzed {results['processed_frames']} frame(s).")
                except FileNotFoundError as error:
                    st.warning(str(error))
                except Exception as error:  # pragma: no cover - displayed interactively.
                    st.error(f"Analysis failed: {error}")
    else:
        st.info("Upload an mp4, avi, or mov traffic video to begin.")

    render_dashboard(results)
    if imports is not None:
        render_historical_analytics(
            imports=imports,
            date_filter=history_date_filter,
            congestion_filter=history_congestion_filter,
            recommendation_filter=history_recommendation_filter,
        )


if __name__ == "__main__":
    main()
