from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, NVARCHAR, Boolean


class Notification(SQLModel, table=True):
    __tablename__ = "app_notification"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)

    type: str = Field(
        sa_column=Column(NVARCHAR(50), nullable=False)
    )

    payload: Optional[str] = Field(
        default=None,
        sa_column=Column(NVARCHAR(None), nullable=True)  # NVARCHAR(MAX)
    )

    is_read: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False)
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False)
    )

    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False)
    )
