from __future__ import annotations

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import NVARCHAR, TEXT, DateTime, Float

# IMPORTACIÓN REAL (Runtime) para que SQLAlchemy encuentre la clase "Business"
# Esto es seguro porque Business.py NO importa BusinessLocation.
from app.models.business import Business

if TYPE_CHECKING:
    # JobOffer sí podría causar ciclo si lo importamos arriba, así que lo dejamos aquí
    from app.models.job_offer import JobOffer


class BusinessLocation(SQLModel, table=True):
    """
    Sucursal/Local físico de un negocio.
    Guarda dirección y coordenadas lat/lng.
    """
    __tablename__ = "business_location"

    id: Optional[int] = Field(default=None, primary_key=True)

    business_id: int = Field(
        foreign_key="business.id",
        nullable=False,
        index=True,
        description="Negocio al que pertenece este local"
    )

    name: str = Field(
        sa_column=Column(NVARCHAR(200), nullable=False),
        description="Nombre de la sucursal/local"
    )

    address: str = Field(
        sa_column=Column(NVARCHAR(300), nullable=False),
        description="Dirección textual del local"
    )

    region: Optional[str] = Field(
        default=None,
        sa_column=Column(NVARCHAR(120), nullable=True)
    )

    comuna: Optional[str] = Field(
        default=None,
        sa_column=Column(NVARCHAR(120), nullable=True)
    )

    lat: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="Latitud del local"
    )

    lng: Optional[float] = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        description="Longitud del local"
    )

    notes: Optional[str] = Field(
        default=None,
        sa_column=Column(TEXT, nullable=True),
        description="Notas internas"
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

    # -------------------------
    # Relationships
    # -------------------------
    
    # Relación N:1 con Business
    # Al haber importado Business arriba, SQLAlchemy ya sabe qué es.
    #business: "Business" = Relationship(
    #    back_populates="locations"
    #)

    # Relación 1:N con JobOffer
    #job_offers: List["JobOffer"] = Relationship(
    #    back_populates="location_obj"
    #)