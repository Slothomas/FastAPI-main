# app/schemas/review.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, confloat


class ReviewCreate(BaseModel):
    """
    Datos que el FRONT envía al backend al crear una reseña.
    OJO: Ya NO incluye reviewee_id ni reviewer_id.
    Esos se calculan en backend.
    """

    # Obligatorios
    application_id: int = Field(..., gt=0)
    job_offer_id: int = Field(..., gt=0)

    # Rating 1–5
    rating: confloat(ge=1, le=5) = Field(
        ..., description="Rating entre 1 y 5"
    )

    # Opcionales
    topic: Optional[str] = Field(default="general", max_length=50)
    comment: Optional[str] = Field(None, max_length=1000)

    # NO se incluyen:
    # reviewee_id
    # reviewer_id
    # (ambos los determina backend según rol real)


class ReviewResponse(BaseModel):
    id: int
    application_id: int
    job_offer_id: int
    reviewer_id: int
    reviewee_id: int
    rating: float
    topic: Optional[str]
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    reviewee_id: int
    rating_avg: float
    reviews_count: int
    reviews: List[ReviewResponse]
