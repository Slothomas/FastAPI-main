from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, TEXT, NVARCHAR, Enum as SQLEnum, DECIMAL
import enum


class ApplicationStatus(str, enum.Enum):
    """Estados del proceso de contratación"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEWED = "interviewed"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"


class JobApplication(SQLModel, table=True):
    """
    Modelo de postulación a oferta de trabajo.
    Relaciona un usuario con una oferta de trabajo.
    """
    __tablename__ = "job_application"

    id: Optional[int] = Field(default=None, primary_key=True)

    job_offer_id: int = Field(foreign_key="job_offer.id", nullable=False)
    user_id: int = Field(foreign_key="app_user.id", nullable=False)

    cover_letter: Optional[str] = Field(
        default=None, sa_column=Column(TEXT, nullable=True)
    )

    status: ApplicationStatus = Field(
        default=ApplicationStatus.PENDING,
        sa_column=Column(SQLEnum(ApplicationStatus), nullable=False)
    )

    recruiter_notes: Optional[str] = Field(
        default=None, sa_column=Column(TEXT, nullable=True)
    )

    # ===== NUEVO: campos de matching persistido =====
    match_score: Optional[float] = Field(
        default=None,
        sa_column=Column(DECIMAL(5, 2), nullable=True)
    )
    match_breakdown_json: Optional[str] = Field(
        default=None,
        sa_column=Column(NVARCHAR(None), nullable=True)  # NVARCHAR(MAX)
    )
    match_refreshed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True)
    )

    applied_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False)
    )
