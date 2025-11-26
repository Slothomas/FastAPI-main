from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import NVARCHAR, TEXT, DateTime

class Business(SQLModel, table=True):
    __tablename__ = "business"

    id: Optional[int] = Field(default=None, primary_key=True)

    owner_id: int = Field(
        foreign_key="app_user.id",
        nullable=False,
        index=True,
        description="Usuario dueño del negocio"
    )

    name: str = Field(
        sa_column=Column(NVARCHAR(200), nullable=False),
        description="Nombre comercial del negocio"
    )

    business_type: Optional[str] = Field(
        default=None,
        sa_column=Column(NVARCHAR(100), nullable=True),
        description="Tipo de negocio: café, restaurante, academia, etc."
    )

    description: Optional[str] = Field(
        default=None,
        sa_column=Column(TEXT, nullable=True),
        description="Descripción general del negocio"
    )

    logo_url: Optional[str] = Field(
        default=None,
        sa_column=Column(NVARCHAR(500), nullable=True),
        description="URL logo o imagen del negocio"
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
    # Relationships (DESACTIVADAS TEMPORALMENTE PARA EVITAR ERROR CIRCULAR)
    # -------------------------
    # locations: List["BusinessLocation"] = Relationship(back_populates="business")
    # job_offers: List["JobOffer"] = Relationship(back_populates="business")