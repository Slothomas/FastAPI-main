from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, UniqueConstraint


class UserFavoriteOffer(SQLModel, table=True):
    __tablename__ = "user_favorite_offers"
    __table_args__ = (
        UniqueConstraint("user_id", "job_offer_id", name="UQ_fav_offers"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", nullable=False)
    job_offer_id: int = Field(foreign_key="job_offer.id", nullable=False)

    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False)
    )
