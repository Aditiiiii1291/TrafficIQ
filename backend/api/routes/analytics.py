"""FastAPI router for aggregated historical analytics."""

from fastapi import APIRouter, HTTPException, status
from backend.core.logger import logger
import backend.services.analytics_service as analytics_service
from backend.schemas.schemas import AnalyticsResponse, TrafficStats, TrendData, EventStats

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("", response_model=AnalyticsResponse)
async def get_analytics():
    """Retrieve aggregated traffic flow statistics, congestion trends, and metrics."""
    logger.info("Fetching aggregated analytics summary")
    try:
        records = analytics_service.load_historical_records()
        
        if not records:
            # Return empty response metrics safely
            return AnalyticsResponse(
                summary=TrafficStats(
                    total_analyzed_records=0,
                    total_emergency_events=0,
                    most_common_congestion_level="N/A",
                    most_common_recommendation="N/A"
                ),
                trends=TrendData(
                    vehicle_count_over_time=[],
                    density_distribution={},
                    congestion_distribution={},
                    recommendation_distribution={}
                ),
                event_statistics=EventStats(
                    total_emergency_events=0,
                    emergency_rate="0.0%"
                )
            )
            
        summary_raw = analytics_service.generate_summary(records)
        trends_raw = analytics_service.generate_trend_data(records)
        events_raw = analytics_service.generate_event_statistics(records)
        
        return AnalyticsResponse(
            summary=TrafficStats(
                total_analyzed_records=summary_raw.get("total_analyzed_records", 0),
                total_emergency_events=summary_raw.get("total_emergency_events", 0),
                most_common_congestion_level=str(summary_raw.get("most_common_congestion_level", "N/A")),
                most_common_recommendation=str(summary_raw.get("most_common_recommendation", "N/A"))
            ),
            trends=TrendData(
                vehicle_count_over_time=trends_raw.get("vehicle_count_over_time", []),
                density_distribution=trends_raw.get("density_distribution", {}),
                congestion_distribution=trends_raw.get("congestion_distribution", {}),
                recommendation_distribution=trends_raw.get("recommendation_distribution", {})
            ),
            event_statistics=EventStats(
                total_emergency_events=events_raw.get("total_emergency_events", 0),
                emergency_rate=str(events_raw.get("emergency_rate", "0.0%"))
            )
        )
        
    except Exception as error:
        logger.error(f"Failed to compile analytics: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile analytics: {error}"
        )
