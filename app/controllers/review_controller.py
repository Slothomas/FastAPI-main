# app/controllers/review_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from sqlmodel import Session

from app.services.db.sql_server_connection import get_session
from app.services.db.review_service import ReviewService
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewListResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    reviewer_id: int = Query(..., description="ID del usuario que evalúa"),
    session: Session = Depends(get_session)
):
    review = ReviewService.create_review(
        session=session,
        reviewer_id=reviewer_id,
        data=data
    )

    if not review:
        raise HTTPException(
            status_code=400,
            detail="No se pudo crear review (posible duplicado)."
        )

    return review


@router.get("/user/{user_id}", response_model=ReviewListResponse)
def get_reviews_for_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    reviews = ReviewService.get_reviews_for_user(session, user_id)
    avg_rating, cnt = ReviewService.get_reviews_summary_for_user(session, user_id)

    return ReviewListResponse(
        reviewee_id=user_id,
        rating_avg=avg_rating,
        reviews_count=cnt,
        reviews=reviews
    )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    requester_id: int = Query(..., description="ID del usuario que elimina su review"),
    session: Session = Depends(get_session)
):
    ok = ReviewService.delete_review(session, review_id, requester_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail="Review no encontrada o no tienes permiso para eliminarla."
        )
    return None
