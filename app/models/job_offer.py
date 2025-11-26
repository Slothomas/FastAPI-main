from __future__ import annotations

from datetime import datetime, date
from typing import Optional, TYPE_CHECKING, List
import enum

from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import NVARCHAR, TEXT, DateTime, Enum as SQLEnum, Date

# IMPORTACIONES REALES (Runtime)
# Necesarias para que SQLAlchemy resuelva las relaciones sin errores
from app.models.business import Business
from app.models.business_location import BusinessLocation

if TYPE_CHECKING:
    # Mantenemos JobApplication aquí por precaución de ciclos
    from app.models.job_application import JobApplication


# ============================================================
# ENUMS
# ============================================================

class JobType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    REPLACEMENT = "REPLACEMENT"
    URGENT = "URGENT"


class JobOfferStatus(str, enum.Enum):
    PUBLICADO = "PUBLICADO"
    PAUSADO = "PAUSADO"
    CERRADO = "CERRADO"


class UrgencyType(str, enum.Enum):
    NORMAL = "NORMAL"
    URGENT = "URGENT"


# ============================================================
# MODELO
# ============================================================

class JobOffer(SQLModel, table=True):
    __tablename__ = "job_offer"

    id: Optional[int] = Field(default=None, primary_key=True)

    title: str = Field(sa_column=Column(NVARCHAR(200), nullable=False))
    company: str = Field(sa_column=Column(NVARCHAR(200), nullable=False))

    # Texto legacy
    location: str = Field(sa_column=Column(NVARCHAR(200), nullable=False))
    
    region: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(120), nullable=True))
    comuna: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(120), nullable=True))

    job_type: JobType = Field(sa_column=Column(SQLEnum(JobType), nullable=False))
    description: str = Field(sa_column=Column(TEXT, nullable=False))

    salary_range: Optional[str] = Field(default=None, sa_column=Column(NVARCHAR(100), nullable=True))
    requirements: Optional[str] = Field(default=None, sa_column=Column(TEXT, nullable=True))
    required_skills: Optional[str] = Field(default=None, sa_column=Column(TEXT, nullable=True))

    urgency: UrgencyType = Field(
        default=UrgencyType.NORMAL,
        sa_column=Column(SQLEnum(UrgencyType), nullable=False)
    )

    status: JobOfferStatus = Field(
        default=JobOfferStatus.PUBLICADO,
        sa_column=Column(SQLEnum(JobOfferStatus), nullable=False)
    )

    date_start: Optional[date] = Field(default=None, sa_column=Column(Date, nullable=True))
    date_end: Optional[date] = Field(default=None, sa_column=Column(Date, nullable=True))

    # FK Usuario Creador (asegúrate de que app_user exista)
    created_by: int = Field(foreign_key="app_user.id", nullable=False)

    # FK Aplicación Seleccionada
    selected_application_id: Optional[int] = Field(
        default=None,
        foreign_key="job_application.id",
        nullable=True
    )

    filled_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True)
    )

    is_active: int = Field(default=1, nullable=False)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False)
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False)
    )

    vacancies_filled: int = Field(default=0, nullable=False)
    vacancies_total: int = Field(default=1, ge=1, nullable=False)

    # ============================================================
    # FKs a Business y Location
    # ============================================================
    business_id: Optional[int] = Field(
        default=None,
        foreign_key="business.id",
        nullable=True,
        index=True
    )

    location_id: Optional[int] = Field(
        default=None,
        foreign_key="business_location.id",
        nullable=True,
        index=True
    )

    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    
    # Relación N:1 con Business
    #business: "Business" = Relationship(back_populates="job_offers")
    
    # Relación N:1 con BusinessLocation
    #location_obj: "BusinessLocation" = Relationship(back_populates="job_offers")

    # Relación 1:N con JobApplication
    #applications: List["JobApplication"] = Relationship(back_populates="job_offer")