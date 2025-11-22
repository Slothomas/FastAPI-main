# app/schemas/review.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, confloat


class ReviewCreate(BaseModel):
    job_offer_id: int = Field(..., gt=0)
    reviewee_id: int = Field(..., gt=0)  # worker evaluado
    rating: confloat(ge=1, le=5) = Field(..., description="Rating entre 1 y 5")
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewResponse(BaseModel):
    id: int
    job_offer_id: int
    reviewer_id: int
    reviewee_id: int
    rating: float
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    reviewee_id: int
    rating_avg: float
    reviews_count: int
    reviews: List[ReviewResponse]
