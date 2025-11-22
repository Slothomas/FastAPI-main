from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# -------- Requests --------

class FavoriteOfferRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="Worker que guarda la oferta")
    job_offer_id: int = Field(..., gt=0, description="Oferta favorita")


class FavoriteWorkerRequest(BaseModel):
    client_user_id: int = Field(..., gt=0, description="Cliente que guarda al worker")
    worker_user_id: int = Field(..., gt=0, description="Worker favorito")


# -------- Responses --------

class FavoriteOfferResponse(BaseModel):
    id: int
    user_id: int
    job_offer_id: int
    created_at: datetime
    is_active: bool


class FavoriteWorkerResponse(BaseModel):
    id: int
    client_user_id: int
    worker_user_id: int
    created_at: datetime
    is_active: bool


# Listados con info útil (para front y demo)
class FavoriteOfferWithInfo(BaseModel):
    favorite_id: int
    job_offer_id: int
    title: str
    company: str
    location: Optional[str]
    salary_range: Optional[str]
    date_start: Optional[datetime]
    date_end: Optional[datetime]
    created_at: datetime


class FavoriteWorkerWithInfo(BaseModel):
    favorite_id: int
    worker_user_id: int
    full_name: Optional[str]
    bio: Optional[str]
    skills: Optional[str]
    avatar_url: Optional[str]
    rating_avg: Optional[float]
    reviews_count: int
    created_at: datetime
