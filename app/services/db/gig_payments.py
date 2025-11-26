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
    # 🔧 Si tu Assignment usa user_id en vez de worker_id, cambia esta línea
    if hasattr(assignment, "worker_id") and assignment.worker_id is not None:
        return assignment.worker_id

    if hasattr(assignment, "user_id") and assignment.user_id is not None:
        return assignment.user_id

    raise ValueError("No se pudo determinar el barista_id desde el Assignment")


def create_gig_payment_from_assignment(
    session: Session, assignment: JobAssignment
) -> GigPayment:
    """
    Crea (o devuelve si ya existe) el registro de GigPayment asociado a un assignment.

    Regla de negocio:
    - Se llama cuando un assignment pasa a estado COMPLETED.
    - Usa el campo JobOffer.shift_gross_amount como monto bruto del turno.
    - Aplica los fees configurados en app.core.fees (7% cafe, 3% barista).
    """

    if assignment.id is None:
        raise ValueError("El assignment debe tener id antes de crear un GigPayment")

    # 1) Ver si ya existe un pago para este assignment
    existing: Optional[GigPayment] = session.exec(
        select(GigPayment).where(GigPayment.assignment_id == assignment.id)
    ).first()

    if existing:
        return existing

    # 2) Obtener JobOffer asociada
    if not hasattr(assignment, "job_offer_id"):
        raise ValueError(
            "El modelo Assignment no tiene el campo job_offer_id. "
            "Ajusta el servicio para usar el nombre correcto."
        )

    job_offer = session.get(JobOffer, assignment.job_offer_id)
    if not job_offer:
        raise ValueError(
            f"JobOffer con id={assignment.job_offer_id} no encontrada para el assignment {assignment.id}"
        )

    # 3) Validar que la oferta tenga shift_gross_amount definido
    gross_amount = job_offer.shift_gross_amount
    if gross_amount is None:
        raise ValueError(
            f"JobOffer {job_offer.id} no tiene shift_gross_amount definido. "
            "No se puede generar el GigPayment."
        )

    # 4) Determinar barista y cafetería
    barista_id = _get_barista_id_from_assignment(assignment)

    # Preferimos business_id si existe, si no, dejamos NULL (lógica de fallback)
    business_id = getattr(job_offer, "business_id", None)

    # 5) Calcular montos (CLP -> enteros)
    gross = int(gross_amount)

    fee_amount_cafe = int(round(gross * FEE_PCT_CAFE))
    fee_amount_barista = int(round(gross * FEE_PCT_BARISTA))
    net_amount_barista = gross - fee_amount_barista

    # 6) Crear GigPayment
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
        # status por defecto = SIMULATED (se setea en el modelo)
    )

    session.add(payment)
    session.commit()
    session.refresh(payment)

    return payment


def ensure_gig_payment_for_assignment_id(
    session: Session, assignment_id: int
) -> GigPayment:
    """
    Helper por id: carga el Assignment y delega en create_gig_payment_from_assignment.
    Puede ser útil si en algún endpoint solo recibes el id.
    """
    assignment = session.get(JobAssignment, assignment_id)
    if not assignment:
        raise ValueError(f"Assignment con id={assignment_id} no encontrado")

    return create_gig_payment_from_assignment(session, assignment)
