"""FastAPI router for historical analysis run history from database."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.core.logger import logger
from backend.database.session import get_db
from backend.repositories.processing_repository import ProcessingRepository
from backend.schemas.schemas import HistoryResponse, HistoricalRecordModel

router = APIRouter(prefix="/history", tags=["History"])

@router.get("", response_model=HistoryResponse)
async def get_history(
    date_filter: Optional[str] = Query(None, description="Prefix to filter records by timestamp"),
    congestion_level: str = Query("ALL", description="Filter records by congestion level"),
    recommendation: str = Query("ALL", description="Filter records by recommendation action"),
    db: Session = Depends(get_db)
):
    """Retrieve historical processing logs and records from the database with optional filtering."""
    logger.info(f"Fetching history logs from DB (date={date_filter}, congestion={congestion_level}, recommendation={recommendation})")
    try:
        results = ProcessingRepository.get_all_processing_results(
            db=db,
            date_filter=date_filter,
            congestion_level=congestion_level,
            recommendation=recommendation
        )
        
        formatted_records = []
        for res in results:
            # Safely fetch vehicle count and density from related analytics summaries
            vehicle_count = 0
            density = "LOW"
            if res.analytics_summaries:
                vehicle_count = res.analytics_summaries[0].vehicle_count
                
                # Re-calculate density based on total vehicles count
                if vehicle_count <= 10:
                    density = "LOW"
                elif vehicle_count <= 25:
                    density = "MEDIUM"
                else:
                    density = "HIGH"
                    
            formatted_records.append(
                HistoricalRecordModel(
                    timestamp=res.created_at.isoformat(timespec="milliseconds") + "Z",
                    total_vehicles=vehicle_count,
                    density=density,
                    congestion=res.congestion_level,
                    emergency_present=res.emergency_detected,
                    recommended_action=res.signal_recommendation
                )
            )
            
        return HistoryResponse(
            records=formatted_records,
            total_records=len(formatted_records)
        )
        
    except Exception as error:
        logger.error(f"Failed to fetch history logs from DB: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history logs from DB: {error}"
        )
