from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, UniqueConstraint


class UserFavoriteWorker(SQLModel, table=True):
    __tablename__ = "user_favorite_workers"
    __table_args__ = (
        UniqueConstraint("client_user_id", "worker_user_id", name="UQ_fav_workers"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    client_user_id: int = Field(foreign_key="app_user.id", nullable=False)
    worker_user_id: int = Field(foreign_key="app_user.id", nullable=False)

    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False)
    )
