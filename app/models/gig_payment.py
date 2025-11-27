# app/models/gig_payment.py

from __future__ import annotations

from datetime import datetime
from typing import Optional
import enum

from sqlmodel import SQLModel, Field


class GigPaymentStatus(str, enum.Enum):
    SIMULATED = "SIMULATED"
    PENDING = "PENDING"
    PAID = "PAID"


class GigPayment(SQLModel, table=True):
    __tablename__ = "gig_payment"

    id: Optional[int] = Field(default=None, primary_key=True)

    # FK a job_assignment (tabla real: job_assignment)
    assignment_id: int = Field(
        foreign_key="job_assignment.id",
        index=True,
    )

    # FK a job_offer
    job_offer_id: int = Field(
        foreign_key="job_offer.id",
        index=True,
    )

    # FK a usuario barista
    barista_id: int = Field(
        foreign_key="app_user.id",
        index=True,
    )

    # FK opcional a negocio (cafetería)
    business_id: Optional[int] = Field(
        default=None,
        foreign_key="business.id",
        index=True,
    )

    # Monto bruto de la oferta (por turno / por gig)
    gross_amount: int

    # Porcentajes de fee
    fee_pct_cafe: float
    fee_pct_barista: float

    # montos de fee ya calculados
    fee_amount_cafe: int
    fee_amount_barista: int

    # neto para el barista
    net_amount_barista: int

    status: GigPaymentStatus = Field(default=GigPaymentStatus.SIMULATED)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None

    # ⚠️ Importante: sin relationships aquí
    # Nada de relationship("JobAssignment") ni similares
