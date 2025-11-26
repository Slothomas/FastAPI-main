from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import NVARCHAR, DateTime, DECIMAL, Integer, Boolean


class Review(SQLModel, table=True):
    __tablename__ = "app_review"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Reseña ligada a una postulación
    application_id: int = Field(
        foreign_key="job_application.id",
        index=True,
        nullable=False
    )

    job_offer_id: int = Field(foreign_key="job_offer.id", index=True, nullable=False)
    reviewer_id: int = Field(foreign_key="app_user.id", index=True, nullable=False)
    reviewee_id: int = Field(foreign_key="app_user.id", index=True, nullable=False)

    rating: float = Field(
        sa_column=Column(DECIMAL(2, 1), nullable=False)
    )

    topic: Optional[str] = Field(
        default="general",
        sa_column=Column(NVARCHAR(50), nullable=True)
    )

    comment: Optional[str] = Field(
        default=None,
        sa_column=Column(NVARCHAR(1000), nullable=True)
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False)
    )

    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False)
    )
