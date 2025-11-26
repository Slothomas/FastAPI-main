# app/controllers/business_controller.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.services.db.sql_server_connection import get_session
from app.models.business import Business
from app.models.business_location import BusinessLocation

router = APIRouter(prefix="/business", tags=["Business"])


@router.get("/my", response_model=List[Business])
def get_my_businesses(
    user_id: int = Query(...),
    session: Session = Depends(get_session),
):
    return session.exec(
        select(Business).where(Business.owner_id == user_id)
    ).all()


@router.get("/{business_id}/locations", response_model=List[BusinessLocation])
def get_locations_by_business(
    business_id: int,
    session: Session = Depends(get_session),
):
    biz = session.get(Business, business_id)
    if not biz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business no encontrado",
        )

    return session.exec(
        select(BusinessLocation).where(BusinessLocation.business_id == business_id)
    ).all()
