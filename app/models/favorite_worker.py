from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime

class FavoriteWorker(SQLModel, table=True):
    __tablename__ = "favorite_worker"

    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="app_user.id", index=True)
    worker_id: int = Field(foreign_key="app_user.id", index=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False)
    )
