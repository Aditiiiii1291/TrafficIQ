"""FastAPI router for retrieving historical run results by ID."""

import urllib.parse
from fastapi import APIRouter, HTTPException, status
from backend.core.logger import logger
import backend.services.analytics_service as analytics_service
from backend.schemas.schemas import HistoricalRecordModel

router = APIRouter(prefix="/results", tags=["Results"])

@router.get("/{record_id}", response_model=HistoricalRecordModel)
async def get_results(record_id: str):
    """Retrieve details of a specific analysis run by its timestamp ID."""
    decoded_id = urllib.parse.unquote(record_id)
    logger.info(f"Looking up results for ID: {decoded_id}")
    try:
        records = analytics_service.load_historical_records()
        matching_record = None
        
        for rec in records:
            if rec.timestamp == decoded_id:
                matching_record = rec
                break
                
        if not matching_record:
            logger.warning(f"Results lookup failed: No record found matching ID {decoded_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run result with ID '{decoded_id}' not found."
            )
            
        return HistoricalRecordModel(
            timestamp=matching_record.timestamp,
            total_vehicles=matching_record.total_vehicles,
            density=matching_record.density,
            congestion=matching_record.congestion,
            emergency_present=matching_record.emergency_present,
            recommended_action=matching_record.recommended_action
        )
        
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Error retrieving result for {decoded_id}: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving result: {error}"
        )
