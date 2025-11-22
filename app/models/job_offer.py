# app/models/job_offer.py
from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import NVARCHAR, TEXT, DateTime, Enum as SQLEnum, Date
import enum


class JobType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    REPLACEMENT = "replacement"
    URGENT = "urgent"


class JobOfferStatus(str, enum.Enum):
    PUBLICADO = "PUBLICADO"
    PAUSADO = "PAUSADO"
    CERRADO = "CERRADO"


class UrgencyType(str, enum.Enum):
    NORMAL = "NORMAL"
    URGENT = "URGENT"


class JobOffer(SQLModel, table=True):
    __tablename__ = "job_offer"

    id: Optional[int] = Field(default=None, primary_key=True)

    title: str = Field(sa_column=Column(NVARCHAR(200), nullable=False))
    company: str = Field(sa_column=Column(NVARCHAR(200), nullable=False))

    # En gig te conviene separar ubicación
    location: str = Field(sa_column=Column(NVARCHAR(200), nullable=False))
    region: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(120), nullable=True))
    comuna: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(120), nullable=True))

    job_type: JobType = Field(sa_column=Column(SQLEnum(JobType), nullable=False))
    description: str = Field(sa_column=Column(TEXT, nullable=False))

    salary_range: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(100), nullable=True))
    requirements: Optional[str] = Field(default=None, sa_column=Column(TEXT, nullable=True))

    # Skills gig
    required_skills: Optional[str] = Field(default=None, sa_column=Column(TEXT, nullable=True))

    # Urgencia + status marketplace
    urgency: UrgencyType = Field(
        default=UrgencyType.NORMAL,
        sa_column=Column(SQLEnum(UrgencyType), nullable=False)
    )

    status: JobOfferStatus = Field(
        default=JobOfferStatus.PUBLICADO,
        sa_column=Column(SQLEnum(JobOfferStatus), nullable=False)
    )

    # Rango de fechas del turno
    date_start: Optional[date] = Field(default=None, sa_column=Column(Date, nullable=True))
    date_end: Optional[date] = Field(default=None, sa_column=Column(Date, nullable=True))

    created_by: int = Field(foreign_key="app_user.id", nullable=False)

    # contratación
    selected_application_id: Optional[int] = Field(
        default=None,
        foreign_key="job_application.id",
        nullable=True
    )
    filled_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True)
    )

    # soft delete
    is_active: int = Field(default=1, nullable=False)

    created_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime, nullable=False))
    updated_at: datetime = Field(default_factory=datetime.now, sa_column=Column(DateTime, nullable=False))

    vacancies_filled: int = Field(default=0)
