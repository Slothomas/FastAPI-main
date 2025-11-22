# app/models/review.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import NVARCHAR, DateTime, DECIMAL, Integer, Boolean

class Review(SQLModel, table=True):
    __tablename__ = "app_review"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_offer_id: int = Field(foreign_key="job_offer.id", index=True)
    reviewer_id: int = Field(foreign_key="app_user.id", index=True)
    reviewee_id: int = Field(foreign_key="app_user.id", index=True)

    rating: float = Field(sa_column=Column(DECIMAL(2,1), nullable=False))
    comment: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(1000), nullable=True))

    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False))
