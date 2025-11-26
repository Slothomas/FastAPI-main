# app/controllers/gig_payment_controller.py  (o app/api/gig_payments.py)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.services.db.sql_server_connection import get_session
from app.models.gig_payment import GigPayment
from app.schemas.gig_payment import GigPaymentResponse

router = APIRouter(prefix="/gig-payments", tags=["GigPayments"])


@router.get("/", response_model=list[GigPaymentResponse])
def list_gig_payments(
    barista_id: int | None = Query(default=None),
    business_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
):
    """
    Lista pagos. Puedes filtrar por barista_id o business_id si quieres.
    Más adelante esto lo va a consumir el dashboard admin.
    """
    query = select(GigPayment)

    if barista_id is not None:
        query = query.where(GigPayment.barista_id == barista_id)

    if business_id is not None:
        query = query.where(GigPayment.business_id == business_id)

    payments = session.exec(query).all()
    return payments


@router.get("/{payment_id}", response_model=GigPaymentResponse)
def get_gig_payment(
    payment_id: int,
    session: Session = Depends(get_session),
):
    """
    Detalle de un GigPayment concreto.
    Útil para debugging o futuras vistas admin.
    """
    payment = session.get(GigPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="GigPayment no encontrado")
    return payment
