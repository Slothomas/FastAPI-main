from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
import enum

from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import Integer, DateTime, Float, Enum as SQLEnum

# IMPORTACIONES REALES
from app.models.business import Business
from app.models.job_offer import JobOffer

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.app_user import AppUser


# ============================================================
# ENUMS
# ============================================================

class GigPaymentStatus(str, enum.Enum):
    SIMULATED = "SIMULATED"   # calculado al completar turno (MVP)
    CONFIRMED = "CONFIRMED"   # si en el futuro se valida el pago
    PAID = "PAID"             # si en el futuro conectas pasarela real


# ============================================================
# MODELO
# ============================================================

class GigPayment(SQLModel, table=True):
    __tablename__ = "gig_payment"

    id: Optional[int] = Field(default=None, primary_key=True)

    # --------------------------------------------------------
    # RELACIONES CLAVE
    # --------------------------------------------------------
    assignment_id: int = Field(
        foreign_key="assignment.id",
        nullable=False,
        index=True
    )

    job_offer_id: int = Field(
        foreign_key="job_offer.id",
        nullable=False,
        index=True
    )

    # Barista (trabajador que hizo el turno)
    barista_id: int = Field(
        foreign_key="app_user.id",
        nullable=False,
        index=True
    )

    # Cafetería / negocio que creó la oferta
    business_id: Optional[int] = Field(
        default=None,
        foreign_key="business.id",
        nullable=True,
        index=True
    )

    # --------------------------------------------------------
    # MONTOS Y PORCENTAJES
    # (usamos Integer para CLP, igual que salary_range / shift_gross_amount)
    # --------------------------------------------------------

    # Monto bruto del turno (CLP)
    gross_amount: int = Field(
        sa_column=Column(Integer, nullable=False)
    )

    # Porcentajes usados (para dejar trazado si algún día cambian)
    fee_pct_cafe: float = Field(
        default=0.07,
        sa_column=Column(Float, nullable=False)
    )

    fee_pct_barista: float = Field(
        default=0.03,
        sa_column=Column(Float, nullable=False)
    )

    # Monto que gana la plataforma desde la cafetería (CLP)
    fee_amount_cafe: int = Field(
        sa_column=Column(Integer, nullable=False)
    )

    # Monto que gana la plataforma desde el barista (CLP)
    fee_amount_barista: int = Field(
        sa_column=Column(Integer, nullable=False)
    )

    # Monto neto que recibe el barista (CLP)
    net_amount_barista: int = Field(
        sa_column=Column(Integer, nullable=False)
    )

    # --------------------------------------------------------
    # ESTADO Y FECHAS
    # --------------------------------------------------------

    status: GigPaymentStatus = Field(
        default=GigPaymentStatus.SIMULATED,
        sa_column=Column(SQLEnum(GigPaymentStatus), nullable=False)
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False)
    )

    paid_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True)
    )

    # --------------------------------------------------------
    # RELATIONSHIPS (opcionales por ahora)
    # --------------------------------------------------------

    # assignment: "Assignment" = Relationship(back_populates="gig_payment")
    # job_offer: "JobOffer" = Relationship(back_populates="gig_payments")
    # barista: "AppUser" = Relationship(back_populates="gig_payments_as_barista")
    # business: "Business" = Relationship(back_populates="gig_payments")
