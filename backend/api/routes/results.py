"""FastAPI router for retrieving historical run results by ID from database."""

import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.logger import logger
from backend.database.session import get_db
from backend.repositories.processing_repository import ProcessingRepository
from backend.schemas.schemas import HistoricalRecordModel

router = APIRouter(prefix="/results", tags=["Results"])

@router.get("/{record_id}", response_model=HistoricalRecordModel)
async def get_results(record_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific analysis run by its timestamp ID from the database."""
    decoded_id = urllib.parse.unquote(record_id)
    logger.info(f"Looking up database results for ID: {decoded_id}")
    try:
        results = ProcessingRepository.get_all_processing_results(db=db)
        matching_result = None
        
        for res in results:
            ts = res.created_at.isoformat(timespec="milliseconds") + "Z"
            if ts == decoded_id:
                matching_result = res
                break
                
        if not matching_result:
            logger.warning(f"DB results lookup failed: No record found matching ID {decoded_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run result with ID '{decoded_id}' not found."
            )
            
        # Get vehicle count and density
        vehicle_count = 0
        density = "LOW"
        if matching_result.analytics_summaries:
            vehicle_count = matching_result.analytics_summaries[0].vehicle_count
            if vehicle_count <= 10:
                density = "LOW"
            elif vehicle_count <= 25:
                density = "MEDIUM"
            else:
                density = "HIGH"
                
        return HistoricalRecordModel(
            timestamp=decoded_id,
            total_vehicles=vehicle_count,
            density=density,
            congestion=matching_result.congestion_level,
            emergency_present=matching_result.emergency_detected,
            recommended_action=matching_result.signal_recommendation
        )
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error retrieving database result for {decoded_id}: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving database result: {error}"
        )
