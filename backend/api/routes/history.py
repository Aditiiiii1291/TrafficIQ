"""FastAPI router for historical analysis run history."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.core.logger import logger
import backend.services.analytics_service as analytics_service
from backend.schemas.schemas import HistoryResponse, HistoricalRecordModel

router = APIRouter(prefix="/history", tags=["History"])

@router.get("", response_model=HistoryResponse)
async def get_history(
    date_filter: Optional[str] = Query(None, description="Prefix to filter records by timestamp"),
    congestion_level: str = Query("ALL", description="Filter records by congestion level"),
    recommendation: str = Query("ALL", description="Filter records by recommendation action")
):
    """Retrieve historical processing logs and records with optional filtering."""
    logger.info(f"Fetching history logs with filters (date={date_filter}, congestion={congestion_level}, recommendation={recommendation})")
    try:
        records = analytics_service.load_historical_records()
        
        # Apply filters using analytics service
        filtered_records = analytics_service.filter_records(
            records,
            date_filter=date_filter,
            congestion_level=congestion_level,
            recommendation=recommendation
        )
        
        # Format response records
        formatted_records = [
            HistoricalRecordModel(
                timestamp=rec.timestamp,
                total_vehicles=rec.total_vehicles,
                density=rec.density,
                congestion=rec.congestion,
                emergency_present=rec.emergency_present,
                recommended_action=rec.recommended_action
            )
            for rec in filtered_records
        ]
        
        return HistoryResponse(
            records=formatted_records,
            total_records=len(formatted_records)
        )
        
    except Exception as error:
        logger.error(f"Failed to fetch history logs: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history logs: {error}"
        )
