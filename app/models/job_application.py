from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, TEXT, NVARCHAR, Enum as SQLEnum, DECIMAL, Boolean
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

    # ===== NUEVO: post trabajo / reseñas =====
    COMPLETED_BY_EMPLOYER = "completed_by_employer"
    COMPLETED_BY_WORKER = "completed_by_worker"
    COMPLETED_CONFIRMED = "completed_confirmed"


class RejectionReason(str, enum.Enum):
    NO_CUMPLE_REQUISITOS = "NO_CUMPLE_REQUISITOS"
    YA_CUBRIMOS_VACANTES = "YA_CUBRIMOS_VACANTES"
    NO_DISPONIBILIDAD_HORARIA = "NO_DISPONIBILIDAD_HORARIA"
    EXPERIENCIA_INSUFICIENTE = "EXPERIENCIA_INSUFICIENTE"
    OTRO = "OTRO"


class JobApplication(SQLModel, table=True):
    """
    Modelo de postulación a oferta de trabajo.
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

    match_score: Optional[float] = Field(
        default=None,
        sa_column=Column(DECIMAL(5, 2), nullable=True)
    )
    match_breakdown_json: Optional[str] = Field(
        default=None,
        sa_column=Column(NVARCHAR(None), nullable=True)
    )
    match_refreshed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True)
    )

    applied_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False)
    )

    # onupdate asegura que se refresque solo en updates
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime, nullable=False, onupdate=datetime.now)
    )

    rejection_reason: Optional[str] = Field(
        default=None,
        sa_column=Column(NVARCHAR(60), nullable=True)
    )
    rejection_note: Optional[str] = Field(
        default=None,
        sa_column=Column(TEXT, nullable=True)
    )
    rejected_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True)
    )

    # ============================
    # COLUMNAS REALES PARA RESEÑAS
    # BIT/BOOLEAN, NOT NULL, DEFAULT 0
    # ============================
    worker_reviewed: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="0")
    )
    employer_reviewed: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default="0")
    )
