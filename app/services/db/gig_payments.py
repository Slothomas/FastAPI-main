# app/services/gig_payments.py

from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select

from app.models.gig_payment import GigPayment
from app.models.job_offer import JobOffer
from app.models.job_assignment import JobAssignment

from app.utils.fees import FEE_PCT_CAFE, FEE_PCT_BARISTA


def _get_barista_id_from_assignment(assignment: JobAssignment) -> int:
    """
    Obtiene el ID del barista desde el assignment.
    Ajusta aquí si tu modelo usa otro nombre de campo (por ejemplo user_id).
    """
    if hasattr(assignment, "worker_id") and assignment.worker_id is not None:
        return assignment.worker_id

    if hasattr(assignment, "user_id") and assignment.user_id is not None:
        return assignment.user_id

    raise ValueError("No se pudo determinar el barista_id desde el Assignment")


# ================================================================
#  Fallback inteligente: shift_gross_amount → salary_range
# ================================================================

def _get_gross_amount(job_offer: JobOffer) -> Optional[int]:
    """
    Regla:
    1) Si shift_gross_amount viene definido → usarlo.
    2) Si viene None → usar salary_range.
    3) Si tampoco → retornar None.
    """

    # 1) monto principal
    if job_offer.shift_gross_amount is not None:
        return int(job_offer.shift_gross_amount)

    # 2) fallback: salary_range (INT)
    if job_offer.salary_range is not None:
        return int(job_offer.salary_range)

    # 3) no hay valor usable
    return None


# ================================================================
#  Crear GigPayment
# ================================================================

def create_gig_payment_from_assignment(
    session: Session, assignment: JobAssignment
) -> GigPayment:
    """
    Crea (o devuelve si ya existe) el registro de GigPayment asociado a un assignment.

    - Se llama cuando una asignación queda COMPLETED/CONFIRMED.
    - Usa shift_gross_amount o salary_range como monto.
    """

    if assignment.id is None:
        raise ValueError("El assignment debe tener id antes de crear un GigPayment")

    # 1) Ver si ya existe un pago para este assignment
    existing: Optional[GigPayment] = session.exec(
        select(GigPayment).where(GigPayment.assignment_id == assignment.id)
    ).first()

    if existing:
        return existing

    # 2) Obtener oferta
    job_offer = session.get(JobOffer, assignment.job_offer_id)
    if not job_offer:
        raise ValueError(
            f"JobOffer con id={assignment.job_offer_id} no encontrada para el assignment {assignment.id}"
        )

    # 3) Obtener monto bruto
    gross = _get_gross_amount(job_offer)

    if gross is None:
        print(
            f"[GigPayments] ❌ No se pudo determinar monto bruto para JobOffer {job_offer.id}. "
            f"(shift_gross_amount=None, salary_range=None). "
            f"No se generará GigPayment para assignment_id={assignment.id}."
        )
        raise ValueError(
            f"La oferta {job_offer.id} no tiene shift_gross_amount ni salary_range. "
            "Se requiere uno de los dos para generar un GigPayment."
        )

    # 4) IDs
    barista_id = _get_barista_id_from_assignment(assignment)
    business_id = getattr(job_offer, "business_id", None)

    # 5) Calcular fees
    fee_amount_cafe = int(round(gross * FEE_PCT_CAFE))
    fee_amount_barista = int(round(gross * FEE_PCT_BARISTA))
    net_amount_barista = gross - fee_amount_barista

    # 6) Crear registro
    payment = GigPayment(
        assignment_id=assignment.id,
        job_offer_id=job_offer.id,
        barista_id=barista_id,
        business_id=business_id,
        gross_amount=gross,
        fee_pct_cafe=FEE_PCT_CAFE,
        fee_pct_barista=FEE_PCT_BARISTA,
        fee_amount_cafe=fee_amount_cafe,
        fee_amount_barista=fee_amount_barista,
        net_amount_barista=net_amount_barista,
    )

    session.add(payment)
    session.commit()
    session.refresh(payment)

    print(f"[GigPayments] ✔ Pago generado para assignment_id={assignment.id}")

    return payment


# ================================================================
#  Helper
# ================================================================

def ensure_gig_payment_for_assignment_id(
    session: Session, assignment_id: int
) -> GigPayment:

    assignment = session.get(JobAssignment, assignment_id)
    if not assignment:
        raise ValueError(f"Assignment con id={assignment_id} no encontrado")

    return create_gig_payment_from_assignment(session, assignment)
