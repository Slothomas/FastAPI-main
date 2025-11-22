from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class AssignmentStatus(str, Enum):
    ASSIGNED = "assigned"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class JobAssignment(SQLModel, table=True):
    __tablename__ = "job_assignment"

    id: Optional[int] = Field(default=None, primary_key=True)

    job_offer_id: int = Field(foreign_key="job_offer.id", nullable=False)

    # worker y client son AppUser / user_profile => ajusta FK si tu tabla real es otra
    worker_id: int = Field(foreign_key="app_user.id", nullable=False)
    client_id: int = Field(foreign_key="app_user.id", nullable=False)

    status: AssignmentStatus = Field(default=AssignmentStatus.ASSIGNED, nullable=False)

    assigned_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)

    notes: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True, nullable=False)
