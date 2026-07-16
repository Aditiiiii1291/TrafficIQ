"""FastAPI router for aggregated historical analytics from database."""

from collections import Counter
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.logger import logger
from backend.database.session import get_db
from backend.repositories.processing_repository import ProcessingRepository
from backend.schemas.schemas import AnalyticsResponse, TrafficStats, TrendData, EventStats

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("", response_model=AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """Retrieve aggregated traffic flow statistics, congestion trends, and metrics from database."""
    logger.info("Fetching database analytics summary")
    try:
        results = ProcessingRepository.get_all_processing_results(db=db)
        
        if not results:
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
            
        total_records = len(results)
        emergency_events = sum(1 for res in results if res.emergency_detected)
        
        # Calculate rates
        rate_val = (emergency_events / total_records) if total_records > 0 else 0.0
        emergency_rate = f"{rate_val:.1%}"
        
        # Congestion and recommendation counters
        congestion_counter = Counter(res.congestion_level for res in results)
        rec_counter = Counter(res.signal_recommendation for res in results)
        
        most_common_congestion = congestion_counter.most_common(1)[0][0] if congestion_counter else "N/A"
        most_common_rec = rec_counter.most_common(1)[0][0] if rec_counter else "N/A"
        
        # Build trends
        vehicle_trend = []
        density_counter = Counter()
        
        for res in results:
            ts = res.created_at.isoformat(timespec="milliseconds") + "Z"
            v_count = 0
            if res.analytics_summaries:
                v_count = res.analytics_summaries[0].vehicle_count
                
            vehicle_trend.append({
                "timestamp": ts,
                "total_vehicles": v_count
            })
            
            # Map density
            if v_count <= 10:
                density = "LOW"
            elif v_count <= 25:
                density = "MEDIUM"
            else:
                density = "HIGH"
            density_counter[density] += 1
            
        return AnalyticsResponse(
            summary=TrafficStats(
                total_analyzed_records=total_records,
                total_emergency_events=emergency_events,
                most_common_congestion_level=most_common_congestion,
                most_common_recommendation=most_common_rec
            ),
            trends=TrendData(
                vehicle_count_over_time=vehicle_trend,
                density_distribution=dict(density_counter),
                congestion_distribution=dict(congestion_counter),
                recommendation_distribution=dict(rec_counter)
            ),
            event_statistics=EventStats(
                total_emergency_events=emergency_events,
                emergency_rate=emergency_rate
            )
        )
        
    except Exception as error:
        logger.error(f"Failed to compile database analytics: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile database analytics: {error}"
        )
