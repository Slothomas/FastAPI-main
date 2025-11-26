# app/schemas/gig_payment.py

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class GigPaymentBase(SQLModel):
    assignment_id: int
    job_offer_id: int

    barista_id: int
    business_id: Optional[int] = None

    gross_amount: int

    fee_pct_cafe: float
    fee_pct_barista: float

    fee_amount_cafe: int
    fee_amount_barista: int

    net_amount_barista: int

    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None


class GigPaymentResponse(GigPaymentBase):
    id: int
