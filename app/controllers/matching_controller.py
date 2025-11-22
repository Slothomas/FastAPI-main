from fastapi import APIRouter, HTTPException
from app.services.db.matching_service import get_matching_workers

router = APIRouter(
    prefix="/job-offers",
    tags=["Matching"]
)

@router.get("/{job_offer_id}/matching")
def matching(job_offer_id: int):
    result = get_matching_workers(job_offer_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    return result
