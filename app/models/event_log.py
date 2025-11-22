from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, NVARCHAR, Integer


class EventLog(SQLModel, table=True):
    __tablename__ = "app_event_log"

    id: Optional[int] = Field(default=None, primary_key=True)

    event_type: str = Field(
        sa_column=Column(NVARCHAR(60), nullable=False)
    )

    actor_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, nullable=True)
    )

    entity_type: str = Field(
        sa_column=Column(NVARCHAR(60), nullable=False)
    )

    entity_id: int = Field(index=True)

 
    metadata_text: Optional[str] = Field(
        default=None,
        sa_column=Column("metadata", NVARCHAR(None), nullable=True)  # NVARCHAR(MAX)
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False)
    )
